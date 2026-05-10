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


class TestRunnerPreflight:
    """Runner calls run_preflight before spawning and forwards its result."""

    def test_run_playbook_calls_preflight_and_forwards_definitions(self) -> None:
        from ansible_aom.runner import run_playbook

        captured_defs: list = []

        class StubRenderer:
            def start(self, playbook: str, args: list[str]) -> None: ...
            def set_definitions(self, definitions: list) -> None:
                captured_defs.extend(definitions)

            def update_state(self, event: dict) -> None: ...
            def handle_password_prompt(self, prompt: str) -> str:
                return ""

            def handle_completion(self, exit_code: int, state: str) -> None: ...
            def stop(self) -> None: ...

        fake_pre_result = MagicMock()
        fake_pre_result.definitions = ["DEF1", "DEF2"]
        fake_pre_result.errors = []

        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with (
            patch(
                "ansible_aom.runner.run_preflight",
                return_value=fake_pre_result,
            ),
            patch("ansible_aom.runner._build_command", return_value=(cmd, args)),
        ):
            exit_code = run_playbook("playbook.yml", [], StubRenderer())

        assert exit_code == 0
        assert captured_defs == ["DEF1", "DEF2"]

    def test_run_playbook_forwards_preflight_errors_as_warnings(self) -> None:
        from ansible_aom.runner import run_playbook

        received_warnings: list[tuple[str, bool]] = []

        class StubRenderer:
            def start(self, playbook: str, args: list[str]) -> None: ...
            def set_definitions(self, definitions: list) -> None: ...
            def add_warning(self, message: str, is_deprecation: bool = False) -> None:
                received_warnings.append((message, is_deprecation))

            def update_state(self, event: dict) -> None: ...
            def handle_password_prompt(self, prompt: str) -> str:
                return ""

            def handle_completion(self, exit_code: int, state: str) -> None: ...
            def stop(self) -> None: ...

        fake_pre_result = MagicMock()
        fake_pre_result.definitions = []
        fake_pre_result.errors = ["--list-hosts failed (exit 1): nope"]

        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with (
            patch(
                "ansible_aom.runner.run_preflight",
                return_value=fake_pre_result,
            ),
            patch("ansible_aom.runner._build_command", return_value=(cmd, args)),
        ):
            run_playbook("playbook.yml", [], StubRenderer())

        assert any("--list-hosts failed" in msg for msg, _ in received_warnings)

    def test_run_playbook_prints_preflight_errors_above_panel(self) -> None:
        """Preflight errors are too important to hide behind a counter — print them."""
        from ansible_aom.runner import run_playbook

        printed: list[str] = []

        class StubRenderer:
            def start(self, playbook: str, args: list[str]) -> None: ...
            def set_definitions(self, definitions: list) -> None: ...
            def print_log(self, message: str) -> None:
                printed.append(message)

            def add_warning(self, message: str, is_deprecation: bool = False) -> None: ...
            def update_state(self, event: dict) -> None: ...
            def handle_password_prompt(self, prompt: str) -> str:
                return ""

            def handle_completion(self, exit_code: int, state: str) -> None: ...
            def stop(self) -> None: ...

        fake_pre_result = MagicMock()
        fake_pre_result.definitions = []
        fake_pre_result.errors = [
            "--list-tasks failed (exit 4): YAML parsing failed",
            "--list-hosts failed (exit 4): YAML parsing failed",
        ]

        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with (
            patch(
                "ansible_aom.runner.run_preflight",
                return_value=fake_pre_result,
            ),
            patch("ansible_aom.runner._build_command", return_value=(cmd, args)),
        ):
            run_playbook("playbook.yml", [], StubRenderer())

        # Both errors share the same body — dedupe to one print, but both
        # still bump the warning counter (asserted via the previous test).
        assert len(printed) == 1
        assert "YAML parsing failed" in printed[0]

    def test_run_playbook_prints_distinct_preflight_errors_separately(self) -> None:
        """When preflight errors have different bodies, all of them are printed."""
        from ansible_aom.runner import run_playbook

        printed: list[str] = []

        class StubRenderer:
            def start(self, playbook: str, args: list[str]) -> None: ...
            def set_definitions(self, definitions: list) -> None: ...
            def print_log(self, message: str) -> None:
                printed.append(message)

            def add_warning(self, message: str, is_deprecation: bool = False) -> None: ...
            def update_state(self, event: dict) -> None: ...
            def handle_password_prompt(self, prompt: str) -> str:
                return ""

            def handle_completion(self, exit_code: int, state: str) -> None: ...
            def stop(self) -> None: ...

        fake_pre_result = MagicMock()
        fake_pre_result.definitions = []
        fake_pre_result.errors = [
            "--list-tasks failed (exit 4): YAML parsing failed",
            "--list-hosts failed (exit 1): something else entirely",
        ]

        cmd, args = _fake_ansible_command(
            [{"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"}],
            exit_code=0,
        )

        with (
            patch(
                "ansible_aom.runner.run_preflight",
                return_value=fake_pre_result,
            ),
            patch("ansible_aom.runner._build_command", return_value=(cmd, args)),
        ):
            run_playbook("playbook.yml", [], StubRenderer())

        assert len(printed) == 2
