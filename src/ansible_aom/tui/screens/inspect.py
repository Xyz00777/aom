"""Inspect TUI screen for AOM.

Readonly mode for browsing sessions.
See SPECIFICATION.md Section 9 for inspect commands.

TDD: This file contains STUB implementations only. Tests come first.
"""

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static


class InspectScreen(Screen):
    """Readonly inspect TUI for browsing sessions.

    Displays session information in TUI format:
    - Session tree (plays/tasks/hosts)
    - Events list
    - Summary statistics

    Closes on Escape.
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

    def compose(self) -> ComposeResult:
        tree_lines = []
        tree_lines.append("Session Tree")
        tree_lines.append("=" * 30)
        tree_lines.append("")
        tree_lines.append("[dim]No session loaded[/dim]")
        tree_lines.append("")
        tree_lines.append("Use: aom inspect <session-id> --tui")

        info_lines = []
        info_lines.append("Session Summary")
        info_lines.append("=" * 30)
        info_lines.append("")
        info_lines.append("[bold]Statistics[/bold]")
        info_lines.append("-" * 10)
        info_lines.append("  Plays: 0")
        info_lines.append("  Tasks: 0")
        info_lines.append("  Hosts: 0")
        info_lines.append("")
        info_lines.append("[bold]Events[/bold]")
        info_lines.append("-" * 7)
        info_lines.append("  Total: 0")
        info_lines.append("")
        info_lines.append("[dim]Press Escape to close[/dim]")

        yield Static("\n".join(tree_lines), id="session-tree", classes="session-tree")
        yield Static("\n".join(info_lines), id="session-info", classes="session-info")

    async def action_dismiss(self, result: Any | None = None) -> None:
        self.app.pop_screen()
