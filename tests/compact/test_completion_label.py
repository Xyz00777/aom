"""Tests for the labeled final-state line in handle_completion.

A bare ✖ told the user nothing about WHY the run ended. We now suffix
the icon with a short label so Ctrl+C (cancelled), missing executable
(not found), generic non-zero exit (failed), and clean exit
(unlabelled ●) are all distinguishable at a glance.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from ansible_aom.compact.renderer import CompactRenderer


def _final_line(exit_code: int, state: str) -> str:
    renderer = CompactRenderer(is_tty=False)
    renderer.start("test.yml", [])
    buf = io.StringIO()
    with redirect_stdout(buf):
        renderer.handle_completion(exit_code, state)
    # The final summary line is the first thing printed by handle_completion.
    return buf.getvalue().splitlines()[0]


class TestCompletionLabel:
    def test_completed_has_no_label(self):
        line = _final_line(0, "completed")
        assert "●" in line or "*" in line
        # No "failed" / "cancelled" / "crashed" suffix on a clean exit.
        assert "failed" not in line.lower()
        assert "cancelled" not in line.lower()
        assert "crashed" not in line.lower()

    def test_failed_state_is_labeled(self):
        line = _final_line(2, "failed")
        assert "failed" in line.lower()

    def test_ctrl_c_shows_cancelled(self):
        """Exit code 130 (KeyboardInterrupt) shows 'cancelled by user'."""
        line = _final_line(130, "crashed")
        assert "cancelled" in line.lower()
        assert "user" in line.lower()

    def test_executable_missing_shows_not_found(self):
        """Exit code 127 (command not found) gets its own label."""
        line = _final_line(127, "crashed")
        assert "not found" in line.lower()

    def test_other_crash_shows_crashed(self):
        line = _final_line(1, "crashed")
        assert "crashed" in line.lower()
