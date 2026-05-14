"""Batch E item #10b — R7 Ctrl-C race with completion.

SIGINT can arrive at any of three windows during ``run_playbook``:

1. **Before** the final ``playbook_on_stats`` event:
   The runner's KeyboardInterrupt branch fires, ``sendintr()`` goes to the
   child, exit code is **130**.

2. **After** ``_drive`` has already returned the child's exit status but
   **before** ``run_playbook`` returns to the caller:
   Vanishingly small window in practice. If SIGINT does land here, the
   except branch catches it and returns 130 — overriding the run result.

3. **After** ``run_playbook`` returns:
   Not our concern; the CLI's outer ``except KeyboardInterrupt`` handles it.

These tests pin the **current** behavior (assertion-of-fact) rather than
the spec-ideal. The spec gap: window #2 currently maps to 130 even when
the underlying run had a clean exit code waiting. SPECIFICATION.md does
not disambiguate. If the team decides the run result should win in
window #2, the second test below becomes the failing-first test for that
change.
"""

from __future__ import annotations

import json
import sys
from typing import Any
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


class TestCtrlCDuringRun:
    """SIGINT before ``playbook_on_stats`` — runner returns 130."""

    def test_keyboard_interrupt_during_drive_returns_130(self) -> None:
        """Variant A: signal arrives mid-stream, completion never happens."""
        from ansible_aom.runner import run_playbook

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

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
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


class TestCtrlCAfterCompletionDocumentsCurrentBehavior:
    """Variant B: completion arrives first, then SIGINT.

    Currently the runner's outer try/except still catches the signal and
    returns 130 — but only if KeyboardInterrupt is raised inside the try
    block. If ``_drive`` has already returned and ``handle_completion``
    already ran, SIGINT raised at that exact moment is still inside the
    try block. This test pins that behavior.

    This is a known spec ambiguity. If the user wants "completion wins",
    the runner needs to guard the post-``_drive`` cleanup against
    interruption, and this test should flip to asserting the recorded
    exit code (0 for the case below).
    """

    def test_signal_after_drive_still_maps_to_130(self) -> None:
        """The run completed cleanly (exit 0). SIGINT arrives during the
        ``renderer.handle_completion`` call. Current behavior: 130 wins."""
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        # Run completes; SIGINT fires when the renderer renders the final
        # completion frame. The except branch re-calls handle_completion
        # (with 130, "crashed") — that second call must NOT re-raise, so
        # set the side_effect to a one-shot via an iterator.
        renderer.handle_completion.side_effect = [KeyboardInterrupt(), None]

        cmd, args = _fake_ansible_command(
            [
                {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
                {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
            ],
            exit_code=0,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer, timeout=0.5)

        # SPEC GAP: ideally completion would win (exit 0). Today the
        # outer KeyboardInterrupt handler always returns 130. Pin the
        # current behavior; flip the assertion when the spec settles.
        assert exit_code == 130, (
            f"Current behavior: SIGINT during handle_completion returns 130, got {exit_code}"
        )

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
        from ansible_aom.runner import run_playbook

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
            with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
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
