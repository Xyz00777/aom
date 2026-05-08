"""Display logic for compact mode — nom-style fixed-bottom status panel.

Renders directly to stdout using ANSI cursor positioning and DEC mode 2026
(synchronized output) — no Rich Live, no alternate screen buffer. This gives
a true nom-style "logs scroll above, status fixed at bottom" experience
without flicker. See SPECIFICATION.md Section 4.1 and
.sisyphus/notepads/new-spec/open-questions.md "Summary of nom-Style Compact
View Research".
"""

from __future__ import annotations

import sys

# Terminal size constants (SPECIFICATION.md Section 4.4)
MINIMUM_LINES = 24
MINIMUM_COLUMNS = 80

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

    def start(self) -> None:
        """Begin owning the bottom of the terminal."""
        if not self._is_tty:
            return
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

        If content is None, the current content is re-rendered (useful
        after a terminal resize, though resize handling is out of scope
        for this slice).
        """
        if not self._is_tty:
            return
        if content is not None:
            self._content = content
        if not self._is_running:
            return

        rendered = self._content
        new_rows = _row_count(rendered)
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + rendered + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = new_rows

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
        new_rows = _row_count(rendered)
        frame = _BSU + self._rewind_status() + _CLEAR_TO_EOS + log + rendered + _ESU
        sys.stdout.write(frame)
        sys.stdout.flush()
        self._status_rows = new_rows

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
        """Cursor sequence to move back to the top of the status block."""
        if self._status_rows == 0:
            return ""
        return _CURSOR_UP_FMT.format(n=self._status_rows)


def _row_count(text: str) -> int:
    """How many terminal rows `text` occupies after it's written.

    Counts newlines as row separators. A trailing newline pushes the
    cursor down to a new row, so it contributes a row too. The empty
    string occupies zero rows. This is an approximation — long lines
    that wrap will undercount, but that's acceptable until we add real
    width-aware wrapping.
    """
    if not text:
        return 0
    rows = text.count("\n")
    if not text.endswith("\n"):
        rows += 1
    return rows
