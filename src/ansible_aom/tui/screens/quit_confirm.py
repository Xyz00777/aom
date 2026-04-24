"""Quit confirmation dialog for AOM TUI.

Triggered by 'q' key when a playbook is running.
See SPECIFICATION.md Section 10 for keybindings.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static


class QuitConfirmScreen(ModalScreen[bool]):
    """Modal dialog confirming quit action.

    Returns:
        True: User confirmed quit
        False: User cancelled
    """

    DEFAULT_CSS = """
    QuitConfirmScreen {
        align: center middle;
    }

    QuitConfirmScreen > Static {
        width: 50;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: solid $error;
    }
    """

    BINDINGS = [
        Binding(key="escape", action="cancel", description="Cancel"),
        Binding(key="y", action="confirm", description="Confirm quit"),
        Binding(key="n", action="cancel", description="Cancel"),
    ]

    def compose(self) -> ComposeResult:
        lines = [
            "[bold red]Quit Confirmation[/bold red]",
            "",
            "A playbook is still running.",
            "Are you sure you want to quit?",
            "",
            "Press [bold]Y[/bold] to quit, [bold]N[/bold] or [bold]Escape[/bold] to cancel",
        ]
        yield Static("\n".join(lines), id="quit-content")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
