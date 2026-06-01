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
from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Label, ListItem, ListView, RichLog, Static, Tree

from ansible_aom.core.inspect_model import (
    DetailBlock,
    RunSummary,
    StatusCounts,
    TaskTreeNode,
    build_detail_block,
    build_run_summary,
    build_task_tree,
)
from ansible_aom.session.store import list_sessions, load_session


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

        pyperclip.copy(text)
    except Exception:
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
            app.focus_tasks()


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
    ]

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
        self._detail_text: str = "Select a task to see details."
        # Cache key for the last detail body we rendered: (task_id,
        # host_label, session_id). Re-rendering only when the key changes
        # protects us from the burst of tree-highlight messages Textual
        # fires when the cursor moves over the same node multiple times.
        self._detail_key: tuple[object, object, object] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="runs-pane"):
                yield _RunsListView(id="runs-list")
            with Vertical(id="tasks-pane"):
                yield _NavTree("Tasks", id="tasks-tree")
            yield _DetailLog(id="detail-pane", markup=True, wrap=True, auto_scroll=False)
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
        # Visual focus indicator
        self._refresh_pane_focus_classes()

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
        except Exception:
            return
        widget.focus()
        self._refresh_pane_focus_classes()

    def _refresh_pane_focus_classes(self) -> None:
        current = self._current_pane()
        for pid in self._PANE_ORDER:
            try:
                pane = self.query_one(f"#{pid}")
            except Exception:
                continue
            if pid == current:
                pane.add_class("--focused-pane")
            else:
                pane.remove_class("--focused-pane")

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
        except Exception:
            tree = None
        if tree is not None and tree.cursor_line < 0 and tree.root.children:
            tree.cursor_line = 0
        self._focus_pane_id("tasks-pane")

    def focus_detail(self) -> None:
        self._focus_pane_id("detail-pane")

    def action_focus_next_pane(self) -> None:
        current = self._current_pane() or self._PANE_ORDER[0]
        idx = self._PANE_ORDER.index(current)
        self._focus_pane_id(self._PANE_ORDER[(idx + 1) % len(self._PANE_ORDER)])

    def action_focus_prev_pane(self) -> None:
        current = self._current_pane() or self._PANE_ORDER[0]
        idx = self._PANE_ORDER.index(current)
        self._focus_pane_id(self._PANE_ORDER[(idx - 1) % len(self._PANE_ORDER)])

    # ── Runs pane ────────────────────────────────────────────────────────

    def _reload_runs(self) -> None:
        raws = list_sessions(self.state_dir)
        summaries: list[RunSummary] = []
        for raw in raws:
            session = load_session(raw["session_id"], self.state_dir)
            if session is not None:
                summaries.append(build_run_summary(session))
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
                except Exception:
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
            self._load_tasks_for(sid)

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

    def _load_tasks_for(self, session_id: str) -> None:
        session = load_session(session_id, self.state_dir)
        if session is None:
            return
        self._current_session = session
        tree_widget = self.query_one("#tasks-tree", _NavTree)
        tree_widget.clear()
        model = build_task_tree(session)
        self._current_tree = model
        for play in model.children:
            self._add_node(tree_widget.root, play, depth=0)
        self.action_show_first_failure()

    def _iter_failures(self, node: TaskTreeNode):
        if node.kind == "task":
            for child in node.children:
                if child.kind == "host" and (child.stats.failed or child.stats.unreachable):
                    yield node, child
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
            self._focused_host = data.children[0] if data.children else None
        else:
            self._focused_task = None
            self._focused_host = None
        self._update_detail()

    def on_tree_node_selected(self, _event) -> None:  # noqa: ANN001
        """Enter on a Task node → drill into the Detail pane."""
        self.focus_detail()

    # ── Detail pane ──────────────────────────────────────────────────────

    def _render_detail_block(self, block: DetailBlock) -> str:
        """Render the per-task detail body.

        Everything here is specific to the focused (task, host) pair —
        session-wide content (the session ``stderr.log``) belongs in a
        separate view, not under each task, because re-rendering the same
        text on every cursor move was confusing.
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

        if block.failed_items:
            total = len(block.failed_items) + len(block.ok_items)
            lines.append(
                f"[{_STATUS_COLOR['failed']}]Failed items[/] ({len(block.failed_items)} of {total}):"
            )
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
            for line in block.module_stdout.splitlines():
                lines.append(f"  {line}")
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
        # Skip the rebuild when the focused (task, host) pair has not
        # actually changed. Tree highlight messages fire for every cursor
        # tick — including ones that select the same node we're already
        # showing — and re-rendering a long error log each time was the
        # second half of the stutter the user reported.
        key = (
            None if self._focused_task is None else self._focused_task.task_id,
            None if self._focused_host is None else self._focused_host.label,
            None if self._current_session is None else self._current_session.get("session_id"),
        )
        if key == self._detail_key:
            return
        self._detail_key = key

        detail.clear()
        if self._current_session is None or self._focused_task is None:
            self._detail_text = "Select a task to see details."
            detail.write(self._detail_text)
            return
        block = build_detail_block(self._current_session, self._focused_task, self._focused_host)
        self._detail_text = self._render_detail_block(block)
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
            target = self.state_dir / sid
            try:
                if target.is_dir():
                    shutil.rmtree(target)
            except OSError as exc:
                self.notify(f"Delete failed: {exc}", severity="error")
                return
            self.notify(f"Deleted {short}")
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

    def action_help(self) -> None:
        self.push_screen(_HelpScreen())
