"""Settings screen for AOM TUI.

Triggered by 'S' key.
See SPECIFICATION.md Section 8 for configuration.

TDD: This file contains STUB implementations only. Tests come first.
"""

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static


class SettingsScreen(Screen):
    """Settings screen for configuration.

    Displays current settings from AppConfig.
    Closes on Escape or 'S' key.
    """

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
    }

    SettingsScreen > Static {
        width: 60;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }
    """

    BINDINGS = [
        Binding(key="escape", action="dismiss", description="Close settings"),
        Binding(key="S", action="dismiss", description="Close settings"),
    ]

    def compose(self) -> ComposeResult:
        lines = []
        lines.append("AOM - Settings")
        lines.append("=" * 40)
        lines.append("")
        lines.append("[bold]Configuration[/bold]")
        lines.append("-" * 14)
        lines.append("")
        lines.append("  Status Bar Elements:")
        lines.append("    - playbook_name")
        lines.append("    - elapsed_time")
        lines.append("    - task_progress")
        lines.append("")
        lines.append("  Log Settings:")
        lines.append("    - max_lines: 50000")
        lines.append("")
        lines.append("  [dim]Settings modification is TBD[/dim]")
        lines.append("")
        lines.append("Press [bold]Escape[/bold] or [bold]S[/bold] to close")

        yield Static("\n".join(lines), id="settings-content")

    async def action_dismiss(self, result: Any | None = None) -> None:
        self.app.pop_screen()
