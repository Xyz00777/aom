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
