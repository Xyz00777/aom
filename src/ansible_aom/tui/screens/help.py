"""Help overlay for AOM TUI.

Triggered by '?' key.
See SPECIFICATION.md Section 10 for keybindings.

TDD: This file contains STUB implementations only. Tests come first.
"""

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static

from ansible_aom.tui.keybindings import KEYBINDINGS, KeyContext


class HelpOverlay(ModalScreen[None]):
    """Help overlay showing keybindings.

    Displays all keybindings grouped by context (GLOBAL, TREE, LOG, POST_RUN).
    Closes on Escape or '?' key.
    """

    DEFAULT_CSS = """
    HelpOverlay {
        align: center middle;
    }

    HelpOverlay > Static {
        width: 60;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }
    """

    BINDINGS = [
        Binding(key="escape", action="dismiss", description="Close help"),
        Binding(key="question", action="dismiss", description="Close help"),
    ]

    def compose(self) -> ComposeResult:
        lines = []
        lines.append("AOM - Keybindings")
        lines.append("=" * 40)
        lines.append("")

        contexts = [
            (KeyContext.GLOBAL, "Global"),
            (KeyContext.TREE, "Tree Navigation"),
            (KeyContext.LOG, "Log Panel"),
            (KeyContext.POST_RUN, "Post-Run"),
        ]

        for context, label in contexts:
            context_bindings = {
                key: action for key, action in KEYBINDINGS.items() if action["context"] == context
            }

            if context_bindings:
                lines.append(f"[bold]{label}[/bold]")
                lines.append("-" * len(label))

                for key, action in sorted(context_bindings.items()):
                    desc = action["description"]
                    key_display = key.ljust(12)
                    lines.append(f"  {key_display}{desc}")

                lines.append("")

        lines.append("Press [bold]Escape[/bold] or [bold]?[/bold] to close")

        yield Static("\n".join(lines), id="help-content")

    async def action_dismiss(self, result: Any | None = None) -> None:
        self.app.pop_screen()
