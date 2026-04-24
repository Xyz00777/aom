"""Status bar widget for AOM TUI.

Configurable status bar showing playbook info.
See SPECIFICATION.md Section 7.4 for status bar details.
"""

from datetime import datetime

from rich.text import Text
from textual.widget import Widget

from ansible_aom.core.config import StatusBarConfig


class StatusBar(Widget):
    """Configurable status bar showing playbook name, time, progress."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        width: 100%;
        background: $surface;
        color: $text;
    }
    """

    def __init__(
        self,
        config: StatusBarConfig | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize the status bar widget.

        Args:
            config: Status bar configuration (uses defaults if None)
            name: Widget name
            id: Widget ID
            classes: Space-separated list of class names
            disabled: Whether the widget is disabled
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.config = config or StatusBarConfig()
        self._playbook_name: str = ""
        self._start_time: datetime | None = None
        self._task_progress: tuple[int, int] = (0, 0)
        self._current_task: str = ""
        self._host_count: tuple[int, int] = (0, 0)
        self._memory_usage: tuple[float, float] | None = None
        self._subprocess_pid: int | None = None

    def set_playbook_name(self, name: str) -> None:
        """Set the playbook name.

        Args:
            name: The playbook file name
        """
        self._playbook_name = name

    def set_elapsed_time(self, start_time: datetime) -> None:
        """Set the start time for elapsed time calculation.

        Args:
            start_time: When the playbook started
        """
        self._start_time = start_time

    def set_task_progress(self, completed: int, total: int) -> None:
        """Set task progress.

        Args:
            completed: Number of completed tasks
            total: Total number of tasks
        """
        self._task_progress = (completed, total)

    def set_current_task(self, task: str) -> None:
        """Set the current task name.

        Args:
            task: The current task name
        """
        self._current_task = task

    def set_host_count(self, completed: int, total: int) -> None:
        """Set host progress count.

        Args:
            completed: Number of completed hosts
            total: Total number of hosts
        """
        self._host_count = (completed, total)

    def set_memory_usage(self, rss_mb: float, vsz_mb: float) -> None:
        """Set memory usage.

        Args:
            rss_mb: Resident set size in MB
            vsz_mb: Virtual memory size in MB
        """
        self._memory_usage = (rss_mb, vsz_mb)

    def set_subprocess_pid(self, pid: int | None) -> None:
        """Set the subprocess PID.

        Args:
            pid: The subprocess PID (or None if not running)
        """
        self._subprocess_pid = pid

    def _format_elapsed_time(self) -> str:
        """Format elapsed time as H:MM:SS or M:SS.

        Returns:
            Formatted time string
        """
        if self._start_time is None:
            return "0:00"

        elapsed = datetime.now() - self._start_time
        total_seconds = int(elapsed.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def _format_host_count(self) -> str:
        """Format host count.

        Returns:
            Formatted host count string
        """
        completed, total = self._host_count
        return f"{completed}/{total} hosts"

    def _format_task_progress(self) -> str:
        """Format task progress.

        Returns:
            Formatted task progress string
        """
        completed, total = self._task_progress
        return f"{completed}/{total}"

    def _format_memory_usage(self) -> str:
        """Format memory usage.

        Returns:
            Formatted memory string or N/A
        """
        if self._memory_usage is None:
            return "RSS: N/A VSZ: N/A"
        rss, vsz = self._memory_usage
        return f"RSS: {rss:.0f}m VSZ: {vsz:.0f}m"

    def _format_pid(self) -> str:
        """Format PID.

        Returns:
            Formatted PID string or N/A
        """
        if self._subprocess_pid is None:
            return "PID: N/A"
        return f"PID: {self._subprocess_pid}"

    def render(self) -> Text:
        """Render the status bar.

        Returns:
            Rich Text object with configured elements separated by │
        """
        elements = self.config.elements or ["playbook_name", "elapsed_time", "task_progress"]

        element_map = {
            "playbook_name": self._playbook_name or "",
            "elapsed_time": self._format_elapsed_time(),
            "task_progress": self._format_task_progress(),
            "current_task": self._current_task or "",
            "host_count": self._format_host_count(),
            "memory_usage": self._format_memory_usage(),
            "subprocess_pid": self._format_pid(),
        }

        parts = []
        for element in elements:
            if element in element_map:
                value = element_map[element]
                if value:
                    parts.append(value)

        return Text(" │ ".join(parts)) if parts else Text("")
