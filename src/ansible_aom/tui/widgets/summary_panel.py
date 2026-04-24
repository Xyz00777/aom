"""Summary panel widget for AOM TUI.

Play-level overview with stats.
See SPECIFICATION.md Section 7.3 for summary panel details.

TDD: This file contains STUB implementations only. Tests come first.
"""

from textual.widget import Widget

from ansible_aom.core.icons import STATUS_ICONS
from ansible_aom.core.models import Status


class SummaryPanel(Widget):
    """Summary panel showing play-level stats."""

    DEFAULT_CSS = """
    SummaryPanel {
        height: auto;
        width: 1fr;
        padding: 1;
    }
    """

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize the summary panel widget.

        Args:
            name: Widget name
            id: Widget ID
            classes: Space-separated list of class names
            disabled: Whether the widget is disabled
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._play_name: str = "No active play"
        self._hosts_completed: int = 0
        self._hosts_total: int = 0
        self._tasks_completed: int = 0
        self._tasks_total: int = 0
        self._elapsed_seconds: int = 0

    def set_play_name(self, name: str) -> None:
        """Set the current play name.

        Args:
            name: The play name
        """
        self._play_name = name if name else "No active play"

    def set_hosts_progress(self, completed: int, total: int) -> None:
        """Set hosts progress.

        Args:
            completed: Number of completed hosts
            total: Total number of hosts
        """
        self._hosts_completed = completed
        self._hosts_total = total

    def set_tasks_progress(self, completed: int, total: int) -> None:
        """Set tasks progress.

        Args:
            completed: Number of completed tasks
            total: Total number of tasks
        """
        self._tasks_completed = completed
        self._tasks_total = total

    def set_elapsed_time(self, seconds: int) -> None:
        """Set elapsed time in seconds.

        Args:
            seconds: Elapsed time in seconds
        """
        self._elapsed_seconds = seconds

    def _format_elapsed_time(self) -> str:
        """Format elapsed time.

        Returns:
            Formatted time string (H:MM:SS or M:SS)
        """
        total_seconds = self._elapsed_seconds
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def format_host_status_line(
        self,
        hostname: str,
        ok: int = 0,
        changed: int = 0,
        failed: int = 0,
        skipped: int = 0,
        unreachable: int = 0,
        pending: int = 0,
    ) -> str:
        """Format a host status line with icons.

        Args:
            hostname: The host name
            ok: Number of OK tasks
            changed: Number of changed tasks
            failed: Number of failed tasks
            skipped: Number of skipped tasks
            unreachable: Number of unreachable
            pending: Number of pending tasks

        Returns:
            Formatted status line string
        """
        parts = [f"{hostname}:"]

        if ok > 0:
            parts.append(f"{STATUS_ICONS[Status.OK]} {ok} ok")
        if changed > 0:
            parts.append(f"{STATUS_ICONS[Status.CHANGED]} {changed} changed")
        if failed > 0:
            parts.append(f"{STATUS_ICONS[Status.FAILED]} {failed} failed")
        if skipped > 0:
            parts.append(f"{STATUS_ICONS[Status.SKIPPED]} {skipped} skipped")
        if unreachable > 0:
            parts.append(f"{STATUS_ICONS[Status.UNREACHABLE]} {unreachable} unreachable")
        if pending > 0:
            parts.append(f"{STATUS_ICONS[Status.PENDING]} {pending} pending")

        return " ".join(parts)

    def get_status_icon(self, status: Status) -> str:
        """Get the icon for a status.

        Args:
            status: The status to get icon for

        Returns:
            Unicode icon string
        """
        return STATUS_ICONS.get(status, "?")
