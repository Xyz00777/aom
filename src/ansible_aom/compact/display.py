"""Display logic for compact mode — nom-style fixed-bottom status panel.

Renders directly to stdout using ANSI cursor positioning and DEC mode 2026
(synchronized output) — no Rich Live, no alternate screen buffer. This gives
a true nom-style "logs scroll above, status fixed at bottom" experience
without flicker. See SPECIFICATION.md Section 4.1 and
.sisyphus/notepads/new-spec/open-questions.md "Summary of nom-Style Compact
View Research".
"""

from __future__ import annotations

import shutil
import sys
import time

# Terminal size constants (SPECIFICATION.md Section 4.4)
MINIMUM_LINES = 24
MINIMUM_COLUMNS = 80
# (cols, rows) threshold for the live panel. Below this we degrade to
# a plain log-only stream — see R4 in .sisyphus/notepads/plans/robustness.md.
MINIMUM_SIZE = (MINIMUM_COLUMNS, MINIMUM_LINES)

# Maximum status redraws per second. Bursts of state events get coalesced
# into the most-recent content; the next eligible update flushes whatever
# the latest state happens to be. Matches Rich Live's old refresh_per_second=4.
_THROTTLE_INTERVAL_S = 0.25

# DEC mode 2026 — Synchronized Output. Wrapping a frame between BSU/ESU
# tells the terminal to buffer the bytes and apply them atomically, so
# multi-line redraws never produce a torn frame. Terminals that don't
# implement 2026 ignore the codes silently.
_BSU = "\x1b[?2026h"
_ESU = "\x1b[?2026l"

_HIDE_CURSOR = "\x1b[?25l"
_SHOW_CURSOR = "\x1b[?25h"
# Erase from cursor to end of screen. Used to wipe the previous status
# block before redrawing.
_CLEAR_TO_EOS = "\x1b[J"
# Move cursor up N lines, column 1.
_CURSOR_UP_FMT = "\x1b[{n}F"


def check_terminal_size(lines: int | None = None, columns: int | None = None) -> tuple[bool, str]:
    """Check if terminal meets minimum size requirements.

    Args:
        lines: Number of lines (rows). If None, auto-detect.
        columns: Number of columns. If None, auto-detect.

    Returns:
        Tuple of (is_ok, error_message). error_message is empty string if OK.

    Example:
        >>> ok, msg = check_terminal_size(24, 80)
        >>> ok
        True
        >>> ok, msg = check_terminal_size(20, 60)
        >>> ok
        False
        >>> "Terminal too small" in msg
        True
    """
    if lines is None or columns is None:
        try:
            import shutil

            detected_columns, detected_lines = shutil.get_terminal_size()
            if lines is None:
                lines = detected_lines
            if columns is None:
                columns = detected_columns
        except Exception:
            if lines is None:
                lines = 24
            if columns is None:
                columns = 80

    if lines < MINIMUM_LINES or columns < MINIMUM_COLUMNS:
        return (
            False,
            f"Terminal too small: {lines}×{columns}. "
            f"Minimum: {MINIMUM_LINES}×{MINIMUM_COLUMNS}. "
            f"Resize or use --no-tui flag.",
        )
    return True, ""


