"""Re-run dialog for AOM TUI.

Triggered by Shift+R.
See SPECIFICATION.md Section 10 for keybindings.

TDD: This file contains STUB implementations only. Tests come first.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static


class RerunDialog(ModalScreen[bool]):
    """Modal dialog for re-running playbook with modified args.

    Shows confirmation dialog with two options:
    - "Rerun with same args": Returns True
    - "Rerun with modified args": Returns False (caller shows arg editor)

    Return Value:
        - True: Rerun with same arguments
        - False: Rerun with modified arguments (show arg editor)
    """

    DEFAULT_CSS = """
    RerunDialog {
        align: center middle;
    }

    RerunDialog > Static {
        width: 50;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }

    RerunDialog > Static > Static.title {
        text-align: center;
        text-style: bold;
    }

    RerunDialog > Static > .dialog-content {
        margin-top: 1;
    }

    RerunDialog Button {
        margin: 1 1;
    }

    RerunDialog .button-row {
        layout: horizontal;
        align: center middle;
    }
    """

    BINDINGS = [
        Binding(key="escape", action="cancel", description="Cancel"),
        Binding(key="s", action="same_args", description="Same args"),
        Binding(key="m", action="modified_args", description="Modified args"),
        Binding(key="enter", action="same_args", description="Confirm"),
    ]

    def compose(self) -> ComposeResult:
        lines = []
        lines.append("[bold]Re-run Playbook[/bold]")
        lines.append("")
        lines.append("How would you like to re-run the playbook?")
        lines.append("")
        lines.append("")
        lines.append("Press [bold]S[/bold] for same args, [bold]M[/bold] for modified args")
        lines.append("Press [bold]Escape[/bold] to cancel")

        yield Static("\n".join(lines), id="rerun-content")

    def action_same_args(self) -> None:
        self.dismiss(True)

    def action_modified_args(self) -> None:
        self.dismiss(False)

    async def action_cancel(self) -> None:
        self.app.pop_screen()
