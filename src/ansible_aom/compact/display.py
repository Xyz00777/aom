"""Display logic for compact mode.

Rich Live + blessed display implementation.
See SPECIFICATION.md Section 4.1 for rendering details.

TDD: Tests defined in tests/integration/test_compact_renderer.py.
"""


class Display:
    """Manages Rich Live display and ANSI cursor positioning.

    Handles terminal rendering for compact mode including:
    - Rich Live updates at 4 FPS
    - Status bar formatting
    - Host summary display
    - Terminal size handling
    """

    def __init__(self) -> None:
        """Initialize the display manager."""
        self._is_running = False
        self._content = ""

    def start(self) -> None:
        """Start the Rich Live display."""
        self._is_running = True

    def stop(self) -> None:
        """Stop the Rich Live display and restore terminal state."""
        self._is_running = False

    def update(self, content: str) -> None:
        """Update the display content.

        Args:
            content: New content to display in the status panel.
        """
        self._content = content

    def print_log(self, line: str) -> None:
        """Print a log line above the live display.

        Args:
            line: Log line to print.
        """
        pass

    def clear(self) -> None:
        """Clear the display and reset to initial state."""
        self._content = ""