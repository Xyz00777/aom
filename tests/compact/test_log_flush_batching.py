"""Cross-event log batching — cap frame rate during event storms.

Per-event batching (test_emit_event_log_batching.py) collapses N host
lines into one ``print_log`` per event, but each ``print_log`` still
emits its own rewind+clear+redraw frame. At hundreds of events/sec the
status block is repainted hundreds of times a second — visible flicker
even on DEC-2026 terminals (kitty enforces a timeout on synchronized
updates, so back-to-back frames can tear).

Contract pinned here: ``Display`` buffers log lines and flushes them
leading-edge on a ~30 Hz window. The first line of a burst renders
immediately; lines arriving within ``_LOG_FLUSH_INTERVAL_S`` of the
last flush are buffered and emitted together in the next frame. Any
frame-writing path (``update``, ``stop``, shrink-to-degraded) drains
the buffer so no log line is ever lost or reordered.
"""

from __future__ import annotations

import io
import time
from contextlib import redirect_stdout

from ansible_aom.compact.display import Display

BSU = "\x1b[?2026h"
ESU = "\x1b[?2026l"

# A monotonic timestamp far in the future: "the window has NOT elapsed"
# no matter how slow the test machine is. Backdating to 0.0 means
# "never flushed" → the window HAS elapsed.
_WINDOW_OPEN = 0.0


def _fresh_display() -> Display:
    display = Display(is_tty=True)
    display.start()
    return display


def _pin_window_closed(display: Display) -> None:
    """Force 'a flush just happened' so subsequent print_log calls buffer."""
    display._last_log_flush_time = time.monotonic() + 3600.0


class TestLeadingEdgeFlush:
    def test_first_log_line_of_burst_renders_immediately(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = _fresh_display()
            display.print_log("line1")

        assert "line1" in buf.getvalue()

    def test_lines_within_window_are_buffered_not_written(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = _fresh_display()
            display.print_log("line1")
            _pin_window_closed(display)
            display.print_log("line2")
            display.print_log("line3")

        out = buf.getvalue()
        assert "line1" in out
        assert "line2" not in out
        assert "line3" not in out

    def test_buffered_lines_flush_together_in_one_frame(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = _fresh_display()
            display.print_log("line1")
            _pin_window_closed(display)
            display.print_log("line2")
            display.print_log("line3")
            frames_before = buf.getvalue().count(BSU)
            display._last_log_flush_time = _WINDOW_OPEN
            display.print_log("line4")

        out = buf.getvalue()
        # Exactly one more frame carrying all three pending lines, in order.
        assert out.count(BSU) == frames_before + 1
        assert out.index("line2") < out.index("line3") < out.index("line4")

    def test_flush_logs_drains_buffer(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = _fresh_display()
            display.print_log("line1")
            _pin_window_closed(display)
            display.print_log("line2")
            display.flush_logs()

        assert "line2" in buf.getvalue()

    def test_flush_logs_is_noop_when_buffer_empty(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = _fresh_display()
            display.print_log("line1")
            frames_before = buf.getvalue().count(BSU)
            display.flush_logs()

        assert buf.getvalue().count(BSU) == frames_before


class TestDrainOnOtherFrames:
    def test_update_drains_pending_logs_above_new_status(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = _fresh_display()
            display.print_log("line1")
            _pin_window_closed(display)
            display.print_log("pending-line")
            # Open both the status throttle and write a new status.
            display._last_status_update_time = 0.0
            display._last_log_flush_time = _WINDOW_OPEN
            display.update("NEW-STATUS")

        out = buf.getvalue()
        assert "pending-line" in out
        assert out.index("pending-line") < out.index("NEW-STATUS")

    def test_stop_drains_pending_logs(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = _fresh_display()
            display.print_log("line1")
            _pin_window_closed(display)
            display.print_log("last-words")
            display.stop()

        assert "last-words" in buf.getvalue()

    def test_shrink_to_degraded_does_not_lose_pending_logs(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = _fresh_display()
            display.print_log("line1")
            _pin_window_closed(display)
            display.print_log("survivor")
            # Terminal shrinks below minimum → degraded-mode wipe.
            display.update("status", force_size=(40, 10))

        assert "survivor" in buf.getvalue()


class TestRendererTickFlushes:
    def test_tick_drains_pending_display_logs(self) -> None:
        """The quiet-period tick is the backstop flush: the last lines of
        a burst must not sit buffered until the next event arrives."""
        from unittest.mock import MagicMock

        from ansible_aom.compact.renderer import CompactRenderer

        renderer = CompactRenderer(is_tty=True)
        renderer.start("test.yml", [])
        renderer._display = MagicMock()
        renderer.tick()

        assert renderer._display.flush_logs.called


class TestNonTtyUnaffected:
    def test_non_tty_print_log_stays_immediate_and_plain(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            display = Display(is_tty=False)
            display.start()
            display.print_log("line1")
            display.print_log("line2")

        out = buf.getvalue()
        assert "line1" in out
        assert "line2" in out
        assert BSU not in out
