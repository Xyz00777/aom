"""Main TUI screen for AOM.

See SPECIFICATION.md Section 4.2 for layout.
"""

from datetime import datetime, timedelta

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen

from ansible_aom.core.models import RunState
from ansible_aom.core.tree import TreeProjection
from ansible_aom.tui.keybindings import KEYBINDINGS, KeyContext
from ansible_aom.tui.widgets import DebugPanel, LogPanel, StatusBar, SummaryPanel, TaskTree


class MainScreen(Screen):
    """Main TUI screen with tree, summary, and log panels.

    Layout (from SPECIFICATION.md Section 4.2):
    - Header: Status bar (top, configurable)
    - Left panel: Tree view (play/task/host hierarchy)
    - Right panel: Summary (top) + Log panel (bottom)
    - Footer: Help shortcuts
    """

    _projection: TreeProjection | None = None

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

    def update_from_state(self, run_state: RunState) -> None:
        """Update all widgets from RunState.

        Idempotent: safe to call on every UI tick. The tree is rebuilt
        from the projection each call so completed tasks/plays are
        dropped automatically.
        """
        try:
            summary = self.query_one(SummaryPanel)
            status = self.query_one(StatusBar)
            tree = self.query_one(TaskTree)
        except Exception:
            # Screen not fully mounted yet; the next tick will retry.
            return

        current_play_name = ""
        hosts_total = 0
        tasks_completed = 0
        tasks_total = 0

        completed_statuses = ("ok", "changed", "failed", "skipped", "unreachable")
        host_statuses: dict[str, str] = {}

        for play in run_state.plays.values():
            if play.status.value == "running":
                current_play_name = play.name
            for task in play.tasks.values():
                tasks_total += 1
                if task.status.value in completed_statuses:
                    tasks_completed += 1
                for hostname, host_state in task.hosts.items():
                    host_statuses[hostname] = host_state.status.value

        hosts_completed = sum(1 for s in host_statuses.values() if s in completed_statuses)

        if run_state.definitions:
            for play_def in run_state.definitions:
                hosts_total = len(play_def.resolved_hosts)
                break

        summary.set_play_name(current_play_name)
        summary.set_hosts_progress(hosts_completed, hosts_total)
        summary.set_tasks_progress(tasks_completed, tasks_total)
        status.set_task_progress(tasks_completed, tasks_total)
        status.set_host_count(hosts_completed, hosts_total)
        status.set_playbook_name(run_state.playbook)

        # Tree handling: two-mode refresh.
        # When the projection is visible (during a run), rebuild from
        # projection every call — this drops completed tasks/plays so
        # the tree only shows running and pending items.
        # When the projection is NOT visible (before tasks arrive, or
        # after end_time is set), fall back to the original two-step
        # behaviour: skeleton built once from definitions, icons mutated
        # every call via apply_state_icons. This preserves final status
        # icons after completion — populate_from_definitions alone would
        # reset all icons to PENDING.
        if self._projection is None or self._projection._state is not run_state:
            self._projection = TreeProjection.from_run_state(run_state)
        raw_height = tree.size.height
        budget = max(8, min(60, raw_height if raw_height > 0 else 20))
        if self._projection.is_tree_visible():
            tree.populate_from_projection(self._projection, budget=budget)
        else:
            if run_state.definitions and not list(tree.root.children):
                tree.populate_from_definitions(run_state.definitions)
            if run_state.plays:
                tree.apply_state_icons(run_state)

        if run_state.start_time:
            try:
                self._update_elapsed_from_start(run_state.start_time)
            except TypeError:
                # naive/aware datetime mismatch on legacy fixtures; the
                # tree/summary updates above are the load-bearing path
                # and must not be blocked by a clock-format quirk.
                pass

        # Force a refresh — Textual reactives only fire on assignment,
        # but we mutated node labels imperatively above.
        summary.refresh()
        status.refresh()
        tree.refresh()

    def _update_elapsed_from_start(self, start_time: datetime) -> None:
        """Update elapsed time on both panels from start time."""
        elapsed = datetime.now() - start_time
        seconds = int(elapsed.total_seconds())

        summary = self.query_one(SummaryPanel)
        status = self.query_one(StatusBar)

        summary.set_elapsed_time(seconds)
        status.set_elapsed_time(start_time)

    def update_play_name(self, name: str) -> None:
        """Update play name on SummaryPanel and playbook name on StatusBar."""
        summary = self.query_one(SummaryPanel)
        status = self.query_one(StatusBar)

        summary.set_play_name(name)
        status.set_playbook_name(name)

    def update_hosts_progress(self, completed: int, total: int) -> None:
        """Update hosts progress on SummaryPanel and StatusBar."""
        summary = self.query_one(SummaryPanel)
        status = self.query_one(StatusBar)

        summary.set_hosts_progress(completed, total)
        status.set_host_count(completed, total)

    def update_tasks_progress(self, completed: int, total: int) -> None:
        """Update tasks progress on SummaryPanel and StatusBar."""
        summary = self.query_one(SummaryPanel)
        status = self.query_one(StatusBar)

        summary.set_tasks_progress(completed, total)
        status.set_task_progress(completed, total)

    def update_elapsed(self, seconds: int) -> None:
        """Update elapsed time on SummaryPanel and StatusBar."""
        summary = self.query_one(SummaryPanel)
        status = self.query_one(StatusBar)

        summary.set_elapsed_time(seconds)
        start_time = datetime.now() - timedelta(seconds=seconds)
        status.set_elapsed_time(start_time)

    def update_log_line(self, line: str) -> None:
        """Write a line to the LogPanel."""
        log = self.query_one(LogPanel)
        log.write_line(line)

    def update_debug_from_summary(self, summary: dict) -> None:
        """Update DebugPanel from debug summary dict."""
        debug = self.query_one(DebugPanel)

        if "command" in summary:
            debug.set_command(str(summary["command"]))
        if "env_overrides" in summary:
            env = summary["env_overrides"]
            if isinstance(env, dict):
                debug.set_env_overrides({k: str(v) for k, v in env.items()})
        if "event_count" in summary:
            debug.set_event_count(int(summary["event_count"]))
        if "parsing_errors" in summary:
            errors = summary["parsing_errors"]
            if isinstance(errors, list):
                debug.set_parsing_errors([str(e) for e in errors])
        if "callback_status" in summary:
            debug.set_callback_status(str(summary["callback_status"]))
        if "timing_stats" in summary:
            stats = summary["timing_stats"]
            if isinstance(stats, dict):
                debug.set_timing_stats({k: float(v) for k, v in stats.items()})
        if "subprocess_pid" in summary:
            pid = summary["subprocess_pid"]
            debug.set_subprocess_pid(int(pid) if pid is not None else None)
        if "state_tree" in summary:
            tree = summary["state_tree"]
            if isinstance(tree, dict):
                debug.set_state_tree({k: int(v) for k, v in tree.items()})
        if "pending_events" in summary:
            debug.set_pending_events(int(summary["pending_events"]))
        if "memory_usage" in summary:
            mem = summary["memory_usage"]
            if isinstance(mem, tuple) and len(mem) == 2:
                debug.set_memory_usage(float(mem[0]), float(mem[1]))
        if "renderer_fps" in summary:
            debug.set_renderer_fps(float(summary["renderer_fps"]))
        if "event_latency" in summary:
            debug.set_event_latency(float(summary["event_latency"]))
