"""Inspect TUI app — three-pane browser for past AOM sessions.

Pane layout (Horizontal, each pane sized 1fr so they scale with terminal
width):

- Runs (left)   : ListView. Each entry spans 3 lines (icon+date+playbook,
                  duration+status+host roll-up, short session_id).
- Tasks (mid)   : Tree, hierarchical (play → role/group → task → host);
                  failure paths auto-expanded, all-OK groups collapsed.
- Detail (right): Scrollable Static, failure-first body for the focused
                  (task, host) pair.

Navigation model — drill in / step back:
  Enter / →   move focus one pane to the right (drill in)
  Esc / ←     move focus one pane to the left (step back)
  Tab / S-Tab alternative cycle (forward / back)

Inside the Tasks tree, Left and Right do the classic file-manager thing:
  ←  collapse the current node, or jump to its parent if already collapsed
  →  expand the current node, or jump to its first child if already expanded

Other shortcuts:
  q   quit
  f   toggle failed-only filter
  g   first failure   n  next failure   N  prev failure
  d   delete focused session (with confirm)
  r   reload runs from disk
  R   copy rerun command for focused task to clipboard
  y   yank Detail body to clipboard
  ?   help overlay
"""

from __future__ import annotations

import shutil
from collections import OrderedDict
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from time import perf_counter
from types import EllipsisType
from typing import Literal

from rich.markup import escape
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.timer import Timer
from textual.widgets import Footer, Header, Label, ListItem, ListView, RichLog, Static, Tree
from textual.widgets._static import VisualType
from textual.worker import Worker, WorkerState

from ansible_aom.core.inspect_model import (
    DetailBlock,
    RunSummary,
    StatusCounts,
    TaskTreeNode,
    build_detail_block,
    build_run_summary,
    build_task_tree,
    build_verbose_lines,
    task_ids_by_play,
    tree_from_index,
)
from ansible_aom.session.index import (
    build_indexes,
    ensure_index,
    events_stat,
    index_is_fresh,
    load_structure,
    load_summary,
    query_verbose,
    read_event,
    sessions_needing_index,
)
from ansible_aom.session.store import list_sessions, load_session, load_session_meta


