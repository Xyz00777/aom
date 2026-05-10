"""Integration tests for the ansible-playbook runner.

The runner spawns `ansible-playbook` with the JSONL callback, reads the
PTY stream line-by-line, and feeds events to the renderer. These tests
substitute a fake `ansible-playbook` executable (a python -c command
that emits canned JSONL) so we can assert the runner's wiring without
needing a real Ansible install.
"""

from __future__ import annotations

import json
import sys
from typing import Any
from unittest.mock import MagicMock, patch


def _fake_ansible_command(events: list[dict], exit_code: int = 0) -> tuple[str, list[str]]:
    """Build a (command, args) pair that emits `events` as JSONL then exits.

    Returns the tuple in the form pexpect.spawn expects.
    """
    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


class TestRunnerHappyPath:
    """Runner spawns the subprocess and pumps events to the renderer."""

    def test_run_playbook_calls_renderer_start_and_completion(self) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [
                {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
                {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
            ],
            exit_code=0,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer)

        assert exit_code == 0
        renderer.start.assert_called_once_with("playbook.yml", [])
        renderer.handle_completion.assert_called_once()
        completion_args = renderer.handle_completion.call_args
        assert completion_args.args[0] == 0
        assert completion_args.args[1] == "completed"
        renderer.stop.assert_called_once()

    def test_run_playbook_forwards_jsonl_events_to_update_state(self) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        events: list[dict[str, Any]] = [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-08T10:00:00Z",
                "play": {"name": "p1", "uuid": "u1"},
            },
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
        ]
        cmd, args = _fake_ansible_command(events, exit_code=0)

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer)

        update_calls = renderer.update_state.call_args_list
        seen_event_names = [c.args[0]["_event"] for c in update_calls]
        # All three events should reach the renderer in order.
        assert seen_event_names == [
            "v2_playbook_on_start",
            "v2_playbook_on_play_start",
            "v2_playbook_on_stats",
        ]


class TestRunnerFailureExit:
    """Non-zero subprocess exit becomes 'failed' state."""

    def test_run_playbook_marks_failed_on_nonzero_exit(self) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:00Z"}],
            exit_code=2,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer)

        assert exit_code == 2
        completion_args = renderer.handle_completion.call_args
        assert completion_args.args[0] == 2
        assert completion_args.args[1] == "failed"


class TestRunnerCommandNotFound:
    """Missing ansible-playbook surfaces as exit 127 without crashing."""

    def test_run_playbook_returns_127_when_command_missing(self) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        # Path that definitely doesn't exist.
        with patch(
            "ansible_aom.runner._build_command",
            return_value=("/nonexistent/ansible-playbook-xxx", []),
        ):
            exit_code = run_playbook("playbook.yml", [], renderer)

        assert exit_code == 127
        completion_args = renderer.handle_completion.call_args
        assert completion_args.args[0] == 127
        # State should be 'crashed' for a missing executable, not 'failed' —
        # the playbook never got a chance to run.
        assert completion_args.args[1] == "crashed"
