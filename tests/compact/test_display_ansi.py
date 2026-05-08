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