class Display:
    """Manages the nom-style compact display.

    Owns stdout for the duration of the run. The status panel is drawn
    at the cursor and stays "anchored" by tracking how many lines it
    occupies — every redraw rewinds that many lines, clears, and writes
    the new content. Log lines are printed by first wiping the status
    block, writing the log, then re-emitting the status below it.

    Public API is intentionally identical to the previous Rich Live
    implementation so callers (CompactRenderer) don't need to change.
    """

    MINIMUM_LINES = MINIMUM_LINES
    MINIMUM_COLUMNS = MINIMUM_COLUMNS

    def __init__(self, is_tty: bool = True) -> None:
        """Initialize the display manager.

        Args:
            is_tty: Whether stdout is a TTY. If False, all positioning
                and synchronization codes are suppressed and updates
                become no-ops; log lines still print as plain text.
        """
        self._is_tty = is_tty
        self._is_running = False
        self._content = ""
        # Number of terminal rows the current status block occupies.
        # 0 means nothing is currently drawn that needs to be cleared.
        self._status_rows = 0
        # Monotonic timestamp of the last status frame written to stdout.
        # 0.0 means we've never written, so the first update goes through
        # without waiting for the throttle window.
        self._last_update_time = 0.0
        # R4: True when the terminal is below MINIMUM_SIZE. Degraded
        # mode disables the live panel entirely and falls back to a
        # plain log-only stream. Re-checked on every update() so the
        # panel re-enables transparently when the terminal grows.
        self._degraded = False
        # Tracks whether we've already printed the "terminal too small"
        # warning so we don't spam it on every update() while degraded.
        self._degraded_warning_printed = False

    def start(self, force_size: tuple[int, int] | None = None) -> None:
        """Begin owning the bottom of the terminal.

        Args:
            force_size: ``(cols, rows)`` override for ``shutil.get_terminal_size``.
                Used by tests to drive the degraded-mode logic deterministically.
                When None, the actual terminal size is queried.
        """
        if not self._is_tty:
            return

        cols, rows = force_size if force_size is not None else shutil.get_terminal_size()
        if (cols, rows) < MINIMUM_SIZE:
            # Degraded mode: no panel, no cursor anchoring, no DEC frames.
            # Print the warning OUTSIDE any synchronization sequence so it
            # survives on terminals that don't implement DEC 2026.
            self._degraded = True
            if not self._degraded_warning_printed:
                print(
                    f"[aom] terminal too small ({cols}×{rows}); "
                    f"minimum is {MINIMUM_SIZE[0]}×{MINIMUM_SIZE[1]}. "
                    f"Falling back to plain log output until you resize.",
                )
                self._degraded_warning_printed = True
            return

        self._degraded = False
        sys.stdout.write(_HIDE_CURSOR)
        sys.stdout.flush()
        self._is_running = True

    def stop(self) -> None:
        """Erase the status block and release the terminal."""
        if not self._is_tty:
            return
        # Wipe whatever status block is currently visible so the user's
        # shell prompt doesn't appear on top of leftover content.
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + _SHOW_CURSOR + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._is_running = False
        self._status_rows = 0

    def update(self, content: str | None = None) -> None:
        """Redraw the status block with new content.

        Updates within _THROTTLE_INTERVAL_S of the last write are coalesced:
        the new content is stored but no frame is emitted. The next eligible
        call will render whatever the latest content is. If content is None,
        the current content is re-rendered.
        """
        if not self._is_tty:
            return
        if content is not None:
            self._content = content
        if not self._is_running:
            return

        now = time.monotonic()
        if self._last_update_time and (now - self._last_update_time) < _THROTTLE_INTERVAL_S:
            return

        rendered = self._content
        new_rows = _row_count(rendered, _terminal_width())
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + rendered + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = new_rows
        self._last_update_time = now

    def print_log(self, message: str) -> None:
        """Print a log line above the status block.

        Wipes the status, writes the log line, then re-renders the
        status. The whole operation is a single synchronized frame so
        the user never sees an intermediate state.
        """
        if not self._is_tty:
            print(message)
            return

        # Ensure the log line ends with exactly one newline so the
        # following status rendering starts on a fresh row.
        log = message if message.endswith("\n") else message + "\n"
        rendered = self._content
        new_rows = _row_count(rendered, _terminal_width())
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + log + rendered + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = new_rows
        # The status was just redrawn as part of this frame, so reset the
        # throttle clock — the next update() should compete from "now".
        self._last_update_time = time.monotonic()

    def clear(self) -> None:
        """Erase the status content (but leave the display running)."""
        self._content = ""
        if not self._is_tty or not self._is_running:
            return
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = 0

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_tty(self) -> bool:
        return self._is_tty

    def _rewind_status(self) -> str:
        """Cursor sequence to move back to the start of the status block.

        After writing an N-row status (no trailing newline), the cursor
        sits on the LAST row of the block. To get back to the first row
        and column 1 we need to move up N-1 lines, then to col 1.

        N = 1: cursor is already on the right row → just `\\r`.
        N > 1: `CSI (N-1) F` (cursor previous line, N-1 up + col 1).

        Using `CSI N F` for N=1 was a bug: it moved up onto the line
        above the status, which is the user's shell command line.
        The subsequent `CSI J` then wiped that command line.
        """
        if self._status_rows == 0:
            return ""
        if self._status_rows == 1:
            return "\r"
        return _CURSOR_UP_FMT.format(n=self._status_rows - 1)


def _terminal_width() -> int:
    """Current terminal width in columns, with a sensible fallback.

    Queried fresh on every render so that resizing the terminal mid-run
    (SIGWINCH) is picked up by the next redraw without needing an
    explicit signal handler. ``shutil.get_terminal_size`` reads the
    underlying TIOCGWINSZ ioctl, which the kernel keeps current.
    """
    return shutil.get_terminal_size((80, 24)).columns


def _row_count(text: str, width: int) -> int:
    """How many terminal rows `text` occupies at the given terminal `width`.

    Each logical line consumes ``ceil(len(line) / width)`` rows because
    the terminal wraps at the right margin. A trailing newline doesn't
    contribute a row — the cursor sits at the start of the next line
    but nothing has been rendered there yet. The empty string is zero
    rows.

    Width-awareness is what makes the rewind step correct on narrow
    terminals: with the previous newline-only counter, a status bar
    that wrapped from 1 logical line into 2 rendered rows would only
    rewind by 1, leaving stale half-bar visible on the next redraw.

    Note: ``len()`` undercounts East Asian wide chars (emoji, CJK) —
    those occupy two columns each but Python counts them as one. Status
    bar content is BMP punctuation and ASCII, so this approximation is
    safe for the AOM call sites; revisit if we ever push wide content
    through ``Display.update()``.
    """
    if not text:
        return 0
    lines = text.split("\n")
    # A trailing newline produces an empty final element ("abc\n" -> ["abc", ""]).
    # That empty trailing line is "where the cursor sits next", not a rendered row.
    if lines[-1] == "":
        lines = lines[:-1]
    rows = 0
    for line in lines:
        if not line:
            rows += 1
        else:
            # ceil(len / width); the -1/+1 dance avoids importing math.
            rows += (len(line) - 1) // width + 1
    return rows
