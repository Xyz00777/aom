"""Unit tests for F2 replay_session.

Replay reads `events.jsonl` + `meta.json` from a session directory and
feeds the events into a Renderer at the recorded pace. This test
covers the simplest path: a session with two events; speed=0 (no
sleeps); renderer receives both events in order followed by
handle_completion.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _make_session(
    base: Path,
    session_id: str,
    events: list[dict],
    meta: dict | None = None,
) -> Path:
    """Create a sessions/<id>/ directory with events.jsonl + meta.json."""
    session_path = base / session_id
    session_path.mkdir(parents=True)
    with open(session_path / "events.jsonl", "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    full_meta = {"playbook": "test.yml", "status": "completed"}
    if meta:
        full_meta.update(meta)
    with open(session_path / "meta.json", "w") as f:
        json.dump(full_meta, f)
    (session_path / "stderr.log").touch()
    return session_path


class TestReplaySessionBasic:
    def test_renderer_receives_each_event_in_order(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "v2_playbook_on_play_start", "_timestamp": "2026-05-08T10:00:00.5Z"},
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
        ]
        _make_session(tmp_path, "abc123", events)

        renderer = MagicMock()
        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="abc123",
            renderer=renderer,
            speed=0,  # as fast as possible
        )

        assert exit_code == 0
        # update_state called once per event, in order.
        assert renderer.update_state.call_count == 3
        seen = [c.args[0]["_event"] for c in renderer.update_state.call_args_list]
        assert seen == [
            "v2_playbook_on_start",
            "v2_playbook_on_play_start",
            "v2_playbook_on_stats",
        ]

    def test_returns_minus_one_when_session_missing(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        renderer = MagicMock()
        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="does-not-exist",
            renderer=renderer,
            speed=0,
        )

        # Convention: missing session => non-zero, no renderer activity.
        assert exit_code != 0
        renderer.start.assert_not_called()
        renderer.update_state.assert_not_called()


class TestReplaySpeedControl:
    """speed=0 means no sleeps; speed=2 halves them; default 1× honors deltas."""

    def test_speed_zero_makes_no_sleep_calls(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:30Z"},
        ]
        _make_session(tmp_path, "s1", events)

        sleeps: list[float] = []
        renderer = MagicMock()
        replay_session(
            session_dir=tmp_path,
            session_id="s1",
            renderer=renderer,
            speed=0,
            sleeper=sleeps.append,
        )

        assert sleeps == []

    def test_speed_one_sleeps_real_delta_seconds(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "a", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "b", "_timestamp": "2026-05-08T10:00:01Z"},
            {"_event": "c", "_timestamp": "2026-05-08T10:00:03Z"},
        ]
        _make_session(tmp_path, "s2", events)

        sleeps: list[float] = []
        renderer = MagicMock()
        replay_session(
            session_dir=tmp_path,
            session_id="s2",
            renderer=renderer,
            speed=1.0,
            sleeper=sleeps.append,
        )

        # Two gaps (1s, 2s) → two sleeps of ~1.0 and ~2.0.
        assert len(sleeps) == 2
        assert sleeps[0] == pytest.approx(1.0, abs=1e-6)
        assert sleeps[1] == pytest.approx(2.0, abs=1e-6)

    def test_speed_two_halves_sleeps(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "a", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "b", "_timestamp": "2026-05-08T10:00:02Z"},
        ]
        _make_session(tmp_path, "s3", events)

        sleeps: list[float] = []
        renderer = MagicMock()
        replay_session(
            session_dir=tmp_path,
            session_id="s3",
            renderer=renderer,
            speed=2.0,
            sleeper=sleeps.append,
        )

        assert sleeps == [pytest.approx(1.0, abs=1e-6)]


class TestReplayNegativeDelta:
    """Real ansible JSONL is not strictly monotonic across threads.

    A delta of -0.5s must not sleep negative time (would crash
    time.sleep) — instead replay treats it as zero.
    """

    def test_out_of_order_timestamps_do_not_sleep_negative(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "a", "_timestamp": "2026-05-08T10:00:01Z"},
            {"_event": "b", "_timestamp": "2026-05-08T10:00:00Z"},  # earlier!
            {"_event": "c", "_timestamp": "2026-05-08T10:00:02Z"},
        ]
        _make_session(tmp_path, "s4", events)

        sleeps: list[float] = []
        renderer = MagicMock()
        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="s4",
            renderer=renderer,
            speed=1.0,
            sleeper=sleeps.append,
        )

        assert exit_code == 0
        # Two transitions:
        #   a -> b: delta = -1s → clamped to 0 → no sleep recorded
        #   b -> c: delta = +2s → 2.0
        # We allow either "no sleep at all when wait==0" or "sleep(0.0)".
        positive_sleeps = [s for s in sleeps if s > 0]
        assert positive_sleeps == [pytest.approx(2.0, abs=1e-6)]
        # And the renderer must still see all three in file order.
        seen = [c.args[0]["_event"] for c in renderer.update_state.call_args_list]
        assert seen == ["a", "b", "c"]


class TestReplayCompletionFromMeta:
    """`handle_completion` is called with the meta.json status."""

    def test_status_completed(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        _make_session(
            tmp_path,
            "ok",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
            meta={"status": "completed"},
        )

        renderer = MagicMock()
        replay_session(tmp_path, "ok", renderer, speed=0)

        renderer.handle_completion.assert_called_once_with(0, "completed")

    def test_status_failed(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        _make_session(
            tmp_path,
            "bad",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
            meta={"status": "failed"},
        )

        renderer = MagicMock()
        replay_session(tmp_path, "bad", renderer, speed=0)

        renderer.handle_completion.assert_called_once_with(0, "failed")

    def test_status_crashed(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        _make_session(
            tmp_path,
            "boom",
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
            meta={"status": "crashed"},
        )

        renderer = MagicMock()
        replay_session(tmp_path, "boom", renderer, speed=0)

        renderer.handle_completion.assert_called_once_with(0, "crashed")

    def test_missing_status_defaults_to_completed(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        # Create a session whose meta.json has no status field at all.
        session_path = tmp_path / "noStatus"
        session_path.mkdir()
        (session_path / "events.jsonl").write_text(
            '{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}\n'
        )
        (session_path / "meta.json").write_text('{"playbook": "x.yml"}')
        (session_path / "stderr.log").touch()

        renderer = MagicMock()
        replay_session(tmp_path, "noStatus", renderer, speed=0)

        renderer.handle_completion.assert_called_once_with(0, "completed")


class TestReplayKeyboardInterrupt:
    """User hits Ctrl+C mid-replay → renderer sees handle_completion(130, 'crashed')."""

    def test_keyboard_interrupt_during_sleep(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "a", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "b", "_timestamp": "2026-05-08T10:00:01Z"},
            {"_event": "c", "_timestamp": "2026-05-08T10:00:02Z"},
        ]
        _make_session(tmp_path, "kc", events)

        renderer = MagicMock()

        # Sleep raises KeyboardInterrupt the second time it's called
        # (i.e. between events b and c).
        call_count = {"n": 0}

        def fake_sleep(seconds: float) -> None:
            call_count["n"] += 1
            if call_count["n"] >= 2:
                raise KeyboardInterrupt

        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="kc",
            renderer=renderer,
            speed=1.0,
            sleeper=fake_sleep,
        )

        assert exit_code == 130
        renderer.handle_completion.assert_called_once_with(130, "crashed")
        # Renderer should have seen events a and b, not c.
        seen = [c.args[0]["_event"] for c in renderer.update_state.call_args_list]
        assert seen == ["a", "b"]

    def test_keyboard_interrupt_during_update_state(self, tmp_path: Path) -> None:
        from ansible_aom.replay import replay_session

        events = [
            {"_event": "a", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "b", "_timestamp": "2026-05-08T10:00:01Z"},
        ]
        _make_session(tmp_path, "kc2", events)

        renderer = MagicMock()
        renderer.update_state.side_effect = KeyboardInterrupt

        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="kc2",
            renderer=renderer,
            speed=0,
        )

        assert exit_code == 130
        renderer.handle_completion.assert_called_once_with(130, "crashed")
