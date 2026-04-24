"""Debug panel widget for AOM TUI.

Shows internal state for debugging.
See SPECIFICATION.md Section 7.5 for debug panel details.
"""

from rich.text import Text
from textual.widget import Widget


class DebugPanel(Widget):
    """Debug panel showing internal state."""

    DEFAULT_CSS = """
    DebugPanel {
        display: none;
        height: auto;
        max-height: 50%;
        width: 1fr;
        padding: 1;
        background: $surface-darken-1;
        border: solid $primary;
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
        """Initialize the debug panel widget.

        Args:
            name: Widget name
            id: Widget ID
            classes: Space-separated list of class names
            disabled: Whether the widget is disabled
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        # Debug data fields (12 fields as per spec)
        self._command: str = ""
        self._env_overrides: dict[str, str] = {}
        self._event_count: int = 0
        self._parsing_errors: list[str] = []
        self._callback_status: str = "idle"
        self._timing_stats: dict[str, float] = {}
        self._subprocess_pid: int | None = None
        self._state_tree: dict[str, int] = {}
        self._pending_events: int = 0
        self._memory_usage: tuple[float, float] | None = None
        self._renderer_fps: float = 0.0
        self._event_latency: float = 0.0

    def set_command(self, command: str) -> None:
        """Set the command line.

        Args:
            command: The ansible-playbook command
        """
        self._command = command

    def set_env_overrides(self, env: dict[str, str]) -> None:
        """Set environment overrides.

        Args:
            env: Dictionary of environment variable overrides
        """
        self._env_overrides = env.copy()

    def set_event_count(self, count: int) -> None:
        """Set event count.

        Args:
            count: Number of events processed
        """
        self._event_count = count

    def set_parsing_errors(self, errors: list[str]) -> None:
        """Set parsing errors.

        Args:
            errors: List of parsing error messages
        """
        self._parsing_errors = errors.copy()

    def set_callback_status(self, status: str) -> None:
        """Set callback status.

        Args:
            status: Callback status string
        """
        self._callback_status = status

    def set_timing_stats(self, stats: dict[str, float]) -> None:
        """Set timing statistics.

        Args:
            stats: Dictionary of timing stats (name -> milliseconds)
        """
        self._timing_stats = stats.copy()

    def set_subprocess_pid(self, pid: int | None) -> None:
        """Set subprocess PID.

        Args:
            pid: The subprocess PID (or None if not running)
        """
        self._subprocess_pid = pid

    def set_state_tree(self, tree: dict[str, int]) -> None:
        """Set state tree stats.

        Args:
            tree: Dictionary of state counts
        """
        self._state_tree = tree.copy()

    def set_pending_events(self, count: int) -> None:
        """Set pending event count.

        Args:
            count: Number of pending events
        """
        self._pending_events = count

    def set_memory_usage(self, rss_mb: float, vsz_mb: float) -> None:
        """Set memory usage.

        Args:
            rss_mb: Resident set size in MB
            vsz_mb: Virtual memory size in MB
        """
        self._memory_usage = (rss_mb, vsz_mb)

    def set_renderer_fps(self, fps: float) -> None:
        """Set renderer FPS.

        Args:
            fps: Frames per second
        """
        self._renderer_fps = fps

    def set_event_latency(self, latency_ms: float) -> None:
        """Set event latency.

        Args:
            latency_ms: Event processing latency in milliseconds
        """
        self._event_latency = latency_ms

    def toggle_visibility(self) -> None:
        """Toggle debug panel visibility (bound to 'D' key)."""
        if self.has_class("visible"):
            self.remove_class("visible")
            self.set_styles("display: none")
        else:
            self.add_class("visible")
            self.set_styles("display: block")

    def get_debug_summary(self) -> dict[str, object]:
        """Get a summary of all debug data.

        Returns:
            Dictionary containing all debug field values
        """
        return {
            "command": self._command,
            "env_overrides": self._env_overrides,
            "event_count": self._event_count,
            "parsing_errors": len(self._parsing_errors),
            "callback_status": self._callback_status,
            "timing_stats": self._timing_stats,
            "subprocess_pid": self._subprocess_pid,
            "state_tree": self._state_tree,
            "pending_events": self._pending_events,
            "memory_usage": self._memory_usage,
            "renderer_fps": self._renderer_fps,
            "event_latency": self._event_latency,
        }

    def render(self) -> Text:
        """Render the debug panel.

        Returns:
            Rich Text object with all debug fields
        """
        lines = []

        lines.append(f"Command: {self._command if self._command else 'N/A'}")

        if self._env_overrides:
            env_str = ", ".join(f"{k}={v}" for k, v in self._env_overrides.items())
            lines.append(f"Environment: {env_str}")
        else:
            lines.append("Environment: (none)")

        lines.append(f"Events: {self._event_count}")

        lines.append(f"Parse errors: {len(self._parsing_errors)}")

        lines.append(f"Callback status: {self._callback_status}")

        if self._timing_stats:
            timing_str = ", ".join(f"{k}={v:.1f}ms" for k, v in self._timing_stats.items())
            lines.append(f"Timing stats: {timing_str}")
        else:
            lines.append("Timing stats: (none)")

        lines.append(f"PID: {self._subprocess_pid if self._subprocess_pid else 'N/A'}")

        if self._state_tree:
            state_str = ", ".join(f"{k}={v}" for k, v in self._state_tree.items())
            lines.append(f"State tree: {state_str}")
        else:
            lines.append("State tree: (none)")

        lines.append(f"Pending events: {self._pending_events}")

        if self._memory_usage:
            rss, vsz = self._memory_usage
            lines.append(f"Memory: RSS: {rss:.0f}m VSZ: {vsz:.0f}m")
        else:
            lines.append("Memory: N/A")

        lines.append(f"Renderer FPS: {self._renderer_fps:.1f}")

        lines.append(f"Event latency: {self._event_latency:.1f}ms")

        return Text("\n".join(lines))