def _fmt_duration_short(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes, sec = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m{sec:02d}s"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h{mins:02d}m"


def _render_stdout_lines(stdout: str, *, full: bool) -> tuple[list[str], bool]:
    """Render stdout with the Q32 lazy-load guardrail.

    Preview mode caps the body at the first 100 lines and measures that pass
    against the 100ms budget explicitly, instead of letting the RichLog body
    balloon during layout.
    """
    rendered = stdout.splitlines()
    if full or len(rendered) <= _DETAIL_STDOUT_PREVIEW_LINES:
        return [f"  {line}" for line in rendered], False

    started = perf_counter()
    preview: list[str] = []
    for line in rendered[:_DETAIL_STDOUT_PREVIEW_LINES]:
        preview.append(f"  {line}")
        if perf_counter() - started > _DETAIL_RENDER_BUDGET_SECONDS:
            return preview, True
    return preview, len(rendered) > len(preview)


_STATUS_ICON = {
    "completed": "✓",
    "failed": "✖",
    "crashed": "!",
    "running": "⠋",
}

# Rich-markup colour for each per-task status. Used in the Tasks tree
# stats labels and the Runs pane status icon. Picked to match common
# terminal-theme expectations:
#   ok        — green (success)
#   changed   — yellow (touched but not failure)
#   failed    — bold red (high signal)
#   unreachable — bold magenta (something different; not "module fail")
#   skipped   — cyan (informational; deliberately not "muted/dim" so the
#               counts stay visible on transparent terminals)
_STATUS_COLOR = {
    "ok": "green",
    "changed": "yellow",
    "failed": "bold red",
    "unreachable": "bold magenta",
    "skipped": "cyan",
}

_DETAIL_RENDER_BUDGET_SECONDS = 0.1
_DETAIL_STDOUT_PREVIEW_LINES = 100


@dataclass(frozen=True)
class VerboseScope:
    """Selection filter for the verbose panel.

    ``level`` is the user-facing scope label; the remaining fields carry
    the focused run / play / task / host identifiers that task 7.2 will
    use to read and filter the captured verbose stream.
    """

    level: Literal["run", "play", "task"]
    session_id: str
    play_name: str | None = None
    task_id: str | None = None
    task_name: str | None = None
    host: str | None = None


class _FooterStatus(Static):
    """One-line status strip above the Textual footer."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.current_text = str(args[0]) if args else ""

    def update(self, content: VisualType | EllipsisType = ..., *, layout: bool = True) -> None:
        if isinstance(content, EllipsisType):
            super().update("", layout=layout)
            return
        self.current_text = str(content)
        super().update(content, layout=layout)


# Per-run-status colour for the icon column on Runs rows.
_RUN_STATUS_COLOR = {
    "completed": "green",
    "failed": "bold red",
    "crashed": "bold red",
    "running": "cyan",
}


def _copy_to_clipboard(app: App, text: str) -> None:
    """Best-effort clipboard copy from within the running TUI.

    Routes through Textual's :meth:`App.copy_to_clipboard` so the OSC52
    escape is written via Textual's driver. A raw ``sys.stdout`` write
    never reaches the terminal while Textual owns the alternate screen,
    which is why ``y``/``R`` silently failed to copy before.

    Also attempts ``pyperclip`` when it is importable so the host's
    native clipboard is populated on terminals lacking OSC52 support;
    it is an optional extra, so its absence is ignored.
    """
    app.copy_to_clipboard(text)
    try:
        import pyperclip  # type: ignore[import-untyped]
    except ImportError:
        # pyperclip isn't installed (optional extra). OSC52 above
        # already pushed the text to the terminal.
        pass
    else:
        try:
            pyperclip.copy(text)
        except Exception:
            # pyperclip is installed but no usable backend (no xclip/xsel/
            # wl-copy on Linux, no pbcopy in macOS sandbox, etc.). Non-fatal
            # because OSC52 above already pushed the text to the terminal.
            pass


def _stats_label(stats: StatusCounts) -> str:
    """Render a colour-coded stats summary using Rich markup."""
    parts: list[str] = []
    if stats.ok:
        parts.append(f"[{_STATUS_COLOR['ok']}]{stats.ok}✓[/]")
    if stats.changed:
        parts.append(f"[{_STATUS_COLOR['changed']}]{stats.changed}◆[/]")
    if stats.failed:
        parts.append(f"[{_STATUS_COLOR['failed']}]{stats.failed}✖[/]")
    if stats.unreachable:
        parts.append(f"[{_STATUS_COLOR['unreachable']}]{stats.unreachable}⊝[/]")
    if stats.skipped:
        parts.append(f"[{_STATUS_COLOR['skipped']}]{stats.skipped}○[/]")
    return " ".join(parts)


def _stats_label_plain(stats: StatusCounts) -> str:
    """Same as :func:`_stats_label` but without colour markup.

    Used in the Runs-row per-host roll-up where Rich markup would
    interfere with column alignment.
    """
    parts: list[str] = []
    if stats.ok:
        parts.append(f"{stats.ok}✓")
    if stats.changed:
        parts.append(f"{stats.changed}◆")
    if stats.failed:
        parts.append(f"{stats.failed}✖")
    if stats.unreachable:
        parts.append(f"{stats.unreachable}⊝")
    if stats.skipped:
        parts.append(f"{stats.skipped}○")
    return " ".join(parts)


def _summarise_hosts(host_counts) -> str:
    """Colour-coded per-host roll-up using Rich markup."""
    if not host_counts:
        return ""
    pieces = [f"{h} {_stats_label(c) or '—'}" for h, c in host_counts.items()]
    return ", ".join(pieces)


def _render_run_lines(summary: RunSummary) -> tuple[str, str, str]:
    # JSONL ``_timestamp`` is UTC; ``.astimezone()`` (no arg) renders in
    # the local system timezone — which is what the user actually wants
    # to see when scanning recent runs.
    date = summary.start_time.astimezone().strftime("%Y-%m-%d %H:%M") if summary.start_time else "—"
    icon = _STATUS_ICON.get(summary.status, "?")
    icon_color = _RUN_STATUS_COLOR.get(summary.status, "")
    icon_markup = f"[{icon_color}]{icon}[/]" if icon_color else icon
    dur = _fmt_duration_short(summary.duration.total_seconds() if summary.duration else None)
    playbook = summary.playbook or "(no playbook)"

    line1 = f"{icon_markup} {date}  {playbook}"
    status_markup = f"[{icon_color}]{summary.status}[/]" if icon_color else summary.status
    line2 = f"   {dur}  {status_markup}"
    if summary.failed_task_count:
        line2 += f"  [{_STATUS_COLOR['failed']}]{summary.failed_task_count}✖ tasks[/]"
    host_summary = _summarise_hosts(summary.host_counts)
    if host_summary:
        line2 += f"  · {host_summary}"
    line3 = f"   id {summary.short_id}"
    return line1, line2, line3


class _RunRow(ListItem):
    DEFAULT_CSS = """
    _RunRow { padding: 0 1; height: 4; }
    _RunRow > .run-line1 { text-style: bold; }
    _RunRow > .run-line2 { color: $text-muted; }
    _RunRow > .run-line3 { color: $text-disabled; }
    """

    def __init__(self, summary: RunSummary) -> None:
        super().__init__()
        self.summary = summary
        self.session_id = summary.session_id

    def compose(self) -> ComposeResult:
        line1, line2, line3 = _render_run_lines(self.summary)
        # ``markup=True`` is the default for Label; spelt out for clarity.
        yield Label(line1, classes="run-line1", markup=True)
        yield Label(line2, classes="run-line2", markup=True)
        yield Label(line3, classes="run-line3", markup=True)

    def update_summary(self, summary: RunSummary) -> None:
        """Refresh the row's labels in place (e.g. after index backfill).

        Rebuilding the whole ListView per hydrated row would reset scroll
        and selection under the user's cursor.
        """
        self.summary = summary
        line1, line2, line3 = _render_run_lines(summary)
        try:
            self.query_one(".run-line1", Label).update(line1)
            self.query_one(".run-line2", Label).update(line2)
            self.query_one(".run-line3", Label).update(line3)
        except NoMatches:
            pass


class _ConfirmDelete(ModalScreen[bool]):
    """Yes/no confirmation for session deletion."""

    DEFAULT_CSS = """
    _ConfirmDelete { align: center middle; }
    _ConfirmDelete > Vertical {
        width: 60; height: 7; padding: 1 2;
        border: thick $error;
        background: $surface;
    }
    _ConfirmDelete .hint { color: $text-muted; }
    """

    BINDINGS = [
        # ``d`` confirms too so a quick ``dd`` (vim-style double-tap)
        # deletes the focused session without leaving the keyboard.
        Binding("y,d", "confirm", "Delete", show=True),
        Binding("n,escape,q", "cancel", "Cancel", show=True),
    ]

    def __init__(self, short_id: str, playbook: str) -> None:
        super().__init__()
        self._short_id = short_id
        self._playbook = playbook

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"Delete session {self._short_id} ({self._playbook})?")
            yield Label("")
            yield Label("y / d to delete · n / Esc to cancel", classes="hint")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


_HELP_TEXT = """\
Navigation
  Enter / →   drill into the next pane (Runs → Tasks → Detail)
  Esc / ←     step back one pane

Inside Tasks tree
  ↑ / ↓       move cursor
  ←           collapse, or jump to parent if already collapsed
  →           expand, or jump to first child if already expanded
  Space       toggle expand / collapse
  e           expand every node in the tree
  c           collapse every node in the tree

Runs filter
  f           toggle failed-only

Verbose
  V           open Verbose for the focused run / play / task
              ↳ Esc returns to the pane you came from

Failures
  g           jump to first failure
  n / N       next / previous failure

Session management
  d           delete focused session (opens confirm modal)
              ↳ y / d to confirm · n / Esc to cancel  (so `dd` deletes)
  r           reload runs from disk

Clipboard
  R           copy rerun command to clipboard
  y           yank Detail to clipboard

Detail
  L           load the full Detail body after lazy previewing

Other
  ?           this help
  q           quit
"""


class _HelpScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    _HelpScreen { align: center middle; }
    _HelpScreen > VerticalScroll {
        width: 70; height: 80%; padding: 1 2;
        border: thick $accent;
        background: $surface;
    }
    """

    BINDINGS = [Binding("escape,q,question_mark", "dismiss", "Close", show=True)]

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(_HELP_TEXT, expand=True)


class _RunsListView(ListView):
    """ListView that treats Right / Enter as "drill into Tasks pane"."""

    BINDINGS = ListView.BINDINGS + [
        Binding("right", "drill_in", "Drill in", show=False),
    ]

    def action_drill_in(self) -> None:
        app = self.app
        if isinstance(app, InspectApp):
            app.focus_tasks()


class _DetailLog(RichLog):
    """RichLog used as the Detail pane.

    Replaces an earlier ``VerticalScroll`` containing a ``Static`` whose
    body was the whole detail text. ``Static`` stores its content as a
    single ``Content`` object whose ``get_height`` wraps the entire body
    on every layout-triggering refresh — an O(N) cost that visibly froze
    the UI for seconds on failed tasks with tens of thousands of stderr
    lines. ``RichLog`` stores each line as a pre-rendered ``Strip`` so
    scrolling stays O(visible) and updates are O(lines written).

    Left / Escape step back to the Tasks pane, matching the
    drill-in / step-back navigation model used by the other panes.
    """

    BINDINGS = RichLog.BINDINGS + [
        Binding("left", "step_back", "Back", show=False),
        Binding("escape", "step_back", "Back", show=False),
    ]

    def action_step_back(self) -> None:
        app = self.app
        if isinstance(app, InspectApp):
            app.focus_previous_pane()


class _NavTree(Tree):
    """Tree that adds Left / Right bindings for hierarchical navigation.

    Default Textual ``Tree`` reserves Shift+Left/Right for parent / sibling
    navigation; the plain arrow keys aren't bound. We add:

    * ``Right``: if the cursor is on a collapsed branch, expand it; if it's
      already expanded, move to its first child; if it's a leaf and the
      Tree's host is an ``InspectApp``, hand off to the Detail pane.
    * ``Left``: if expanded → collapse; if already collapsed → jump to
      parent. On a top-level node with no parent → hand back to Runs.

    Falling out of the tree at the edges is a convenience: it makes the
    same arrow keys do the right thing without requiring users to learn
    a separate "leave pane" shortcut.

    ``BINDINGS`` is concatenated with ``Tree.BINDINGS`` rather than
    replacing them — the parent class binds Enter / Space / arrows that
    we still want.
    """

    BINDINGS = Tree.BINDINGS + [
        Binding("right", "deeper", "Expand / drill", show=False),
        Binding("left", "shallower", "Collapse / back", show=False),
        # Bulk expand / collapse the whole tree.
        Binding("e", "expand_all", "Expand all", show=True),
        Binding("c", "collapse_all", "Collapse all", show=True),
    ]

    def action_expand_all(self) -> None:
        """Expand every node in the tree (root downward)."""
        for child in self.root.children:
            child.expand_all()

    def action_collapse_all(self) -> None:
        """Collapse every node in the tree, then keep top-level plays visible.

        Fully collapsing would hide everything except play headers. That's
        usually what the user wants — a one-line-per-play overview — so
        we leave plays themselves at the cursor's reach but collapse all
        their descendants.
        """
        for child in self.root.children:
            child.collapse_all()
            child.collapse()

    def action_deeper(self) -> None:
        node = self.cursor_node
        if node is None:
            return
        if node.allow_expand:
            if not node.is_expanded:
                node.expand()
                return
            # Already expanded — move cursor to first child if any.
            # ``move_cursor`` (not ``select_node``) so we don't fire a
            # ``NodeSelected`` message that would be interpreted by the
            # App's Enter-handler as "drill into Detail" and steal focus.
            if node.children:
                self.move_cursor(node.children[0])
                return
        # Leaf (or expanded with no children) — hand off to Detail pane.
        app = self.app
        if isinstance(app, InspectApp):
            app.focus_detail()

    def action_shallower(self) -> None:
        node = self.cursor_node
        if node is None:
            return
        if node.allow_expand and node.is_expanded:
            node.collapse()
            return
        parent = node.parent
        # Walk past the (hidden) root: any node whose parent is the
        # tree's root is "top-level"; collapsing/parent-jumping further
        # should leave the pane.
        if parent is None or parent is self.root:
            app = self.app
            if isinstance(app, InspectApp):
                app.focus_runs()
            return
        # ``move_cursor`` rather than ``select_node`` — see action_deeper.
        # Without this, walking up to a parent would post NodeSelected,
        # which the App's Enter-handler routes to ``focus_detail()``,
        # making Left arrow appear to jump to the Detail pane.
        self.move_cursor(parent)


class InspectApp(App):
    """Three-pane inspector app."""

    CSS = """
    Screen { background: ansi_default; }
    Header, Footer { background: ansi_default; }

    #footer-bar {
        dock: bottom;
        height: 2;
        background: ansi_default;
    }
    #focus-footer {
        height: 1;
        background: ansi_default;
        color: $text;
        text-wrap: nowrap;
    }

    Horizontal { height: 1fr; }

    /* Equal-weight panes — adapt naturally to terminal width.
       Each pane has a one-cell top border that switches colour when the
       pane holds focus, so "which pane am I in" is unmissable. */
    #runs-pane, #tasks-pane, #detail-pane {
        width: 1fr;
        background: ansi_default;
        border-top: tall $panel;
    }
    #runs-pane.--focused-pane,
    #tasks-pane.--focused-pane,
    #detail-pane.--focused-pane {
        border-top: tall $accent;
    }

    /* Subtle separators between panes — narrower than the focus border. */
    #runs-pane    { border-right: tall $panel; }
    #tasks-pane   { border-right: tall $panel; }
    #detail-pane  { padding: 0 1; }

    #runs-list, #tasks-tree, #detail-pane { background: ansi_default; }
    _RunRow { background: ansi_default; }

    /* Selected/highlighted rows — bright enough to be readable on a
       transparent terminal background. */
    ListView > ListItem.-highlight {
        background: $accent 30%;
    }
    ListView:focus > ListItem.-highlight {
        background: $accent 60%;
        text-style: bold;
    }
    Tree > .tree--cursor {
        background: $accent 30%;
    }
    Tree:focus > .tree--cursor {
        background: $accent 60%;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        # Textual's default binds ctrl+c to ``help_quit`` (a notification
        # nudging the user toward ctrl+q) because ctrl+c doubles as copy
        # when an Input/TextArea is focused. The inspect view is read-only
        # with no such widgets — copy is on y/R — so honour the reflex and
        # make ctrl+c actually quit. priority beats the focused widget.
        Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
        # Pane navigation
        Binding("tab", "focus_next_pane", "Next pane", show=False),
        Binding("shift+tab", "focus_prev_pane", "Prev pane", show=False),
        # Escape always steps back one pane (modals consume it first
        # via their own bindings, so this only fires at the top level).
        Binding("escape", "focus_prev_pane", "Back", show=True),
        # Filter / failures / help
        Binding("f", "toggle_failed", "Failed-only"),
        Binding("g", "show_first_failure", "First fail"),
        Binding("n", "next_failure", "Next fail"),
        Binding("N", "prev_failure", "Prev fail"),
        Binding("question_mark", "help", "Help"),
        # Session management
        Binding("d", "delete_session", "Delete"),
        Binding("r", "reload_runs", "Reload"),
        # Clipboard
        Binding("R", "copy_rerun", "Rerun"),
        Binding("y", "yank_detail", "Yank"),
        Binding("V", "open_verbose", "Verbose", show=True),
        Binding("L", "load_full_detail", "Load full", show=False),
    ]

    # Delay before loading a newly-highlighted session. Scrolling the Runs
    # list fires a highlight per row; the debounce means only the row the
    # cursor settles on actually loads. Tests set this to 0 for determinism.
    LOAD_DEBOUNCE_SECONDS: float = 0.15
    # Loaded (meta, tree, index_backed) models kept per session. Small on
    # purpose: each entry is O(tasks × hosts).
    _MODEL_CACHE_SIZE = 4

    _PANE_ORDER: tuple[str, ...] = ("runs-pane", "tasks-pane", "detail-pane")
    # Map pane container → focusable widget inside it. ``detail-pane`` is
    # the VerticalScroll itself (its inner Static is not focusable), so
    # focus stays on the scrollable container and PgUp/PgDn just work.
    _PANE_TARGETS: dict[str, str] = {
        "runs-pane": "runs-list",
        "tasks-pane": "tasks-tree",
        "detail-pane": "detail-pane",
    }

    def __init__(self, *, state_dir: Path, initial_session_id: str | None = None) -> None:
        super().__init__(ansi_color=True)
        self.state_dir = state_dir
        self.initial_session_id = initial_session_id
        self.selected_session_id: str | None = None
        self._all_summaries: list[RunSummary] = []
        self._failed_only = False
        self._current_session: dict | None = None
        self._current_tree: TaskTreeNode | None = None
        self._focused_task: TaskTreeNode | None = None
        self._focused_host: TaskTreeNode | None = None
        self._detail_return_pane_id: str | None = None
        self._verbose_scope: VerboseScope | None = None
        self._verbose_flash: str | None = None
        self._verbose_flash_timer: Timer | None = None
        self._detail_text: str = "Select a task to see details."
        self._detail_focus_key: tuple[object, ...] | None = None
        self._detail_force_full = False
        # Index-backed session loading state (see _load_tasks_for). Cache
        # entries: (meta_or_session, tree, index_backed, events_stat_at_load).
        self._model_cache: OrderedDict[
            str, tuple[dict, TaskTreeNode, bool, tuple[int, int] | None]
        ] = OrderedDict()
        self._index_backed = False
        self._load_debounce: Timer | None = None
        self._loading_session_id: str | None = None
        self._loading_note: str | None = None
        # Cache key for the last detail body we rendered: (task_id,
        # host_label, session_id). Re-rendering only when the key changes
        # protects us from the burst of tree-highlight messages Textual
        # fires when the cursor moves over the same node multiple times.
        self._detail_key: tuple[object, ...] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="runs-pane"):
                yield _RunsListView(id="runs-list")
            with Vertical(id="tasks-pane"):
                yield _NavTree("Tasks", id="tasks-tree")
            yield _DetailLog(id="detail-pane", markup=True, wrap=True, auto_scroll=False)
        with Vertical(id="footer-bar"):
            yield _FooterStatus("focus: —", id="focus-footer")
            yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one("#tasks-tree", _NavTree)
        tree.show_root = False
        # ``auto_expand`` toggles a node on every NodeSelected message.
        # We use NodeSelected as the "Enter pressed → drill into Detail"
        # signal, so disable the implicit toggle. Space / Left / Right
        # still expand and collapse explicitly.
        tree.auto_expand = False
        self._reload_runs()
        sid = self.initial_session_id or (
            self._all_summaries[0].session_id if self._all_summaries else None
        )
        if sid:
            self._select_session(sid)
            self._load_tasks_for(sid)
        self._start_index_backfill()
        # Visual focus indicator
        self._refresh_pane_focus_classes()
        self._refresh_footer()

    # ── Pane focus ──────────────────────────────────────────────────────

    def _current_pane(self) -> str | None:
        node = self.focused
        while node is not None:
            ident = getattr(node, "id", None)
            if isinstance(ident, str) and ident in self._PANE_ORDER:
                return ident
            parent = getattr(node, "parent", None)
            # Some widget hierarchies expose ``.parent`` as a property;
            # if it's the same node, bail to avoid an infinite loop.
            if parent is node:
                return None
            node = parent
        return None

    def _focus_pane_id(self, pane_id: str) -> None:
        target = self._PANE_TARGETS.get(pane_id)
        if not target:
            return
        try:
            widget = self.query_one(f"#{target}")
        except NoMatches:
            return
        widget.focus()
        self._refresh_pane_focus_classes()

    def _refresh_pane_focus_classes(self) -> None:
        current = self._current_pane()
        for pid in self._PANE_ORDER:
            try:
                pane = self.query_one(f"#{pid}")
            except NoMatches:
                continue
            if pid == current:
                pane.add_class("--focused-pane")
            else:
                pane.remove_class("--focused-pane")
        self._refresh_footer()

    def _footer_scope(self) -> VerboseScope | None:
        pane = self._current_pane()
        if pane == "runs-pane":
            if not self.selected_session_id:
                return None
            return VerboseScope(level="run", session_id=self.selected_session_id)
        if pane == "detail-pane" and self._verbose_scope is not None:
            return self._verbose_scope
        if pane != "tasks-pane":
            return None

        try:
            tree = self.query_one("#tasks-tree", _NavTree)
        except NoMatches:
            return None
        cursor = tree.cursor_node
        data = getattr(cursor, "data", None)
        if not isinstance(data, TaskTreeNode):
            return None

        session_id = self.selected_session_id or ""
        if data.kind == "play":
            return VerboseScope(level="play", session_id=session_id, play_name=data.label)
        if data.kind == "group":
            play = self._ancestor_tree_node(cursor, "play")
            return VerboseScope(
                level="play",
                session_id=session_id,
                play_name=play.label if play else None,
            )
        if data.kind not in ("task", "host"):
            return None

        task_node = data if data.kind == "task" else self._ancestor_tree_node(cursor, "task")
        if task_node is None:
            return None
        play = self._ancestor_tree_node(cursor, "play")
        host = (
            data.label
            if data.kind == "host"
            else self._focused_host.label
            if self._focused_host
            else None
        )
        return VerboseScope(
            level="task",
            session_id=session_id,
            play_name=play.label if play else None,
            task_id=task_node.task_id or "",
            task_name=task_node.label,
            host=host,
        )

    def _footer_context(self, scope: VerboseScope) -> str:
        if scope.level == "run":
            return "current session"
        if scope.level == "play":
            return scope.play_name or "(unnamed play)"
        if scope.host and scope.task_name:
            return f"{scope.host} / {scope.task_name}"
        if scope.task_name:
            return scope.task_name
        if scope.host:
            return scope.host
        return "(selected task)"

    def _footer_text(self) -> str:
        scope = self._footer_scope()
        parts = [
            "focus: —" if scope is None else f"focus: {scope.level} ({self._footer_context(scope)})"
        ]
        if self._loading_note is not None:
            parts.append(self._loading_note)
        if self._verbose_flash is not None:
            parts.append(self._verbose_flash)
        return " | ".join(parts)

    def _refresh_footer(self) -> None:
        try:
            footer = self.query_one("#focus-footer", _FooterStatus)
        except NoMatches:
            return
        footer.update(self._footer_text())

    def _clear_verbose_flash(self) -> None:
        self._verbose_flash = None
        self._verbose_flash_timer = None
        self._refresh_footer()

    def _set_verbose_flash(self, scope: VerboseScope) -> None:
        self._verbose_flash = f"V: verbose for {self._footer_context(scope)}"
        if self._verbose_flash_timer is not None:
            self._verbose_flash_timer.stop()
        self._verbose_flash_timer = self.set_timer(1.5, self._clear_verbose_flash)
        self._refresh_footer()

    def on_descendant_focus(self, _event) -> None:  # noqa: ANN001
        self._refresh_pane_focus_classes()

    def focus_runs(self) -> None:
        self._focus_pane_id("runs-pane")

    def focus_tasks(self) -> None:
        # Make sure the tree has a visible cursor before focus lands on
        # it — Tree.action_select_cursor is a no-op when cursor_line < 0,
        # which means Enter would silently do nothing on the very first
        # entry to the pane.
        try:
            tree = self.query_one("#tasks-tree", _NavTree)
        except NoMatches:
            tree = None
        if tree is not None and tree.cursor_line < 0 and tree.root.children:
            tree.cursor_line = 0
        self._focus_pane_id("tasks-pane")

    def focus_detail(self, *, return_to: str | None = "tasks-pane") -> None:
        self._detail_return_pane_id = return_to or "tasks-pane"
        self._focus_pane_id("detail-pane")
        self._update_detail()

    def focus_previous_pane(self) -> None:
        target = self._detail_return_pane_id or "tasks-pane"
        self._detail_return_pane_id = None
        self._verbose_scope = None
        self._focus_pane_id(target)
        self._update_detail()

    def action_focus_next_pane(self) -> None:
        current = self._current_pane() or self._PANE_ORDER[0]
        idx = self._PANE_ORDER.index(current)
        self._focus_pane_id(self._PANE_ORDER[(idx + 1) % len(self._PANE_ORDER)])

    def action_focus_prev_pane(self) -> None:
        current = self._current_pane() or self._PANE_ORDER[0]
        idx = self._PANE_ORDER.index(current)
        self._focus_pane_id(self._PANE_ORDER[(idx - 1) % len(self._PANE_ORDER)])

    def _ancestor_tree_node(self, node, kind: str):  # noqa: ANN001
        current = node
        while current is not None:
            data = getattr(current, "data", None)
            if isinstance(data, TaskTreeNode) and data.kind == kind:
                return data
            current = getattr(current, "parent", None)
        return None

    def _verbose_scope_from_focus(self) -> VerboseScope | None:
        pane = self._current_pane()
        if pane == "runs-pane":
            if not self.selected_session_id:
                return None
            return VerboseScope(level="run", session_id=self.selected_session_id)
        if pane != "tasks-pane":
            return None

        try:
            tree = self.query_one("#tasks-tree", _NavTree)
        except NoMatches:
            return None
        cursor = tree.cursor_node
        data = getattr(cursor, "data", None)
        if not isinstance(data, TaskTreeNode):
            return None

        session_id = self.selected_session_id or ""
        if data.kind == "play":
            return VerboseScope(level="play", session_id=session_id, play_name=data.label)
        if data.kind == "group":
            play = self._ancestor_tree_node(cursor, "play")
            return VerboseScope(
                level="play",
                session_id=session_id,
                play_name=play.label if play else None,
            )
        if data.kind not in ("task", "host"):
            return None

        task_node = data if data.kind == "task" else self._ancestor_tree_node(cursor, "task")
        if task_node is None:
            return None
        play = self._ancestor_tree_node(cursor, "play")
        host = (
            data.label
            if data.kind == "host"
            else self._focused_host.label
            if self._focused_host
            else None
        )
        return VerboseScope(
            level="task",
            session_id=session_id,
            play_name=play.label if play else None,
            task_id=task_node.task_id or "",
            task_name=task_node.label,
            host=host,
        )

    def _render_verbose_placeholder(self, scope: VerboseScope) -> str:
        lines: list[str] = ["[bold]VERBOSE[/]", "─" * 40]
        lines.append(f"SCOPE  {scope.level}")
        session = self._current_session or {}
        if scope.level == "run":
            playbook = session.get("playbook") or "(no playbook)"
            lines.append(f"RUN    {playbook}")
        else:
            if scope.play_name:
                lines.append(f"PLAY   {scope.play_name}")
            if scope.task_name:
                lines.append(f"TASK   {scope.task_name}")
            if scope.host:
                lines.append(f"HOST   {scope.host}")
        lines.append("")
        sid = session.get("session_id")
        if self._index_backed and self._current_tree is not None and sid:
            body = query_verbose(
                self.state_dir / sid,
                tree=self._current_tree,
                level=scope.level,
                play_name=scope.play_name,
                task_id=scope.task_id,
                host=scope.host,
            )
        else:
            body = build_verbose_lines(
                session,
                level=scope.level,
                play_name=scope.play_name,
                task_id=scope.task_id,
                host=scope.host,
                play_task_ids=(
                    task_ids_by_play(self._current_tree) if self._current_tree is not None else None
                ),
            )
        if body:
            lines.extend(body)
        else:
            lines.append("(no verbose lines matched this scope)")
        lines.append("Press Esc to return to the previous pane.")
        return "\n".join(lines)

    # ── Runs pane ────────────────────────────────────────────────────────

    def _reload_runs(self) -> None:
        """Populate the Runs pane WITHOUT touching any events.jsonl.

        Rows come from meta.json; host roll-ups come from the sqlite
        index when one is already fresh. Sessions never opened before
        show a meta-only row and hydrate after their first load — the
        alternative (indexing every session at startup) is exactly the
        many-huge-runs stall this replaced.
        """
        raws = list_sessions(self.state_dir)
        summaries: list[RunSummary] = []
        for raw in raws:
            sid = raw["session_id"]
            meta = load_session_meta(sid, self.state_dir)
            if meta is None:
                continue
            summary: RunSummary | None = None
            session_path = self.state_dir / sid
            if index_is_fresh(session_path):
                summary = load_summary(session_path, meta)
            if summary is None:
                # build_run_summary on a meta-only dict (no "events" key)
                # yields the placeholder: correct times/status, empty
                # host roll-up.
                summary = build_run_summary(meta)
            summaries.append(summary)
        self._all_summaries = summaries
        self._refresh_list()

    def _visible_summaries(self) -> list[RunSummary]:
        if self._failed_only:
            return [s for s in self._all_summaries if s.status in ("failed", "crashed")]
        return self._all_summaries

    def _refresh_list(self) -> None:
        listview = self.query_one("#runs-list", _RunsListView)
        listview.clear()
        for s in self._visible_summaries():
            listview.append(_RunRow(s))

    def _select_session(self, session_id: str) -> None:
        listview = self.query_one("#runs-list", _RunsListView)
        for idx, s in enumerate(self._visible_summaries()):
            if s.session_id == session_id:
                try:
                    listview.index = idx
                except ValueError, IndexError:
                    # ValueError/IndexError: ListView.index assignment
                    # validates against the current child count; a
                    # concurrent reload between enumerate() and the
                    # assignment can land out-of-range. Skip — the
                    # follow-up _load_tasks_for still wires the data.
                    pass
                self.selected_session_id = session_id
                return

    def action_toggle_failed(self) -> None:
        self._failed_only = not self._failed_only
        self._refresh_list()
        visible = self._visible_summaries()
        if visible:
            self._select_session(visible[0].session_id)
            self._load_tasks_for(visible[0].session_id)

    def action_reload_runs(self) -> None:
        self._reload_runs()
        self._start_index_backfill()
        self.notify(f"{len(self._all_summaries)} sessions on disk")

    def on_list_view_highlighted(self, event) -> None:  # noqa: ANN001
        item = event.item
        sid = getattr(item, "session_id", None)
        if not sid:
            return
        # Drop events that arrive after a refresh / delete — the queued
        # message can carry a reference to a row that no longer exists
        # in the model. Without this filter, deleting a session causes a
        # stale highlight event to immediately re-select the just-removed
        # row.
        if not any(s.session_id == sid for s in self._all_summaries):
            return
        if sid != self.selected_session_id:
            self.selected_session_id = sid
            self._schedule_load(sid)

    def on_list_view_selected(self, _event) -> None:  # noqa: ANN001
        """Enter on a Runs row → drill into the Tasks pane."""
        self.focus_tasks()

    # ── Tasks pane ───────────────────────────────────────────────────────

    def _should_auto_expand(self, node: TaskTreeNode, depth: int) -> bool:
        if depth == 0:
            return True
        return node.stats.failed > 0 or node.stats.unreachable > 0

    def _add_node(self, parent, node: TaskTreeNode, *, depth: int) -> None:
        # ``Tree.add`` / ``add_leaf`` treat a plain string as literal text;
        # passing a ``rich.Text`` parses the embedded markup so the stats
        # icons show in their per-status colour.
        label_text = Text.from_markup(f"{node.label}  {_stats_label(node.stats)}".strip())
        is_leaf = not node.children
        if is_leaf:
            parent.add_leaf(label_text, data=node)
            return
        sub = parent.add(label_text, data=node)
        for child in node.children:
            self._add_node(sub, child, depth=depth + 1)
        # Expand after children exist — Textual's ``expand()`` is a no-op
        # on a node with no children yet (it doesn't carry the "should be
        # expanded once children arrive" intent forward).
        if self._should_auto_expand(node, depth):
            sub.expand()

    def _schedule_load(self, session_id: str) -> None:
        """Debounced entry point for Runs-list scrolling."""
        if self._load_debounce is not None:
            self._load_debounce.stop()
            self._load_debounce = None
        if self.LOAD_DEBOUNCE_SECONDS <= 0 or session_id in self._model_cache:
            self._load_tasks_for(session_id)
            return
        self._load_debounce = self.set_timer(
            self.LOAD_DEBOUNCE_SECONDS, partial(self._load_tasks_for, session_id)
        )

    def _cache_entry_fresh(
        self, session_id: str, entry: tuple[dict, TaskTreeNode, bool, tuple[int, int] | None]
    ) -> bool:
        """A cached model is reusable while the log it was built from is
        unchanged. Index-backed entries defer to the index freshness
        check; fallback entries (un-indexable sessions) compare the
        events.jsonl stat captured at load time — otherwise every
        re-selection would re-parse the full log."""
        _, _, index_backed, stat_at_load = entry
        session_path = self.state_dir / session_id
        if index_backed:
            return index_is_fresh(session_path)
        return events_stat(session_path) == stat_at_load

    def _load_tasks_for(self, session_id: str) -> None:
        self._loading_session_id = session_id
        cached = self._model_cache.get(session_id)
        if cached is not None and self._cache_entry_fresh(session_id, cached):
            self._model_cache.move_to_end(session_id)
            meta_or_session, tree, index_backed, _ = cached
            self._apply_session_model(session_id, meta_or_session, tree, index_backed)
            return
        # Slow path: index build (first open of a legacy session can
        # stream hundreds of MB) or db read + tree assembly. Runs in a
        # thread worker so the UI keeps painting; exclusive group means
        # a newer selection cancels a stale in-flight load.
        tree_widget = self.query_one("#tasks-tree", _NavTree)
        tree_widget.clear()
        self._loading_note = f"loading {session_id[:8]}…"
        self._refresh_footer()
        self.run_worker(
            partial(self._load_model_blocking, session_id),
            thread=True,
            exclusive=True,
            group="session-load",
        )

    def _load_model_blocking(
        self, session_id: str
    ) -> tuple[str, dict, TaskTreeNode, bool, tuple[int, int] | None] | None:
        """Worker body — no widget access allowed here (thread)."""
        session_path = self.state_dir / session_id
        # Stat BEFORE parsing (same reasoning as build_index): a log that
        # grows during the load makes the cache entry read as stale.
        stat = events_stat(session_path)
        meta = load_session_meta(session_id, self.state_dir)
        if meta is None:
            return None
        if ensure_index(session_path):
            index = load_structure(session_path)
            if index is not None:
                tree = tree_from_index(index, playbook=str(meta.get("playbook", "")))
                return (session_id, meta, tree, True, stat)
        # No index possible (no events.jsonl, unreadable db): legacy
        # full-parse fallback.
        session = load_session(session_id, self.state_dir)
        if session is None:
            return None
        return (session_id, session, build_task_tree(session), False, stat)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if getattr(event.worker, "group", None) != "session-load":
            return
        if event.state in (WorkerState.ERROR, WorkerState.CANCELLED):
            self._loading_note = None
            self._refresh_footer()
            return
        if event.state is not WorkerState.SUCCESS:
            return
        result = event.worker.result
        if not result:
            # Session vanished mid-load (deleted / pruned): nothing to
            # show, but don't leave the footer stuck on "loading …".
            self._loading_note = None
            self._refresh_footer()
            return
        session_id, session_meta, tree, index_backed, stat = result
        if session_id != self._loading_session_id:
            return  # superseded by a newer selection while loading
        self._model_cache[session_id] = (session_meta, tree, index_backed, stat)
        self._model_cache.move_to_end(session_id)
        while len(self._model_cache) > self._MODEL_CACHE_SIZE:
            self._model_cache.popitem(last=False)
        self._apply_session_model(session_id, session_meta, tree, index_backed)

    def _apply_session_model(
        self, session_id: str, session_meta: dict, tree: TaskTreeNode, index_backed: bool
    ) -> None:
        self._current_session = session_meta
        self._index_backed = index_backed
        self._current_tree = tree
        self._loading_note = None
        tree_widget = self.query_one("#tasks-tree", _NavTree)
        tree_widget.clear()
        for play in tree.children:
            self._add_node(tree_widget.root, play, depth=0)
        self._refresh_run_summary(session_id, session_meta)
        self.action_show_first_failure()
        self._refresh_footer()

    def _refresh_run_summary(self, session_id: str, meta: dict) -> None:
        """Hydrate a meta-only Runs row once its session has been indexed."""
        del meta  # re-read inside _hydrate_run_row; kept for signature clarity
        if not self._index_backed:
            return
        self._hydrate_run_row(session_id)

    def _hydrate_run_row(self, session_id: str) -> None:
        """Swap a placeholder Runs row for real index-derived counts."""
        for i, summary in enumerate(self._all_summaries):
            if summary.session_id != session_id:
                continue
            if summary.host_counts:
                return  # already showing real counts
            meta = load_session_meta(session_id, self.state_dir)
            if meta is None:
                return
            hydrated = load_summary(self.state_dir / session_id, meta)
            if hydrated is None:
                return
            self._all_summaries[i] = hydrated
            for row in self.query(_RunRow):
                if row.session_id == session_id:
                    row.update_summary(hydrated)
                    break
            return

    # ── Background index backfill ───────────────────────────────────────

    def _start_index_backfill(self) -> None:
        """Index sessions that lack a fresh index, in the background.

        Runs once at mount (and again on ``r``). Large backlogs fan out
        over a process pool inside the worker thread — json parsing is
        CPU-bound, so this is the one place the GIL would otherwise
        serialise hours of old logs.
        """
        self.run_worker(
            self._backfill_indexes_blocking,
            thread=True,
            exclusive=True,
            group="index-backfill",
        )

    def _backfill_indexes_blocking(self) -> None:
        """Worker body — no widget access allowed here (thread)."""
        paths = [
            path
            for path in sessions_needing_index(self.state_dir)
            # The selected session is being indexed by its own load worker.
            if path.name != self._loading_session_id
        ]
        for path, ok in build_indexes(paths):
            if ok:
                self.call_from_thread(self._hydrate_run_row, path.name)

    def _iter_failures(self, node: TaskTreeNode):
        if node.kind == "task":
            for child in node.children:
                if child.kind == "host" and (child.stats.failed or child.stats.unreachable):
                    yield node, child
                elif child.kind == "task":
                    # Nested include_tasks children: recurse so failures
                    # inside an included file still surface.
                    yield from self._iter_failures(child)
        else:
            for child in node.children:
                yield from self._iter_failures(child)

    def on_tree_node_highlighted(self, event) -> None:  # noqa: ANN001
        data = getattr(event.node, "data", None)
        if not isinstance(data, TaskTreeNode):
            return
        if data.kind == "host":
            self._focused_host = data
            parent_widget = event.node.parent
            if parent_widget is not None and isinstance(
                getattr(parent_widget, "data", None), TaskTreeNode
            ):
                self._focused_task = parent_widget.data
        elif data.kind == "task":
            self._focused_task = data
            # A task's children may now include nested include_tasks rows,
            # so pick the first *host* child rather than children[0].
            self._focused_host = next((c for c in data.children if c.kind == "host"), None)
        else:
            self._focused_task = None
            self._focused_host = None
        self._update_detail()
        self._refresh_footer()

    def on_tree_node_selected(self, _event) -> None:  # noqa: ANN001
        """Enter on a Task node → drill into the Detail pane."""
        self.focus_detail()

    # ── Detail pane ──────────────────────────────────────────────────────

    def _hydrate_node(self, node: TaskTreeNode) -> TaskTreeNode:
        """Resolve an index-built node's byte ref into the event dict.

        Trees loaded from the sqlite index carry EventRefs instead of
        event payloads; the detail pane needs the dict, so seek the one
        line out of events.jsonl on focus. A failed read (log pruned or
        rewritten) degrades to a payload-less detail block.
        """
        if node.raw_event is not None or node.raw_ref is None:
            return node
        sid = (self._current_session or {}).get("session_id")
        if not sid:
            return node
        event = read_event(self.state_dir / sid, node.raw_ref)
        if event is None:
            return node
        return node._replace(raw_event=event)

    def _render_detail_block(self, block: DetailBlock, *, full_stdout: bool = False) -> str:
        """Render the per-task detail body.

        Everything here is specific to the focused (task, host) pair —
        session-wide stderr from ``aom_stderr_line`` events in ``events.jsonl``
        belongs in a separate view, not under each task, because re-rendering
        the same text on every cursor move was confusing.
        """
        status_color = _STATUS_COLOR.get(block.status, "")
        status_markup = f"[{status_color}]{block.status}[/]" if status_color else block.status

        lines: list[str] = []
        lines.append(f"[bold]TASK[/]   {block.task_name}")
        if block.file_line:
            lines.append(f"FILE   {block.file_line}")
        if block.host:
            lines.append(f"HOST   {block.host}")
        if block.action:
            lines.append(f"ACTION {block.action}")
        if block.duration is not None:
            lines.append(f"TIME   {_fmt_duration_short(block.duration.total_seconds())}")
        lines.append(f"STATUS {status_markup}")
        lines.append("─" * 40)

        if block.msg:
            lines.append(f"msg: {block.msg}")
            lines.append("")

        if block.verbose_vars:
            # ``debug: var=thing`` — the value lives under its own key, so
            # without this section the pane had nothing to show at all.
            # Escaped because the pane is rendered with markup=True and a
            # var's value is arbitrary user data ("[bold]" is a plausible
            # string to debug).
            lines.append("[bold]vars[/]")
            for key, value in block.verbose_vars:
                value_lines = value.splitlines() or [""]
                lines.append(f"  {escape(key)}: {escape(value_lines[0])}")
                lines.extend(f"  {escape(cont)}" for cont in value_lines[1:])
            lines.append("")

        if block.failed_items:
            total = len(block.failed_items) + len(block.ok_items)
            failed_color = _STATUS_COLOR["failed"]
            lines.append(f"[{failed_color}]Failed items[/] ({len(block.failed_items)} of {total}):")
            for item in block.failed_items:
                lines.append(f"  [{_STATUS_COLOR['failed']}]✖[/] {item.label}")
                if item.msg:
                    lines.append(f"      {item.msg}")
                if item.stderr:
                    lines.append(f"      stderr: {item.stderr}")
            if block.ok_items:
                lines.append(
                    f"  ({len(block.ok_items)} ok item{'s' if len(block.ok_items) != 1 else ''})"
                )
            lines.append("")

        if block.module_stderr and not block.failed_items:
            lines.append("[bold]stderr[/]")
            for line in block.module_stderr.splitlines():
                lines.append(f"  {line}")
            lines.append("")

        if block.module_stdout:
            lines.append("[bold]stdout[/]")
            stdout_lines, truncated = _render_stdout_lines(block.module_stdout, full=full_stdout)
            lines.extend(stdout_lines)
            if truncated:
                lines.append("")
                lines.append("[dim]press L to load full[/]")
            lines.append("")

        if block.warnings:
            lines.append(f"[{_STATUS_COLOR['changed']}]warnings[/]")
            for w in block.warnings:
                lines.append(f"  ⚠ {w}")
            lines.append("")

        # If we got here with no per-task content beyond the header, give
        # the user a hint rather than a blank pane.
        non_header = (
            block.msg
            or block.verbose_vars
            or block.failed_items
            or block.module_stderr
            or block.module_stdout
            or block.warnings
        )
        if not non_header:
            lines.append("[dim](module returned no message, stdout, or stderr)[/]")

        return "\n".join(lines)

    def _update_detail(self) -> None:
        detail = self.query_one("#detail-pane", _DetailLog)
        if self._verbose_scope is not None:
            verbose_focus_key: tuple[object, ...] = ("verbose", self._verbose_scope)
            if verbose_focus_key != self._detail_focus_key:
                self._detail_focus_key = verbose_focus_key
                self._detail_force_full = False
            verbose_key: tuple[object, ...] = (
                "verbose",
                self._verbose_scope,
                self._detail_force_full,
            )
            if verbose_key == self._detail_key:
                return
            self._detail_key = verbose_key
            self._detail_text = self._render_verbose_placeholder(self._verbose_scope)
            detail.clear()
            detail.write(self._detail_text)
            detail.scroll_home(animate=False)
            return
        # Skip the rebuild when the focused (task, host) pair has not
        # actually changed. Tree highlight messages fire for every cursor
        # tick — including ones that select the same node we're already
        # showing — and re-rendering a long error log each time was the
        # second half of the stutter the user reported.
        detail_focus_key: tuple[object, ...] = (
            "detail",
            None if self._focused_task is None else self._focused_task.task_id,
            None if self._focused_host is None else self._focused_host.label,
            None if self._current_session is None else self._current_session.get("session_id"),
        )
        if detail_focus_key != self._detail_focus_key:
            self._detail_focus_key = detail_focus_key
            self._detail_force_full = False
        detail_key: tuple[object, ...] = (*detail_focus_key, self._detail_force_full)
        if detail_key == self._detail_key:
            return
        self._detail_key = detail_key

        detail.clear()
        if self._current_session is None or self._focused_task is None:
            self._detail_text = "Select a task to see details."
            detail.write(self._detail_text)
            return
        block = build_detail_block(
            self._current_session,
            self._hydrate_node(self._focused_task),
            None if self._focused_host is None else self._hydrate_node(self._focused_host),
        )
        self._detail_text = self._render_detail_block(block, full_stdout=self._detail_force_full)
        # One write, not one per line: each write does its own measure +
        # console.render + virtual-size update, so per-line writes add a
        # ~100 µs overhead that becomes seconds on long stderr. The body
        # already contains literal newlines — RichLog will split them
        # into per-line Strips itself.
        detail.write(self._detail_text)
        detail.scroll_home(animate=False)

    # ── Failures navigation ─────────────────────────────────────────────

    def _failure_pairs(self) -> list[tuple[TaskTreeNode, TaskTreeNode]]:
        if self._current_tree is None:
            return []
        return list(self._iter_failures(self._current_tree))

    def _current_failure_index(self) -> int:
        pairs = self._failure_pairs()
        if not pairs or self._focused_task is None or self._focused_host is None:
            return -1
        for idx, (task, host) in enumerate(pairs):
            if (
                task.task_id == self._focused_task.task_id
                and host.label == self._focused_host.label
            ):
                return idx
        return -1

    def _focus_failure_at(self, index: int) -> None:
        pairs = self._failure_pairs()
        if not pairs:
            self._focused_task = None
            self._focused_host = None
            self._update_detail()
            return
        idx = index % len(pairs)
        self._focused_task, self._focused_host = pairs[idx]
        self._update_detail()
        if len(pairs) > 1:
            self.notify(f"Failure {idx + 1} of {len(pairs)}")

    def action_show_first_failure(self) -> None:
        self._focus_failure_at(0)

    def action_next_failure(self) -> None:
        if not self._failure_pairs():
            self.notify("No failures in this run")
            return
        current = self._current_failure_index()
        self._focus_failure_at(current + 1 if current >= 0 else 0)

    def action_prev_failure(self) -> None:
        pairs = self._failure_pairs()
        if not pairs:
            self.notify("No failures in this run")
            return
        current = self._current_failure_index()
        self._focus_failure_at(current - 1 if current >= 0 else len(pairs) - 1)

    # ── Session management ─────────────────────────────────────────────

    def action_delete_session(self) -> None:
        if not self.selected_session_id:
            self.notify("No session selected")
            return
        # Find the summary for the confirm modal label.
        summary = next(
            (s for s in self._all_summaries if s.session_id == self.selected_session_id),
            None,
        )
        if summary is None:
            return
        short = summary.short_id
        playbook = summary.playbook or "(no playbook)"

        # Capture the deleted session's position BEFORE the modal so the
        # closure can pick the next sibling regardless of what happens
        # to the visible list while the modal is up.
        old_index = next(
            (
                i
                for i, s in enumerate(self._visible_summaries())
                if s.session_id == self.selected_session_id
            ),
            0,
        )

        def _after_confirm(confirmed: bool | None) -> None:
            if not confirmed:
                return
            sid = self.selected_session_id
            if not sid:
                return
            # A pending debounce timer would re-load the session we are
            # about to delete.
            if self._load_debounce is not None:
                self._load_debounce.stop()
                self._load_debounce = None
            target = self.state_dir / sid
            try:
                if target.is_dir():
                    shutil.rmtree(target)
            except OSError as exc:
                self.notify(f"Delete failed: {exc}", severity="error")
                return
            self.notify(f"Deleted {short}")
            self._model_cache.pop(sid, None)
            self._reload_runs()
            visible = self._visible_summaries()
            if visible:
                next_sid = visible[min(old_index, len(visible) - 1)].session_id
                self._select_session(next_sid)
                self._load_tasks_for(next_sid)
                self.focus_runs()
            else:
                self.selected_session_id = None
                self._current_session = None
                self._current_tree = None
                self._focused_task = None
                self._focused_host = None
                self.query_one("#tasks-tree", _NavTree).clear()
                self._update_detail()

        self.push_screen(_ConfirmDelete(short, playbook), _after_confirm)

    # ── Clipboard actions ──────────────────────────────────────────────

    def _build_rerun_command(self) -> str:
        session = self._current_session or {}
        host = self._focused_host.label if self._focused_host else ""
        task = self._focused_task.label if self._focused_task else ""
        args = session.get("ansible_args") or []
        parts: list[str] = ["aom rerun"]
        if args:
            parts.append(" ".join(args))
        if host:
            parts.append(f"--limit '{host}'")
        if task:
            parts.append(f"--start-at-task '{task}'")
        return " ".join(parts)

    def action_copy_rerun(self) -> None:
        cmd = self._build_rerun_command()
        _copy_to_clipboard(self.app, cmd)
        self.notify(f"Copied: {cmd[:60]}…" if len(cmd) > 60 else f"Copied: {cmd}")

    def action_yank_detail(self) -> None:
        _copy_to_clipboard(self.app, self._detail_text)
        self.notify("Detail yanked to clipboard")

    def action_open_verbose(self) -> None:
        scope = self._verbose_scope_from_focus()
        if scope is None:
            return
        self._verbose_scope = scope
        self._set_verbose_flash(scope)
        self.focus_detail(return_to=self._current_pane())

    def action_load_full_detail(self) -> None:
        if self._verbose_scope is not None:
            return
        if self._focused_task is None or self._current_session is None:
            return
        self._detail_force_full = True
        self._update_detail()

    def action_help(self) -> None:
        self.push_screen(_HelpScreen())
