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
