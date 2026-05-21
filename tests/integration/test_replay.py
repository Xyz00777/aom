"""Integration test: record a fake run, then replay it.

Drives ``run_playbook`` against a fake ansible executable so a real
session directory is produced on disk, then calls ``replay_session``
and asserts the replayed renderer sees the same event sequence in the
same order.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _fake_ansible_command(events: list[dict], exit_code: int = 0) -> tuple[str, list[str]]:
    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


class TestRecordThenReplay:
    def test_record_then_replay_produces_same_event_sequence(self, tmp_path: Path) -> None:
        from ansible_aom.drivers.replay import replay_session
        from ansible_aom.ansible.runner import run_playbook

        events = [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-08T10:00:00.5Z",
                "play": {"id": "p1", "name": "Test"},
            },
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-08T10:00:01Z",
                "task": {"id": "t1", "name": "task one"},
            },
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-08T10:00:01.5Z",
                "task": {"id": "t1"},
                "hosts": {"web1": {"ok": True}},
            },
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-05-08T10:00:02Z",
                "stats": {"web1": {"ok": 1}},
            },
        ]

        # ----- Record -----
        record_renderer = MagicMock()
        cmd, args = _fake_ansible_command(events, exit_code=0)
        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], record_renderer, session_dir=tmp_path)
        assert exit_code == 0

        # The runner created exactly one session directory; grab its id.
        session_dirs = list(tmp_path.iterdir())
        assert len(session_dirs) == 1
        session_id = session_dirs[0].name

        # ----- Replay -----
        replay_renderer = MagicMock()
        replay_exit = replay_session(
            session_dir=tmp_path,
            session_id=session_id,
            renderer=replay_renderer,
            speed=0,  # no sleeps in tests
        )
        assert replay_exit == 0

        # Both renderers saw the same _event sequence (ignoring extra
        # callbacks like start/handle_completion which differ between
        # the two paths — we only compare update_state events).
        recorded_seq = [c.args[0]["_event"] for c in record_renderer.update_state.call_args_list]
        replayed_seq = [c.args[0]["_event"] for c in replay_renderer.update_state.call_args_list]
        assert recorded_seq == replayed_seq
        assert recorded_seq == [e["_event"] for e in events]

        # Replay's completion uses meta.status ("completed" → 0/"completed").
        replay_renderer.handle_completion.assert_called_once_with(0, "completed")

    def test_replay_uses_meta_status_failed_when_recorded_failed(self, tmp_path: Path) -> None:
        """A recorded failure (exit 2) writes meta.status=failed; replay
        forwards that status to handle_completion."""
        from ansible_aom.drivers.replay import replay_session
        from ansible_aom.ansible.runner import run_playbook

        events = [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}]
        cmd, args = _fake_ansible_command(events, exit_code=2)

        record_renderer = MagicMock()
        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], record_renderer, session_dir=tmp_path)

        session_id = next(tmp_path.iterdir()).name

        replay_renderer = MagicMock()
        replay_session(tmp_path, session_id, replay_renderer, speed=0)

        replay_renderer.handle_completion.assert_called_once_with(0, "failed")
