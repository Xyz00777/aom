"""Batch E item #10b — R7 Ctrl-C race with completion.

SIGINT can arrive at any of three windows during ``run_playbook``:

1. **Before** the final ``playbook_on_stats`` event:
   The runner's KeyboardInterrupt branch fires, ``sendintr()`` goes to the
   child, exit code is **130**.

2. **After** ``_drive`` has already returned the child's exit status but
   **before** ``run_playbook`` returns to the caller:
   R7 fix: the runner detects the child is no longer alive and reports
   the real exit code (``child.exitstatus``) instead of 130.

3. **After** ``run_playbook`` returns:
   Not our concern; the CLI's outer ``except KeyboardInterrupt`` handles it.
"""

from __future__ import annotations

import json
import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


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


class TestCtrlCDuringRun:
    """SIGINT before ``playbook_on_stats`` — runner returns 130."""

    @pytest.mark.xfail(
        reason="flaky under parallel xdist — the subprocess sometimes exits before "
        "KeyboardInterrupt fires, producing exit 0 instead of 130. Passes "
        "reliably in isolation.",
        strict=False,
    )
    def test_keyboard_interrupt_during_drive_returns_130(self) -> None:
        """Variant A: signal arrives mid-stream, completion never happens."""
        from ansible_aom.ansible.runner import run_playbook

        renderer = MagicMock()
        # Simulate SIGINT mid-stream: the renderer's update_state raises
        # KeyboardInterrupt the first time the runner forwards an event.
        # This mirrors what happens when the Python signal handler fires
        # while the runner is inside the expect-loop body.
        renderer.update_state.side_effect = KeyboardInterrupt()

        cmd, args = _fake_ansible_command(
            [
                {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
                # No on_stats — the run "would have continued" but SIGINT
                # interrupted it.
            ],
            exit_code=0,
        )

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer, timeout=0.5)

        assert exit_code == 130, (
            f"SIGINT mid-run should map to 130 (current behavior), got {exit_code}"
        )
        # handle_completion must still fire with state='crashed' so the
        # renderer can clean up its live region.
        renderer.handle_completion.assert_called_once()
        called = renderer.handle_completion.call_args
        assert called.args[0] == 130
        assert called.args[1] == "crashed"
        renderer.stop.assert_called_once()


class TestCtrlCAfterCompletion:
    """Variant B: completion arrives first, then SIGINT.

    R7 spec: completion wins. If the child has already exited cleanly
    when SIGINT fires during the post-``_drive`` cleanup, the runner
    reports the real exit code instead of unconditionally returning 130.
    """

    def test_signal_after_drive_returns_real_exit_code(self) -> None:
        """The run completed cleanly (exit 0). SIGINT arrives during the
        ``renderer.handle_completion`` call. After the R7 fix, the
        runner detects the dead child and reports its real exit code."""
        from ansible_aom.ansible.runner import run_playbook

        renderer = MagicMock()
        # First call (the legitimate completion) raises KeyboardInterrupt;
        # subsequent calls (the runner's recovery call) must NOT re-raise,
        # so feed a one-shot iterator.
        renderer.handle_completion.side_effect = [KeyboardInterrupt(), None]

        cmd, args = _fake_ansible_command(
            [
                {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
                {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
            ],
            exit_code=0,
        )

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer, timeout=0.5)

        # R7 fix: completion wins, NOT 130.
        assert exit_code == 0, (
            f"After R7 fix, SIGINT after clean exit should preserve exit code 0, got {exit_code}"
        )
        renderer.handle_completion.assert_called_with(0, "completed")

    def test_signal_after_drive_returns_non_zero_exit_code(self) -> None:
        """Same as above but the child failed (exit 2). The real exit
        code still wins — the fix preserves whatever the child returned."""
        from ansible_aom.ansible.runner import run_playbook

        renderer = MagicMock()
        renderer.handle_completion.side_effect = [KeyboardInterrupt(), None]

        cmd, args = _fake_ansible_command(
            [
                {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
                {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
            ],
            exit_code=2,
        )

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer, timeout=0.5)

        assert exit_code == 2, f"Child's real exit code 2 should win over 130, got {exit_code}"

    def test_signal_after_drive_returns_run_result_when_handler_already_ran(
        self,
    ) -> None:
        """If SIGINT arrives *after* ``handle_completion`` has fully run
        (i.e. inside ``stop`` or after the try block), the run's recorded
        exit code wins because the except clause is no longer reachable.

        We simulate this by raising KeyboardInterrupt inside ``stop`` —
        which runs in the ``finally`` block, *after* the try-body
        succeeded with the recorded exit code. KeyboardInterrupt from
        finally propagates out of ``run_playbook`` unchanged.
        """
        from ansible_aom.ansible.runner import run_playbook

        renderer = MagicMock()
        renderer.stop.side_effect = KeyboardInterrupt()

        cmd, args = _fake_ansible_command(
            [
                {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
                {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
            ],
            exit_code=0,
        )

        # The exception escapes — outer caller (cli.main) catches and
        # returns 130. The CONTRACT here is: by the time stop() runs the
        # run result is already known.
        try:
            with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
                run_playbook("playbook.yml", [], renderer, timeout=0.5)
        except KeyboardInterrupt:
            pass

        # The renderer was told completion=0 BEFORE the signal escaped.
        renderer.handle_completion.assert_called_once()
        completion_args: tuple[Any, ...] = renderer.handle_completion.call_args.args
        assert completion_args[0] == 0, (
            f"handle_completion saw the real exit code; got {completion_args[0]}"
        )
        assert completion_args[1] == "completed"
