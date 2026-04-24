"""Main TUI screen for AOM.

See SPECIFICATION.md Section 4.2 for layout.

TDD: This file contains STUB implementations only. Tests come first.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen

from ansible_aom.tui.keybindings import KEYBINDINGS, KeyContext
from ansible_aom.tui.widgets import LogPanel, StatusBar, SummaryPanel, TaskTree


class MainScreen(Screen):
    """Main TUI screen with tree, summary, and log panels.

    Layout (from SPECIFICATION.md Section 4.2):
    - Header: Status bar (top, configurable)
    - Left panel: Tree view (play/task/host hierarchy)
    - Right panel: Summary (top) + Log panel (bottom)
    - Footer: Help shortcuts
    """

    DEFAULT_CSS = """
    MainScreen {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr 2fr;
        grid-rows: 1fr 1;
    }

    MainScreen > TaskTree {
        column-span: 1;
        row-span: 2;
    }

    MainScreen > SummaryPanel {
        column-span: 1;
        row-span: 1;
    }

    MainScreen > LogPanel {
        column-span: 1;
        row-span: 1;
    }

    MainScreen > StatusBar {
        column-span: 2;
        row-span: 1;
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding(
            key=key,
            action=action_info["action"],
            description=action_info["description"],
        )
        for key, action_info in KEYBINDINGS.items()
        if action_info["context"] == KeyContext.GLOBAL
    ]

    def compose(self) -> ComposeResult:
        yield TaskTree("Plays")
        yield SummaryPanel()
        yield LogPanel()
        yield StatusBar()
