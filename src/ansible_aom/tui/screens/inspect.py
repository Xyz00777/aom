"""Inspect TUI app — three-pane browser for past AOM sessions.

Pane layout (Horizontal, each pane sized 1fr so they scale with terminal
width):
- Runs (left)   : ListView. Each entry spans 3 lines (date+playbook,
                  duration+host count+status, short session_id) with a
                  trailing blank line.
- Tasks (mid)   : Tree, hierarchical (play → role/group → task → host);
                  failure paths auto-expanded, all-OK groups collapsed
                  by default.
- Detail (right): Static, failure-first body for the focused (task, host).

Keybindings:
  q          quit
  Tab / S-Tab cycle pane focus
  f          toggle failed-only filter
  g          jump to first failure in current run
  R          copy rerun command for focused (task, host) to clipboard
  y          yank current detail body to clipboard
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static, Tree

from ansible_aom.core.inspect_model import (
    DetailBlock,
    RunSummary,
    StatusCounts,
    TaskTreeNode,
    build_detail_block,
    build_run_summary,
    build_task_tree,
)
from ansible_aom.core.session import list_sessions, load_session


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


def _copy_to_clipboard(text: str) -> None:
    """Best-effort clipboard copy: try pyperclip, then OSC52, then no-op.

    OSC52 is the lowest-common-denominator fallback that most modern
    terminal emulators (kitty, iTerm, Alacritty, recent xterm, recent
    tmux) support — important for users running ``aom inspect`` over SSH
    where no local clipboard daemon exists.
    """
    try:
        import pyperclip  # type: ignore[import-untyped]

        pyperclip.copy(text)
        return
    except Exception:
        pass
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    sys.stdout.write(f"\033]52;c;{encoded}\a")
    sys.stdout.flush()


def _stats_label(stats: StatusCounts) -> str:
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
    """One-line per-host roll-up: 'caeli 22✓ 1✖, web2 8✓'."""
    if not host_counts:
        return "(no hosts)"
    pieces = [f"{h} {_stats_label(c) or '—'}" for h, c in host_counts.items()]
    return ", ".join(pieces)


def _render_run_lines(summary: RunSummary) -> tuple[str, str, str]:
    """Three lines per run row.

    Designed so each line stays informative even when the column is
    narrow — date is always first, status icon hugs the right.
    """
    date = summary.start_time.strftime("%Y-%m-%d %H:%M") if summary.start_time else "—"
    icon = _STATUS_ICON.get(summary.status, "?")
    dur = _fmt_duration_short(summary.duration.total_seconds() if summary.duration else None)
    playbook = summary.playbook or "(no playbook)"

    line1 = f"{icon} {date}  {playbook}"
    line2 = f"   {dur}  {summary.status}"
    if summary.failed_task_count:
        line2 += f"  {summary.failed_task_count}✖ tasks"
    host_summary = _summarise_hosts(summary.host_counts) if summary.host_counts else ""
    if host_summary:
        line2 += f"  · {host_summary}"
    line3 = f"   id {summary.short_id}"
    return line1, line2, line3


class _RunRow(ListItem):
    """One ListView entry: three label lines + blank spacer for breathing room."""

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
        yield Label(line1, classes="run-line1")
        yield Label(line2, classes="run-line2")
        yield Label(line3, classes="run-line3")


class InspectApp(App):
    """Three-pane inspector app."""

    CSS = """
    Screen { background: transparent; }
    Header, Footer { background: transparent; }

    Horizontal { height: 1fr; }

    /* Equal-weight panes — adapt naturally to terminal width. */
    #runs-pane, #tasks-pane, #detail-pane {
        width: 1fr;
        background: transparent;
    }

    /* Pane separators are subtle borders rather than solid backgrounds
       so the terminal's own background shows through. */
    #runs-pane    { border-right: tall $panel; }
    #tasks-pane   { border-right: tall $panel; }
    #detail-pane  { padding: 0 1; }

    #runs-list { background: transparent; }
    #tasks-tree { background: transparent; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("tab", "focus_next_pane", "Next pane", show=True),
        Binding("shift+tab", "focus_prev_pane", "Prev pane", show=False),
        Binding("f", "toggle_failed", "Failed-only"),
        Binding("g", "show_first_failure", "First failure"),
        Binding("n", "next_failure", "Next failure"),
        Binding("N", "prev_failure", "Prev failure"),
        Binding("R", "copy_rerun", "Copy rerun"),
        Binding("y", "yank_detail", "Yank"),
    ]

    # IDs in tab order. action_focus_next_pane / prev cycles through these.
    _PANE_ORDER: tuple[str, ...] = ("runs-list", "tasks-tree", "detail-pane")

    def __init__(self, *, state_dir: Path, initial_session_id: str | None = None) -> None:
        super().__init__()
        self.state_dir = state_dir
        self.initial_session_id = initial_session_id
        self.selected_session_id: str | None = None
        self._all_summaries: list[RunSummary] = []
        self._failed_only = False
        self._current_session: dict | None = None
        self._current_tree: TaskTreeNode | None = None
        self._focused_task: TaskTreeNode | None = None
        self._focused_host: TaskTreeNode | None = None
        # Mirror of the detail-pane content. Static doesn't expose a
        # stable read-back; the mirror is used by yank and tests.
        self._detail_text: str = "Select a task to see details."

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="runs-pane"):
                yield ListView(id="runs-list")
            with Vertical(id="tasks-pane"):
                yield Tree("Tasks", id="tasks-tree")
            with VerticalScroll(id="detail-pane"):
                yield Static("Select a run to see details.", id="detail-body", expand=True)
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one("#tasks-tree", Tree)
        tree.show_root = False
        self._reload_runs()
        sid = self.initial_session_id or (
            self._all_summaries[0].session_id if self._all_summaries else None
        )
        if sid:
            self._select_session(sid)
            self._load_tasks_for(sid)

    # ── Pane navigation ──────────────────────────────────────────────────

    def _focus_pane(self, offset: int) -> None:
        """Move focus N positions through ``_PANE_ORDER`` (wrapping)."""
        current = self.focused
        # Walk up to find which top-level pane currently holds focus.
        current_idx = -1
        node = current
        while node is not None:
            ident = getattr(node, "id", None)
            if ident in self._PANE_ORDER:
                current_idx = self._PANE_ORDER.index(ident)
                break
            node = getattr(node, "parent", None)
        next_idx = (current_idx + offset) % len(self._PANE_ORDER)
        target_id = self._PANE_ORDER[next_idx]
        try:
            widget = self.query_one(f"#{target_id}")
        except Exception:
            return
        widget.focus()

    def action_focus_next_pane(self) -> None:
        self._focus_pane(+1)

    def action_focus_prev_pane(self) -> None:
        self._focus_pane(-1)

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
        listview = self.query_one("#runs-list", ListView)
        listview.clear()
        for s in self._visible_summaries():
            listview.append(_RunRow(s))

    def _select_session(self, session_id: str) -> None:
        listview = self.query_one("#runs-list", ListView)
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

    def on_list_view_highlighted(self, event) -> None:
        item = event.item
        sid = getattr(item, "session_id", None)
        if sid and sid != self.selected_session_id:
            self.selected_session_id = sid
            self._load_tasks_for(sid)

    # ── Tasks pane ───────────────────────────────────────────────────────

    def _should_auto_expand(self, node: TaskTreeNode, depth: int) -> bool:
        if depth == 0:
            return True
        return node.stats.failed > 0 or node.stats.unreachable > 0

    def _add_node(self, parent, node: TaskTreeNode, *, depth: int) -> None:
        label = f"{node.label}  {_stats_label(node.stats)}".strip()
        is_leaf = not node.children
        if is_leaf:
            parent.add_leaf(label, data=node)
            return
        sub = parent.add(label, data=node)
        if self._should_auto_expand(node, depth):
            sub.expand()
        for child in node.children:
            self._add_node(sub, child, depth=depth + 1)

    def _load_tasks_for(self, session_id: str) -> None:
        session = load_session(session_id, self.state_dir)
        if session is None:
            return
        self._current_session = session
        tree_widget = self.query_one("#tasks-tree", Tree)
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

    # ── Detail pane ──────────────────────────────────────────────────────

    def _render_detail_block(self, block: DetailBlock) -> str:
        lines: list[str] = []
        lines.append(f"TASK   {block.task_name}")
        if block.file_line:
            lines.append(f"FILE   {block.file_line}")
        if block.host:
            lines.append(f"HOST   {block.host}")
        if block.duration is not None:
            lines.append(f"TIME   {_fmt_duration_short(block.duration.total_seconds())}")
        lines.append(f"STATUS {block.status}")
        lines.append("─" * 40)
        if block.msg:
            lines.append(f"msg: {block.msg}")
            lines.append("")
        if block.failed_items:
            total = len(block.failed_items) + len(block.ok_items)
            lines.append(f"Failed items ({len(block.failed_items)} of {total}):")
            for item in block.failed_items:
                lines.append(f"  ✖ {item.label}")
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
            lines.append("stderr:")
            for line in block.module_stderr.splitlines():
                lines.append(f"  {line}")
            lines.append("")
        if block.session_stderr_tail:
            lines.append("─ stderr.log (tail) ─")
            lines.extend(block.session_stderr_tail)
        return "\n".join(lines)

    def _update_detail(self) -> None:
        detail = self.query_one("#detail-body", Static)
        if self._current_session is None or self._focused_task is None:
            self._detail_text = "Select a task to see details."
            detail.update(self._detail_text)
            return
        block = build_detail_block(self._current_session, self._focused_task, self._focused_host)
        self._detail_text = self._render_detail_block(block)
        detail.update(self._detail_text)

    def _failure_pairs(self) -> list[tuple[TaskTreeNode, TaskTreeNode]]:
        if self._current_tree is None:
            return []
        return list(self._iter_failures(self._current_tree))

    def _current_failure_index(self) -> int:
        """Return the index of the focused (task, host) pair in the failure list, or -1."""
        pairs = self._failure_pairs()
        if not pairs or self._focused_task is None or self._focused_host is None:
            return -1
        for idx, (task, host) in enumerate(pairs):
            if task.task_id == self._focused_task.task_id and host.label == self._focused_host.label:
                return idx
        return -1

    def _focus_failure_at(self, index: int) -> None:
        """Move the Detail pane focus to the failure at ``index`` (wrapping)."""
        pairs = self._failure_pairs()
        if not pairs:
            self._focused_task = None
            self._focused_host = None
            self._update_detail()
            return
        idx = index % len(pairs)
        self._focused_task, self._focused_host = pairs[idx]
        self._update_detail()
        # Surface a toast so the user knows where they are when many failures exist.
        if len(pairs) > 1:
            self.notify(f"Failure {idx + 1} of {len(pairs)}")

    def action_show_first_failure(self) -> None:
        self._focus_failure_at(0)

    def action_next_failure(self) -> None:
        pairs = self._failure_pairs()
        if not pairs:
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

    def on_tree_node_highlighted(self, event) -> None:
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

    # ── Clipboard actions ────────────────────────────────────────────────

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
        _copy_to_clipboard(cmd)
        self.notify(f"Copied: {cmd[:60]}…" if len(cmd) > 60 else f"Copied: {cmd}")

    def action_yank_detail(self) -> None:
        _copy_to_clipboard(self._detail_text)
        self.notify("Detail yanked to clipboard")
