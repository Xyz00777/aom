"""Display logic for compact mode.

Rich Live display implementation for compact mode.
See SPECIFICATION.md Section 4.1 for rendering details.

TDD: Tests defined in tests/integration/test_compact_renderer.py.
"""

from __future__ import annotations

from rich.console import Console
from rich.live import Live

# Terminal size constants (SPECIFICATION.md Section 4.4)
MINIMUM_LINES = 24
MINIMUM_COLUMNS = 80


def check_terminal_size(
    lines: int | None = None, columns: int | None = None
) -> tuple[bool, str]:
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
    # Auto-detect if not provided
    if lines is None or columns is None:
        try:
            import shutil

            detected_columns, detected_lines = shutil.get_terminal_size()
            if lines is None:
                lines = detected_lines
            if columns is None:
                columns = detected_columns
        except Exception:
            # Fallback to defaults if detection fails
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
    """Manages Rich Live display for compact mode.

    Handles terminal rendering for compact mode including:
    - Rich Live updates at 4 FPS
    - Log output above the status panel
    - Terminal size handling
    - Non-TTY fallback

    Attributes:
        MINIMUM_LINES: Minimum terminal lines required (24)
        MINIMUM_COLUMNS: Minimum terminal columns required (80)
    """

    MINIMUM_LINES = MINIMUM_LINES
    MINIMUM_COLUMNS = MINIMUM_COLUMNS

    def __init__(self, is_tty: bool = True) -> None:
        """Initialize the display manager.

        Args:
            is_tty: Whether stdout is a TTY. If False, disable interactive features.
        """
        self._is_tty = is_tty
        self._is_running = False
        self._content = ""
        self._live: Live | None = None
        self._console: Console | None = None

    def start(self) -> None:
        """Start the Rich Live display context.

        Initializes terminal state (hides cursor if TTY).
        Creates Rich Live instance with refresh_per_second=4.

        Non-TTY Behavior:
            This is a no-op when is_tty=False.
        """
        if not self._is_tty:
            return

        # Create console for this display
        self._console = Console(
            force_terminal=True,
            force_interactive=False,
            legacy_windows=False,
        )

        # Create Live display with 4 FPS refresh (SPECIFICATION.md Section 4.3)
        self._live = Live(
            "",  # Initial content
            console=self._console,
            refresh_per_second=4,
            vertical_overflow="ellipsis",
            auto_refresh=True,
        )
        self._live.start()
        self._is_running = True

    def stop(self) -> None:
        """Stop the Rich Live display and restore terminal state.

        Restores terminal state:
        - Shows cursor (if hidden)
        - Resets colors and styles
        - Flushes output

        Non-TTY Behavior:
            This is a no-op when is_tty=False.
        """
        if not self._is_tty:
            return

        if self._live is not None:
            self._live.stop()
            self._live = None

        self._is_running = False

        # Reset console output - show cursor
        if self._console is not None:
            self._console.show_cursor()

    def update(self, content: str | None = None) -> None:
        """Update the display content.

        If content is None, refresh with current content.

        Args:
            content: New content to display in the status panel.
                     If None, uses current content.

        Non-TTY Behavior:
            This is a no-op when is_tty=False (line-by-line output instead).
        """
        if not self._is_tty:
            return

        if content is not None:
            self._content = content

        if self._live is not None and self._is_running:
            self._live.update(self._content)

    def print_log(self, message: str) -> None:
        """Print a log line ABOVE the live display.

        Uses live.console.print() to output above the status panel.
        The message passes through Rich markup for color support.

        Args:
            message: Log line to print (may contain Rich markup).

        Non-TTY Behavior:
            Writes to stdout without Rich formatting.
        """
        if not self._is_tty:
            # Non-TTY: Plain output without formatting
            print(message)
            return

        if self._console is not None and self._live is not None:
            # Print above the live display using the live's console
            self._live.console.print(message)

    def clear(self) -> None:
        """Clear the display content and reset internal state.

        Clears the status panel content and resets internal buffers.
        Does not stop the live display (use stop() for that).
        """
        self._content = ""
        if self._live is not None and self._is_running:
            self._live.update("")

    @property
    def is_running(self) -> bool:
        """Check if the display is currently running.

        Returns:
            True if start() was called and stop() not yet called.
        """
        return self._is_running

    @property
    def is_tty(self) -> bool:
        """Check if the display is in TTY mode.

        Returns:
            True if output is a TTY, False for piped/redirected output.
        """
        return self._is_tty
