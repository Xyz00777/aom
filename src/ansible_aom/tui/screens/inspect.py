"""Inspect TUI screen for AOM.

Readonly mode for browsing sessions.
See SPECIFICATION.md Section 9 for inspect commands.
"""

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static

from ansible_aom.core.session import load_session


class InspectScreen(Screen):
    """Readonly inspect TUI for browsing sessions.

    Displays session information in TUI format:
    - Session tree (plays/tasks/hosts)
    - Events list
    - Summary statistics

    Closes on Escape.

    Args:
        session_id: Optional session ID to load
        state_dir: Optional state directory (defaults to ~/.local/state/aom/sessions)
    """

    DEFAULT_CSS = """
    InspectScreen {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 1fr;
        grid-rows: 1fr;
    }

    InspectScreen > Static.session-tree {
        column-span: 1;
        overflow: auto;
    }

    InspectScreen > Static.session-info {
        column-span: 1;
        overflow: auto;
    }
    """

    BINDINGS = [
        Binding(key="escape", action="dismiss", description="Close inspect screen"),
    ]

    def __init__(
        self,
        session_id: str | None = None,
        state_dir: Path | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize InspectScreen.

        Args:
            session_id: Optional session ID to load
            state_dir: Optional state directory
            **kwargs: Additional arguments passed to Screen
        """
        super().__init__(**kwargs)
        self._session_id = session_id
        self._state_dir = state_dir or Path.home() / ".local" / "state" / "aom" / "sessions"

    def compose(self) -> ComposeResult:
        session: dict[str, Any] | None = None
        if self._session_id:
            session = load_session(self._session_id, self._state_dir)

        if session:
            tree_lines = self._build_tree_lines(session)
            info_lines = self._build_info_lines(session)
        else:
            tree_lines = self._build_placeholder_tree()
            info_lines = self._build_placeholder_info()

        yield Static("\n".join(tree_lines), id="session-tree", classes="session-tree")
        yield Static("\n".join(info_lines), id="session-info", classes="session-info")

    def _build_tree_lines(self, session: dict[str, Any]) -> list[str]:
        """Build tree panel content from session data.

        Args:
            session: Session dictionary from load_session()

        Returns:
            List of formatted lines for tree panel
        """
        lines = []
        lines.append("Session Tree")
        lines.append("=" * 30)
        lines.append("")

        session_id = session.get("session_id", "unknown")
        short_id = session_id[:8] if session_id else "unknown"
        playbook = session.get("playbook", "unknown")
        status = session.get("status", "unknown")

        lines.append(f"[bold]Session:[/bold] {short_id}")
        lines.append(f"[bold]Playbook:[/bold] {playbook}")
        lines.append(f"[bold]Status:[/bold] {status}")
        lines.append("")

        events = session.get("events", [])
        play_events = [e for e in events if e.get("_event") == "v2_playbook_on_play_start"]

        if play_events:
            lines.append("[bold]Plays:[/bold]")
            for play_event in play_events:
                play = play_event.get("play", {})
                play_name = play.get("name", "unknown")
                lines.append(f"  ▼ {play_name}")
        else:
            lines.append("[dim]No play events[/dim]")

        return lines

    def _build_info_lines(self, session: dict[str, Any]) -> list[str]:
        """Build info panel content from session data.

        Args:
            session: Session dictionary from load_session()

        Returns:
            List of formatted lines for info panel
        """
        lines = []
        lines.append("Session Summary")
        lines.append("=" * 30)
        lines.append("")

        lines.append("[bold]Statistics[/bold]")
        lines.append("-" * 10)

        events = session.get("events", [])
        play_events = [e for e in events if e.get("_event") == "v2_playbook_on_play_start"]
        lines.append(f"  Plays: {len(play_events)}")

        task_events = [
            e
            for e in events
            if e.get("_event")
            in (
                "v2_runner_on_ok",
                "v2_runner_on_failed",
                "v2_runner_on_skipped",
                "v2_runner_on_unreachable",
            )
        ]
        unique_tasks: set[str] = set()
        for event in task_events:
            task = event.get("task", {})
            task_id = task.get("id", "")
            if task_id:
                unique_tasks.add(task_id)
        lines.append(f"  Tasks: {len(unique_tasks)}")

        hosts: set[str] = set()
        for event in events:
            if event.get("_event") == "v2_playbook_on_stats":
                hosts = set(event.get("stats", {}).keys())
                break
        lines.append(f"  Hosts: {len(hosts)}")

        lines.append("")

        lines.append("[bold]Events[/bold]")
        lines.append("-" * 7)
        lines.append(f"  Total: {len(events)}")

        malformed = session.get("malformed_lines", 0)
        if malformed > 0:
            lines.append(f"  Malformed: {malformed}")

        lines.append("")

        lines.append("[bold]Timing[/bold]")
        lines.append("-" * 7)

        start_time = session.get("start_time")
        if start_time:
            lines.append(f"  Started: {start_time}")

        end_time = session.get("end_time")
        if end_time:
            lines.append(f"  Ended: {end_time}")

        duration = session.get("duration_seconds")
        if duration is not None:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            if hours > 0:
                lines.append(f"  Duration: {hours}:{minutes:02d}:{seconds:02d}")
            else:
                lines.append(f"  Duration: {minutes}:{seconds:02d}")

        lines.append("")
        lines.append("[dim]Press Escape to close[/dim]")

        return lines

    def _build_placeholder_tree(self) -> list[str]:
        lines = []
        lines.append("Session Tree")
        lines.append("=" * 30)
        lines.append("")
        lines.append("[dim]No session loaded[/dim]")
        lines.append("")
        lines.append("Use: aom inspect <session-id> --tui")
        return lines

    def _build_placeholder_info(self) -> list[str]:
        lines = []
        lines.append("Session Summary")
        lines.append("=" * 30)
        lines.append("")
        lines.append("[bold]Statistics[/bold]")
        lines.append("-" * 10)
        lines.append("  Plays: 0")
        lines.append("  Tasks: 0")
        lines.append("  Hosts: 0")
        lines.append("")
        lines.append("[bold]Events[/bold]")
        lines.append("-" * 7)
        lines.append("  Total: 0")
        lines.append("")
        lines.append("[dim]Press Escape to close[/dim]")
        return lines

    async def action_dismiss(self, result: Any | None = None) -> None:
        self.app.pop_screen()
