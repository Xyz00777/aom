"""Help overlay for AOM TUI.

Triggered by '?' key.
See SPECIFICATION.md Section 10 for keybindings.

Renders a multi-section reference card:
- Keyboard shortcuts (grouped by KeyContext)
- Command reference for the ``aom`` CLI
- Navigation instructions for the panel layout
- Status icons legend

Follows the inspect screen's VerticalScroll + Static pattern so the
overlay scales to long content on small terminals without truncation.
"""

from typing import Any

from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from ansible_aom.tui.keybindings import KEYBINDINGS, KeyContext

_CONTEXT_LABELS: list[tuple[KeyContext, str]] = [
    (KeyContext.GLOBAL, "Global"),
    (KeyContext.TREE, "Tree Navigation"),
    (KeyContext.LOG, "Log Panel"),
    (KeyContext.POST_RUN, "Post-Run"),
]


_NAVIGATION_TEXT = """\
Panel focus
  Tab            move focus to the next panel
  Shift+Tab      move focus to the previous panel

Panel toggles
  1              toggle Status Bar
  2              toggle Tree view
  3              toggle Summary panel
  4              toggle Log panel
  5              toggle Footer

Layout
  Ctrl+Left      shrink left column
  Ctrl+Right     grow left column
  c              toggle compact view (tree + status only)
  l              toggle log panel visibility
"""


_COMMAND_REFERENCE = """\
Run a playbook
  aom <playbook>                       compact view (default)
  aom --tui <playbook>                 full multi-panel TUI
  aom <playbook> -i inv.ini --tags x   any ansible-playbook flag passes through

Inspect past runs
  aom inspect list                     list recorded sessions, newest first
  aom inspect <session-id>             summary of one run
  aom inspect <session-id> --tree      ASCII tree of plays/tasks/hosts
  aom inspect <session-id> --failed    failed tasks only
  aom inspect <session-id> --host web1 events for one host
  aom inspect diff <id1> <id2>         what changed between runs
  aom inspect prune --days 30          delete sessions older than 30 days

Replay past runs
  aom replay <session-id>              replay at original cadence
  aom replay <session-id> --speed 10   10x faster
  aom replay <session-id> --speed 0    as fast as possible
  aom replay latest                    replay the most recent session

Rerun failed hosts
  aom rerun                            rerun latest session's failed hosts
  aom rerun <session-id> --failed      explicit session, failed hosts only
  aom rerun <session-id> --unreachable failed AND unreachable hosts
  aom rerun --changes-only -y          rerun changed hosts, skip prompt

Other
  aom --install-completion {bash,zsh,fish}
                                       print shell completion snippet
  aom --format json <playbook>         machine-readable output for CI
  aom --verbose <playbook>             AOM diagnostics + DEBUG logging
  aom --no-record <playbook>           disable session recording
  aom --hide-state ok,changed <pb>     suppress per-host lines for those states
"""


_ICONS_LEGEND = """\
Status icons
  ok            green   ●     (ASCII *)
  changed       yellow  ◆     (ASCII +)
  failed        red     ✖     (ASCII X)
  unreachable   magenta ⊝     (ASCII !)
  skipped       cyan    ○     (ASCII o)
  running       cyan    ◐     (ASCII @)
  pending       dim     □     (ASCII .)
"""


def _build_shortcuts_section() -> Text:
    """Render the keybindings section as a Rich Text.

    Each context gets a bold header followed by two-column rows
    (key, description) so the user can scan the overlay quickly.
    """
    out = Text()
    for context, label in _CONTEXT_LABELS:
        context_bindings = {
            key: action for key, action in KEYBINDINGS.items() if action["context"] == context
        }
        if not context_bindings:
            continue
        out.append(f"\n{label}\n", style="bold")
        out.append("-" * len(label) + "\n", style="dim")
        for key, action in sorted(context_bindings.items()):
            desc = action["description"]
            out.append(f"  {key:<14}", style="cyan")
            out.append(f"{desc}\n")
        out.append("\n")
    return out


class HelpOverlay(ModalScreen[None]):
    """Help overlay showing keybindings, commands, and navigation.

    Closes on Escape or '?' key. The body uses a VerticalScroll so
    long content stays reachable on small terminals; the Static inside
    is a Rich Group of Panels so sections get visual separation.
    """

    DEFAULT_CSS = """
    HelpOverlay {
        align: center middle;
    }

    HelpOverlay > VerticalScroll {
        width: 78;
        height: auto;
        max-height: 90%;
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
        shortcuts_text = _build_shortcuts_section()
        body = Group(
            Panel(
                shortcuts_text,
                title="[bold]Keyboard shortcuts[/bold]",
                border_style="cyan",
                padding=(0, 1),
            ),
            Panel(
                Text(_NAVIGATION_TEXT, style="default"),
                title="[bold]Navigation[/bold]",
                border_style="green",
                padding=(0, 1),
            ),
            Panel(
                Text(_COMMAND_REFERENCE, style="default"),
                title="[bold]Command reference[/bold]",
                border_style="yellow",
                padding=(0, 1),
            ),
            Panel(
                Text(_ICONS_LEGEND, style="default"),
                title="[bold]Status icons[/bold]",
                border_style="magenta",
                padding=(0, 1),
            ),
            Text(
                "\nPress [bold]Escape[/bold] or [bold]?[/bold] to close.",
                style="dim",
            ),
        )
        with VerticalScroll():
            yield Static(body, id="help-content")

    async def action_dismiss(self, result: Any | None = None) -> None:
        self.app.pop_screen()
