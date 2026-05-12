"""Tests for R4 — graceful degradation on terminals smaller than 80×24.

Today the compact panel renders into terminals smaller than the spec's
24×80 minimum and produces ghost lines and wrapped status bars. R4
degrades to a plain log-only stream with a one-line warning, then
re-enables the panel automatically when the terminal grows back past
the threshold.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from ansible_aom.compact.display import MINIMUM_SIZE, Display


class TestThresholdConstant:
    """The (cols, rows) threshold lives as a module constant so tests
    can reference it instead of hard-coding 80, 24."""

    def test_minimum_size_is_80_cols_24_rows(self) -> None:
        assert MINIMUM_SIZE == (80, 24)


class TestForceSizePassthrough:
    """`force_size` is the test injection seam for the size detection
    that Task 2 will wire into degraded-mode entry. Task 1 only
    proves the parameter is accepted and changes nothing yet."""

    def test_start_accepts_force_size_kwarg_without_error(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = Display(is_tty=True)
            display.start(force_size=(120, 40))
            display.stop()
        # No assertion on output — Task 1 is wiring-only. The point
        # is that start() accepts the kwarg.

    def test_start_without_force_size_works_as_before(self) -> None:
        """Backwards-compatible: existing callers don't pass force_size."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = Display(is_tty=True)
            display.start()
            display.stop()


class TestDegradedModeEntry:
    """A terminal smaller than MINIMUM_SIZE puts Display into degraded
    mode at start(): no cursor hide, no DEC frames, and a one-line
    warning printed to stdout outside any synchronization sequence.
    """

    BSU = "\x1b[?2026h"
    ESU = "\x1b[?2026l"
    HIDE_CURSOR = "\x1b[?25l"

    def test_force_size_below_threshold_enters_degraded_mode(self) -> None:
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(40, 8))
        assert display._degraded is True
        # Display should not be "running" in the live-panel sense —
        # update() will not draw frames.
        assert display._is_running is False

    def test_force_size_below_threshold_prints_one_line_warning(self) -> None:
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(40, 8))

        out = buf.getvalue()
        # Exactly one warning line, mentioning the actual size and minimum.
        assert "40" in out and "8" in out, f"warning missing actual size:\n{out!r}"
        assert "80" in out and "24" in out, f"warning missing minimum size:\n{out!r}"
        # Critical: the warning must be OUTSIDE any DEC 2026 frame.
        assert self.BSU not in out, f"warning wrapped in BSU frame:\n{out!r}"
        assert self.ESU not in out, f"warning wrapped in ESU frame:\n{out!r}"
        # And the cursor must NOT have been hidden — a degraded display
        # has no panel to anchor, so the cursor should be left alone.
        assert self.HIDE_CURSOR not in out, f"hide-cursor emitted in degraded mode:\n{out!r}"

    def test_force_size_at_threshold_does_not_degrade(self) -> None:
        """Exactly (80, 24) is the supported minimum, not below."""
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(80, 24))
            display.stop()
        assert display._degraded is False

    def test_force_size_just_below_cols_threshold_degrades(self) -> None:
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(79, 24))
            display.stop()
        assert display._degraded is True

    def test_force_size_just_below_rows_threshold_degrades(self) -> None:
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(80, 23))
            display.stop()
        assert display._degraded is True

    def test_non_tty_is_never_degraded(self) -> None:
        """Pipe/CI mode has its own no-op behaviour and shouldn't gain
        the warning line — it'd corrupt downstream consumers."""
        display = Display(is_tty=False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(40, 8))
        assert display._degraded is False
        # No warning text was printed.
        assert buf.getvalue() == ""


class TestDegradedModeFallthrough:
    """In degraded mode update() drops the status content (we don't
    flood stdout with 4Hz status snapshots) and print_log() prints
    plain text. No DEC frames, no cursor sequences."""

    BSU = "\x1b[?2026h"
    ESU = "\x1b[?2026l"

    def test_update_in_degraded_mode_emits_no_dec_frame(self) -> None:
        display = Display(is_tty=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            display.start(force_size=(40, 8))
            # Reset the buffer to isolate the update() output from the
            # startup warning line.
        # Print the warning above, then capture only update() output.
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            display.update("status: 1/3 hosts")

        out = buf2.getvalue()
        assert self.BSU not in out
        assert self.ESU not in out
        # Status snapshots are discarded in degraded mode: the live
        # panel doesn't exist and printing every 250ms would spam
        # stdout. The most recent content is still stored on the
        # instance so a re-enable can resume drawing it.
        assert out == ""
        assert display._content == "status: 1/3 hosts"

    def test_print_log_in_degraded_mode_emits_plain_text(self) -> None:
        display = Display(is_tty=True)
        with redirect_stdout(io.StringIO()):
            display.start(force_size=(40, 8))

        buf = io.StringIO()
        with redirect_stdout(buf):
            display.print_log("PLAY [Setup] (localhost, 1 host, 3 tasks)")

        out = buf.getvalue()
        assert "PLAY [Setup] (localhost, 1 host, 3 tasks)" in out
        assert self.BSU not in out
        assert self.ESU not in out
        # Trailing newline so consecutive print_log lines don't merge.
        assert out.endswith("\n")

    def test_stop_in_degraded_mode_is_a_noop(self) -> None:
        """No panel was ever shown, so stop() must not emit clear/show
        sequences that would corrupt the user's shell."""
        display = Display(is_tty=True)
        with redirect_stdout(io.StringIO()):
            display.start(force_size=(40, 8))

        buf = io.StringIO()
        with redirect_stdout(buf):
            display.stop()

        assert buf.getvalue() == ""

    def test_clear_in_degraded_mode_is_a_noop(self) -> None:
        display = Display(is_tty=True)
        with redirect_stdout(io.StringIO()):
            display.start(force_size=(40, 8))

        buf = io.StringIO()
        with redirect_stdout(buf):
            display.clear()

        assert buf.getvalue() == ""
        # The stored content was wiped though, so a re-enable starts blank.
        assert display._content == ""
