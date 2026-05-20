"""Inspect TUI app — three-pane browser for past AOM sessions.

Pane layout:
- Runs (left)   : DataTable, newest-first, date + playbook + duration + status icon.
- Tasks (mid)   : Tree, hierarchical (play → role/group → task → host); failure
                  paths auto-expanded, all-OK groups collapsed by default.
- Detail (right): Static, failure-first body for the focused (task, host) pair.

Keybindings:
  q        quit
  f        toggle failed-only filter in Runs pane
  g        jump to first failure in current run
  R        copy a rerun command for focused (task, host) to clipboard
  y        yank current detail body to clipboard
  Tab      cycle pane focus

Designed so that ``app.run_test()`` (Textual's Pilot harness) can drive
every keybinding and assert against the visible state.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header, Static, Tree

from ansible_aom.core.inspect_model import (
    DetailBlock,
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


class InspectApp(App):
    """Three-pane inspector app."""

    CSS = """
    Horizontal { height: 1fr; }
    #runs-table { width: 32%; }
    #tasks-tree { width: 36%; }
    #detail-pane { width: 1fr; padding: 0 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f", "toggle_failed", "Failed-only"),
        Binding("g", "show_first_failure", "Goto failure"),
        Binding("R", "copy_rerun", "Copy rerun"),
        Binding("y", "yank_detail", "Yank"),
    ]

    def __init__(self, *, state_dir: Path, initial_session_id: str | None = None) -> None:
        super().__init__()
        self.state_dir = state_dir
        self.initial_session_id = initial_session_id
        self.selected_session_id: str | None = None
        self._all_summaries: list = []
        self._failed_only = False
        self._current_session: dict | None = None
        self._current_tree: TaskTreeNode | None = None
        self._focused_task: TaskTreeNode | None = None
        self._focused_host: TaskTreeNode | None = None
        # Mirror of what the detail pane shows. Textual's Static doesn't
        # expose a stable read-back of the content; keeping our own copy
        # is simpler than fishing through internals.
        self._detail_text: str = "Select a task to see details."

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield DataTable(id="runs-table", cursor_type="row")
            yield Tree("Tasks", id="tasks-tree")
            yield Static("Select a run to see details.", id="detail-pane", expand=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#runs-table", DataTable)
        table.add_columns("Date", "Playbook", "Dur", "")
        tree = self.query_one("#tasks-tree", Tree)
        tree.show_root = False
        self._reload_runs()
        # Pre-select initial session (default: latest).
        sid = self.initial_session_id or (
            self._all_summaries[0].session_id if self._all_summaries else None
        )
        if sid:
            self._select_session(sid)
            self._load_tasks_for(sid)

    # ── Runs pane ────────────────────────────────────────────────────────

    def _reload_runs(self) -> None:
        raws = list_sessions(self.state_dir)
        summaries = []
        for raw in raws:
            session = load_session(raw["session_id"], self.state_dir)
            if session is not None:
                summaries.append(build_run_summary(session))
        self._all_summaries = summaries
        self._refresh_table()

    def _visible_summaries(self):
        if self._failed_only:
            return [s for s in self._all_summaries if s.status in ("failed", "crashed")]
        return self._all_summaries

    def _refresh_table(self) -> None:
        table = self.query_one("#runs-table", DataTable)
        table.clear()
        for s in self._visible_summaries():
            date = s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "—"
            dur = _fmt_duration_short(s.duration.total_seconds() if s.duration else None)
            icon = _STATUS_ICON.get(s.status, "?")
            playbook = s.playbook if len(s.playbook) <= 24 else "…" + s.playbook[-23:]
            table.add_row(date, playbook, dur, icon, key=s.session_id)

    def _select_session(self, session_id: str) -> None:
        table = self.query_one("#runs-table", DataTable)
        visible = self._visible_summaries()
        for idx, s in enumerate(visible):
            if s.session_id == session_id:
                try:
                    table.move_cursor(row=idx)
                except Exception:
                    pass
                self.selected_session_id = session_id
                return

    def action_toggle_failed(self) -> None:
        self._failed_only = not self._failed_only
        self._refresh_table()
        # Re-select latest visible run.
        visible = self._visible_summaries()
        if visible:
            self._select_session(visible[0].session_id)
            self._load_tasks_for(visible[0].session_id)

    def on_data_table_row_highlighted(self, event) -> None:
        sid_raw = getattr(event, "row_key", None)
        sid = sid_raw.value if sid_raw is not None and hasattr(sid_raw, "value") else sid_raw
        if isinstance(sid, str) and sid != self.selected_session_id:
            self.selected_session_id = sid
            self._load_tasks_for(sid)

    # ── Tasks pane ───────────────────────────────────────────────────────

    def _should_auto_expand(self, node: TaskTreeNode, depth: int) -> bool:
        if depth == 0:
            return True  # plays always expanded
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
        # Auto-jump to first failure for the detail pane.
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
        detail = self.query_one("#detail-pane", Static)
        if self._current_session is None or self._focused_task is None:
            self._detail_text = "Select a task to see details."
            detail.update(self._detail_text)
            return
        block = build_detail_block(self._current_session, self._focused_task, self._focused_host)
        self._detail_text = self._render_detail_block(block)
        detail.update(self._detail_text)

    def action_show_first_failure(self) -> None:
        if self._current_tree is None:
            return
        pairs = list(self._iter_failures(self._current_tree))
        if not pairs:
            self._focused_task = None
            self._focused_host = None
        else:
            self._focused_task, self._focused_host = pairs[0]
        self._update_detail()

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
