"""Tests for nom-style ANSI rendering in compact mode.

These tests pin the new-spec rendering contract: direct ANSI cursor
positioning + DEC mode 2026 (synchronized output) instead of Rich Live.
See .sisyphus/notepads/new-spec/open-questions.md "Summary of nom-Style
Compact View Research" and DQ1 for the rationale (Rich Live works but
flickers; direct ANSI gives the fixed-bottom panel without artifacts).
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from ansible_aom.compact.display import Display

# DEC mode 2026: Synchronized Output (Begin/End Sync Update).
# Wrapping a frame in BSU..ESU tells the terminal to buffer renders so
# multi-line updates appear atomically — no flicker, no half-frames.
BSU = "\x1b[?2026h"
ESU = "\x1b[?2026l"


class TestSynchronizedOutput:
    """Each Display.update() in TTY mode emits a single DEC 2026 frame."""

    def test_update_wraps_content_in_dec_2026_sync(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = Display(is_tty=True)
            display.start()
            display.update("status line")
            display.stop()

        out = buf.getvalue()
        assert BSU in out, f"missing BSU (\\x1b[?2026h) in output:\n{out!r}"
        assert ESU in out, f"missing ESU (\\x1b[?2026l) in output:\n{out!r}"
        # BSU must come before ESU at least once.
        assert out.index(BSU) < out.index(ESU)

    def test_non_tty_update_emits_no_ansi(self) -> None:
        """is_tty=False is the pipe/CI fallback (PQ6): never emit positioning."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = Display(is_tty=False)
            display.start()
            display.update("status line")
            display.stop()

        out = buf.getvalue()
        assert BSU not in out
        assert ESU not in out


class TestRewindCorrectness:
    """The status-block rewind must land on the start of the block, not above it.

    Bug seen interactively (fish shell): the line above the status —
    typically the user's `aom playbook.yml` command — got erased on every
    redraw. Root cause: `_rewind_status()` emitted `CSI 1 F` for a 1-row
    status, but `CSI 1 F` moves UP one line, putting the cursor on the
    line ABOVE the status. The subsequent `CSI J` (clear-to-EOS) then
    wipes the command line. For a 1-row block the cursor is already on
    the right line; we just need `\\r` to return to col 1.
    """

    def test_single_row_rewind_uses_carriage_return_not_F(self) -> None:
        """For a 1-row status, rewind is a carriage return, not cursor-up."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = Display(is_tty=True)
            display.start()
            display.update("first")  # 1 row → _status_rows=1
            # Wait long enough to bypass the 250ms throttle.
            import time

            time.sleep(0.3)
            display.update("second")
            display.stop()

        out = buf.getvalue()
        # The second update should NOT contain "CSI 1 F" — that would
        # rewind one line PAST the start of the (1-row) status block.
        assert "\x1b[1F" not in out, (
            f"second update emitted CSI 1 F, which erases the line above the status:\n{out!r}"
        )

    def test_multi_row_rewind_moves_up_rows_minus_one(self) -> None:
        """For an N-row status, cursor is on the last row, so we rewind N-1 lines."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = Display(is_tty=True)
            display.start()
            # Three rows of content (two newlines, no trailing newline).
            display.update("row1\nrow2\nrow3")
            import time

            time.sleep(0.3)
            display.update("new content")
            display.stop()

        out = buf.getvalue()
        # 3 rows → cursor on row 3. Rewind: up 2 lines + col 1.
        assert "\x1b[2F" in out

    def test_print_log_does_not_erase_line_above_single_row_status(self) -> None:
        """The flow that triggered the bug: status, then print_log."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = Display(is_tty=True)
            display.start()
            display.update("playbook.yml | 0/1 hosts | 0:00:00")  # 1 row
            display.print_log("PLAY [Setup] (localhost, 1 host, 3 tasks)")
            display.stop()

        out = buf.getvalue()
        # The whole flow must never emit CSI 1 F — that would clobber
        # the line above (the user's command in their shell).
        assert "\x1b[1F" not in out, f"print_log emitted CSI 1 F after a 1-row status:\n{out!r}"
