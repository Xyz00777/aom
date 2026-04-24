"""Log panel widget for AOM TUI.

RichLog with search functionality.
See SPECIFICATION.md Section 7.2 for log panel details.

TDD: This file contains STUB implementations only. Tests come first.
"""

from typing import TYPE_CHECKING

from textual.widgets import RichLog

from ansible_aom.core.state import MAX_LOG_LINES

if TYPE_CHECKING:
    from textual.events import Mount


def is_vertical_scroll_end(scroll_offset: int, total_lines: int, visible_height: int) -> bool:
    """Determine if scrolled to the end (bottom).

    Args:
        scroll_offset: Index of first visible line
        total_lines: Total number of lines in the log
        visible_height: Number of lines visible in viewport

    Returns:
        True if scrolled to bottom (last line visible)
    """
    return scroll_offset + visible_height >= total_lines


class LogPanel(RichLog):
    """Log panel with search support."""

    DEFAULT_CSS = """
    LogPanel {
        height: 100%;
        width: 1fr;
    }
    """

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        max_lines: int = MAX_LOG_LINES,
    ) -> None:
        """Initialize the log panel widget.

        Args:
            name: Widget name
            id: Widget ID
            classes: Space-separated list of class names
            disabled: Whether the widget is disabled
            max_lines: Maximum number of lines to keep (default: MAX_LOG_LINES)
        """
        super().__init__(
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            max_lines=max_lines,
        )
        self._auto_scroll = True

    def _on_mount(self, event: "Mount") -> None:
        """Handle widget mount event."""
        self._auto_scroll = True

    def write_line(self, line: str) -> None:
        """Write a line to the log, auto-scrolling if enabled.

        Args:
            line: The line to write
        """
        super().write(line)
