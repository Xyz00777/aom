"""Tests for ansible.builtin.pause-with-seconds visibility (IP5).

The pause module with ``seconds:`` doesn't read stdin — it just
sleeps. AOM's pexpect loop sees nothing during the wait; the task
silently disappears from the panel. This is annoying on long pauses.

The fix: when the v2_playbook_on_task_start event names the pause
action and includes ``args.seconds``, the compact renderer prints a
one-line ``[pause] sleeping Ns…`` log line so the user knows what's
happening.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _pause_task_event(
    seconds: int | float | str | None, action: str = "ansible.builtin.pause"
) -> dict:
    args: dict = {}
    if seconds is not None:
        args["seconds"] = seconds
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": "2026-05-11T10:00:00Z",
        "task": {
            "id": "task-uuid",
            "name": "Wait for service to settle",
            "action": action,
            "args": args,
        },
        "play": {"id": "play-uuid"},
    }


class TestPauseSecondsLogged:
    """A pause-with-seconds task surfaces a sleeping log line."""

    def test_pause_with_seconds_logs_sleeping_line(self) -> None:
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer(is_tty=False)
        renderer.start("test.yml", [])

        with patch.object(renderer._display, "print_log") as mock_print:
            renderer.update_state(_pause_task_event(seconds=30))

        logged = [c.args[0] for c in mock_print.call_args_list]
        assert any("[pause]" in line and "30" in line for line in logged), logged

    def test_pause_short_action_name_also_caught(self) -> None:
        """Some playbooks use the short ``pause`` action name."""
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer(is_tty=False)
        renderer.start("test.yml", [])

        with patch.object(renderer._display, "print_log") as mock_print:
            renderer.update_state(_pause_task_event(seconds=5, action="pause"))

        logged = [c.args[0] for c in mock_print.call_args_list]
        assert any("[pause]" in line for line in logged), logged

    def test_pause_without_seconds_does_not_emit_sleeping_line(self) -> None:
        """A prompt-style pause is handled by the runner stdin path, not here."""
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer(is_tty=False)
        renderer.start("test.yml", [])

        with patch.object(renderer._display, "print_log") as mock_print:
            renderer.update_state(_pause_task_event(seconds=None))

        # The normal TASK line still prints (existing behaviour) but no
        # sleeping-Ns hint should appear when there's no seconds value.
        logged = [c.args[0] for c in mock_print.call_args_list]
        assert not any("sleeping" in line for line in logged), logged

    def test_non_pause_task_does_not_emit_sleeping_line(self) -> None:
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer(is_tty=False)
        renderer.start("test.yml", [])

        event = {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-11T10:00:00Z",
            "task": {
                "id": "task-uuid",
                "name": "Install nginx",
                "action": "ansible.builtin.apt",
                "args": {"name": "nginx"},
            },
            "play": {"id": "play-uuid"},
        }

        with patch.object(renderer._display, "print_log") as mock_print:
            renderer.update_state(event)

        logged = [c.args[0] for c in mock_print.call_args_list]
        assert not any("[pause]" in line for line in logged), logged

    def test_pause_with_string_seconds_handled(self) -> None:
        """ansible sometimes serialises args as strings; tolerate that."""
        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer(is_tty=False)
        renderer.start("test.yml", [])

        with patch.object(renderer._display, "print_log") as mock_print:
            renderer.update_state(_pause_task_event(seconds="10"))

        logged = [c.args[0] for c in mock_print.call_args_list]
        assert any("[pause]" in line and "10" in line for line in logged), logged
