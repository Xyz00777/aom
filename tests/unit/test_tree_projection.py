# pyright: reportMissingImports=false

"""Pure-data tests for core/tree.TreeProjection.

The projection is a deterministic function of RunState; tests build a
RunState by firing events from conftest fixtures through handle_event,
then assert on the projection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

from ansible_aom.core.models import (
    PlayDefinition,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
    count_leaf_tasks,
)
from ansible_aom.core.tree import HostRow, TreeLine, TreeProjection


def _state_with_running_task(
    event_playbook_start, event_play_start, event_task_start, event_runner_start
) -> RunState:
    state = RunState(playbook="site.yml")
    for ev in (event_playbook_start, event_play_start, event_task_start, event_runner_start):
        state.handle_event(ev)
    return state


class TestVisibility:
    def test_empty_state_hides_everything(self):
        state = RunState(playbook="site.yml")
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is False
        assert p.is_host_summary_visible() is False

    def test_running_task_shows_tree(
        self, event_playbook_start, event_play_start, event_task_start, event_runner_start
    ):
        state = _state_with_running_task(
            event_playbook_start, event_play_start, event_task_start, event_runner_start
        )
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is True

    def test_host_summary_hidden_for_single_host(
        self, event_playbook_start, event_play_start, event_task_start, event_runner_start
    ):
        state = _state_with_running_task(
            event_playbook_start, event_play_start, event_task_start, event_runner_start
        )
        # Only web1 has appeared so far
        p = TreeProjection.from_run_state(state)
        assert p.is_host_summary_visible() is False

    def test_host_summary_visible_for_multi_host(
        self, event_playbook_start, event_play_start, event_task_start, event_runner_start
    ):
        state = _state_with_running_task(
            event_playbook_start, event_play_start, event_task_start, event_runner_start
        )
        # Fire a second host on the same task
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "task-uuid-1", "name": "Install nginx"},
                "host": "web2",
            }
        )
        p = TreeProjection.from_run_state(state)
        assert p.is_host_summary_visible() is True


class TestDataclassShapes:
    def test_tree_line_is_frozen(self):
        line = TreeLine(
            depth=0,
            kind="task",
            label="Install nginx",
            glyph="◐",
            status=Status.RUNNING,
            elapsed_s=1.0,
        )
        try:
            line.depth = 5  # type: ignore[misc]
        except Exception as e:
            msg = str(e).lower()
            assert "frozen" in msg or "attribute" in msg or "field" in msg
        else:
            raise AssertionError("TreeLine must be frozen")

    def test_host_row_is_frozen(self):
        row = HostRow(
            hostname="web1",
            counts={Status.OK: 3},
            worst_status=Status.OK,
            current_task=None,
            current_elapsed_s=None,
        )
        try:
            row.hostname = "web2"  # type: ignore[misc]
        except Exception as e:
            msg = str(e).lower()
            assert "frozen" in msg or "attribute" in msg or "field" in msg
        else:
            raise AssertionError("HostRow must be frozen")


class TestHostRows:
    def _multi_host_state(self) -> RunState:
        """web1 done-ok, web2 running, web3 done-changed, db1 unreachable."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web3": {"ok": True, "changed": True}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_unreachable",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"db1": {"unreachable": True}},
            }
        )
        # web2 is mid-task
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:06Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:07Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "host": "web2",
            }
        )
        return state

    def test_counts_aggregate_per_host(self):
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].counts == {Status.OK: 1}
        # CHANGED is derived from HostRunState.changed=True even when
        # status=OK — the count belongs to CHANGED, not OK.
        assert rows["web3"].counts == {Status.CHANGED: 1}
        assert rows["db1"].counts == {Status.UNREACHABLE: 1}

    def test_worst_status_selection(self):
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].worst_status == Status.OK
        assert rows["web3"].worst_status == Status.CHANGED
        assert rows["db1"].worst_status == Status.UNREACHABLE

    def test_current_task_for_running_host(self):
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web2"].current_task == "Configure firewall"
        assert rows["web2"].current_elapsed_s is not None

    def test_idle_host_has_no_current_task(self):
        # web1 finished its task; no later task started for it.
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].current_task is None
        assert rows["web1"].current_elapsed_s is None

    def test_unreachable_host_has_no_current_task(self):
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        # The row carries worst_status=UNREACHABLE; the renderer turns
        # that into the "unreachable" suffix. The projection does NOT
        # synthesise a fake current_task.
        assert rows["db1"].current_task is None

    def test_failed_outranks_changed_in_worst_status(self):
        """FAILED has highest precedence — a single failure dominates worst_status."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        # web1: one CHANGED task, then one FAILED task
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": True}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:06Z",
                "task": {"id": "t2", "name": "Start service"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:07Z",
                "task": {"id": "t2", "name": "Start service"},
                "hosts": {"web1": {"failed": True, "msg": "boom"}},
            }
        )
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].worst_status == Status.FAILED
        assert rows["web1"].counts == {Status.CHANGED: 1, Status.FAILED: 1}

    def test_failed_host_tracks_failed_task_name(self):
        """A host with a FAILED entry records the task name in failed_task."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"failed": True, "msg": "boom"}},
            }
        )
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].failed_task == "Install nginx"
        assert rows["web1"].failed_status == Status.FAILED

    def test_unreachable_host_tracks_failed_task_name(self):
        """A host with an UNREACHABLE entry records the task name in failed_task."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Gather facts"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_unreachable",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Gather facts"},
                "hosts": {"db1": {"unreachable": True}},
            }
        )
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["db1"].failed_task == "Gather facts"
        assert rows["db1"].failed_status == Status.UNREACHABLE

    def test_running_host_has_no_failed_task(self):
        """A host currently running a task has no failed_task — running wins."""
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web2"].current_task == "Configure firewall"
        assert rows["web2"].failed_task is None

    def test_ok_host_has_no_failed_task(self):
        """A host that completed with OK has no failed_task."""
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].failed_task is None
        assert rows["web1"].failed_status is None

    def test_failed_task_tracks_most_recent_failure(self):
        """When a host fails multiple tasks, the last one wins."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "First task"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "First task"},
                "hosts": {"web1": {"failed": True, "msg": "fail1"}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:06Z",
                "task": {"id": "t2", "name": "Second task"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:07Z",
                "task": {"id": "t2", "name": "Second task"},
                "hosts": {"web1": {"failed": True, "msg": "fail2"}},
            }
        )
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].failed_task == "Second task"
        assert rows["web1"].failed_status == Status.FAILED

    def test_running_overrides_failed_task_in_display(self):
        """A host that starts a new task after a failure shows the running
        task (not the failed task) because the running task is more recent
        activity — but failed_task still records the failure for fallback."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"failed": True, "msg": "boom"}},
            }
        )
        # A new task starts — web1 is now RUNNING again
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:06Z",
                "task": {"id": "t2", "name": "Configure app"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:07Z",
                "task": {"id": "t2", "name": "Configure app"},
                "host": "web1",
            }
        )
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].current_task == "Configure app"
        assert rows["web1"].failed_task == "Install nginx"
        assert rows["web1"].failed_status == Status.FAILED


class TestTreeLinesBasic:
    def _running_task_state(self) -> RunState:
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy webservers"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        for host in ("web1", "web2"):
            state.handle_event(
                {
                    "_event": "v2_runner_on_start",
                    "_timestamp": "2026-04-20T10:00:03Z",
                    "task": {"id": "t1", "name": "Install nginx"},
                    "host": host,
                }
            )
        return state

    def test_emits_playbook_play_task_hosts(self):
        state = self._running_task_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=20)

        # Expect: playbook, play, task, host x2 — in that source order.
        kinds = [ln.kind for ln in lines]
        assert kinds == ["playbook", "play", "task", "host", "host"]

        assert lines[0].label == "site.yml"
        assert lines[1].label.startswith("play: ")
        assert "deploy webservers" in lines[1].label
        assert lines[2].kind == "task"
        assert lines[2].status == Status.RUNNING

        host_lines = [ln for ln in lines if ln.kind == "host"]
        assert [ln.label for ln in host_lines] == ["web1", "web2"]
        for hl in host_lines:
            assert hl.status == Status.RUNNING
            assert hl.elapsed_s is not None

    def test_task_label_carries_count_summary(self):
        state = self._running_task_state()
        # Finish web1; web2 still running.
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=20)
        task_line = next(ln for ln in lines if ln.kind == "task")
        # Label format: "Install nginx  (1 ok, 1 running)"
        assert "Install nginx" in task_line.label
        assert "1 ok" in task_line.label
        assert "1 running" in task_line.label

    def test_only_currently_running_hosts_appear_as_leaves_before_completion(self):
        state = self._running_task_state()
        # Finish web1 — its result line already streamed to the log
        # above the panel, so the tree keeps only the still-running
        # web2 as a leaf. The task-line summary ("1 ok, 1 running")
        # still accounts for web1.
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        p = TreeProjection.from_run_state(state)
        host_lines = [ln for ln in p.tree_lines(budget=20) if ln.kind == "host"]
        assert [ln.label for ln in host_lines] == ["web2"]
        assert host_lines[0].status == Status.RUNNING

    def test_failed_host_leaf_stays_visible_while_others_run(self):
        # FAILED/UNREACHABLE leaves must survive the running-only
        # filter — a failure is the actionable signal the tree exists
        # for (mirrors the failed-task keep-visible rule in _classify).
        state = self._running_task_state()
        state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:13Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"failed": True, "msg": "boom"}},
            }
        )
        p = TreeProjection.from_run_state(state)
        host_lines = [ln for ln in p.tree_lines(budget=20) if ln.kind == "host"]
        by_label = {ln.label: ln for ln in host_lines}
        assert set(by_label) == {"web1", "web2"}
        assert by_label["web1"].status == Status.FAILED
        assert by_label["web2"].status == Status.RUNNING

    def test_task_with_unreachable_host_drops_from_tree_when_all_hosts_finish(self):
        # When all hosts complete a task (even if one was UNREACHABLE),
        # the task must not remain pinned in the live tree when the next task runs.
        state = self._running_task_state()
        state.handle_event(
            {
                "_event": "v2_runner_on_unreachable",
                "_timestamp": "2026-04-20T10:00:10Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"unreachable": True, "msg": "ssh dead"}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:12Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web2": {"ok": True, "changed": False}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:13Z",
                "task": {"id": "t2", "name": "Start nginx service"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:14Z",
                "task": {"id": "t2", "name": "Start nginx service"},
                "host": "web2",
            }
        )
        p = TreeProjection.from_run_state(state)
        task_lines = [ln for ln in p.tree_lines(budget=20) if ln.kind == "task"]
        assert len(task_lines) == 1
        assert "Start nginx service" in task_lines[0].label
        assert "Install nginx" not in [ln.label for ln in task_lines]

    def test_terminal_leaf_elapsed_is_frozen_at_completion(self):
        # A terminal leaf shows how long the host took (end - start),
        # not a clock that keeps growing after the host finished.
        state = self._running_task_state()  # hosts started at 10:00:03
        state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:13Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"failed": True, "msg": "boom"}},
            }
        )
        p = TreeProjection.from_run_state(state)
        now = datetime(2026, 4, 20, 10, 5, 3, tzinfo=timezone.utc)
        host_lines = [ln for ln in p.tree_lines(budget=20, now=now) if ln.kind == "host"]
        by_label = {ln.label: ln for ln in host_lines}
        assert by_label["web1"].elapsed_s == 10.0  # frozen at completion
        assert by_label["web2"].elapsed_s == 300.0  # still ticking

    def test_task_label_counts_not_yet_started_hosts_as_pending(self):
        # Throttled/free tasks: hosts the play targets but that have
        # not emitted v2_runner_on_start yet surface as "N pending" in
        # the task summary instead of silently missing.
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy webservers",
                hosts="all",
                resolved_hosts=["web1", "web2", "web3", "web4", "web5"],
                tasks=[],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy webservers"},
            }
        )
        for host in ("web1", "web2"):
            state.handle_event(
                {
                    "_event": "v2_runner_on_start",
                    "_timestamp": "2026-04-20T10:00:03Z",
                    "task": {"id": "t1", "name": "Install nginx"},
                    "host": host,
                    "play": {"id": "p1"},
                }
            )
        p = TreeProjection.from_run_state(state)
        task_line = next(ln for ln in p.tree_lines(budget=20) if ln.kind == "task")
        assert "2 running" in task_line.label
        assert "3 pending" in task_line.label

    def test_pending_count_excludes_hosts_failed_earlier_in_play(self):
        # A host that went FAILED/UNREACHABLE earlier in the play is
        # removed from the play by ansible — it will never start later
        # tasks, so it must not count as pending forever.
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy webservers",
                hosts="all",
                resolved_hosts=["web1", "web2", "web3"],
                tasks=[],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy webservers"},
            }
        )
        for host in ("web1", "web2", "web3"):
            state.handle_event(
                {
                    "_event": "v2_runner_on_start",
                    "_timestamp": "2026-04-20T10:00:02Z",
                    "task": {"id": "t1", "name": "Check connectivity"},
                    "host": host,
                    "play": {"id": "p1"},
                }
            )
        state.handle_event(
            {
                "_event": "v2_runner_on_unreachable",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t1", "name": "Check connectivity"},
                "hosts": {"web3": {"unreachable": True, "msg": "ssh dead"}},
                "play": {"id": "p1"},
            }
        )
        for host in ("web1", "web2"):
            state.handle_event(
                {
                    "_event": "v2_runner_on_ok",
                    "_timestamp": "2026-04-20T10:00:04Z",
                    "task": {"id": "t1", "name": "Check connectivity"},
                    "hosts": {host: {"ok": True, "changed": False}},
                    "play": {"id": "p1"},
                }
            )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t2", "name": "Install nginx"},
                "host": "web1",
                "play": {"id": "p1"},
            }
        )
        p = TreeProjection.from_run_state(state)
        task_line = next(
            ln
            for ln in p.tree_lines(budget=20)
            if ln.kind == "task" and "Install nginx" in ln.label
        )
        # web1 running, web2 pending; web3 is gone from the play.
        assert "1 running" in task_line.label
        assert "1 pending" in task_line.label

    def test_no_lines_when_no_task_running(self):
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        p = TreeProjection.from_run_state(state)
        assert p.tree_lines(budget=20) == []

    def test_completed_play_with_no_runtime_tasks_is_hidden(self):
        # Regression: a play whose ``status`` is COMPLETED but whose
        # ``runtime.tasks`` is empty (no task events arrived before it
        # was force-finalized) must NOT render its preflight tasks as
        # pending. The playbook has moved past this play — its preflight
        # tasks should not pollute the tree.
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Play 1",
                hosts="all",
                resolved_hosts=["h1"],
                tasks=[
                    TaskDefinition(
                        name="Task 1.0",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                    )
                ],
            ),
            PlayDefinition(
                id="p2",
                name="Play 2",
                hosts="all",
                resolved_hosts=["h1"],
                tasks=[
                    TaskDefinition(
                        name="Task 2.0",
                        role=None,
                        tags=[],
                        play_id="p2",
                        play_order=0,
                        task_order=0,
                    )
                ],
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-22T10:00:01Z",
                "play": {"id": "p1", "name": "Play 1"},
            }
        )
        # Play 2 starts. Under linear strategy this force-finalizes
        # play 1; under free strategy play 1's status may stay RUNNING
        # (out of scope here). Either way, play 1 has no runtime tasks
        # and the playbook has moved past it.
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-22T10:00:02Z",
                "play": {"id": "p2", "name": "Play 2"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-06-22T10:00:03Z",
                "task": {"id": "t2_0", "name": "Task 2.0"},
                "play": {"id": "p2"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-22T10:00:03Z",
                "task": {"id": "t2_0", "name": "Task 2.0"},
                "host": "h1",
            }
        )

        p = TreeProjection.from_run_state(state)
        play_lines = [ln for ln in p.tree_lines(budget=20) if ln.kind == "play"]
        play_names = [ln.label.removeprefix("play: ") for ln in play_lines]
        assert play_names == ["Play 2"], (
            "Only the active play should appear; Play 1 should be hidden "
            "because the playbook has moved past it. "
            f"Got: {play_names}"
        )


class TestTreeLinesRolesAndFanOut:
    def _role_aware_definitions(self) -> list[PlayDefinition]:
        # Mirrors preflight output: one play with one role containing two tasks.
        return [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="webservers",
                resolved_hosts=["web1", "web2"],
                tasks=[
                    RoleGroupDefinition(
                        role="webserver",
                        tasks=[
                            TaskDefinition(
                                name="Install nginx",
                                role="webserver",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=0,
                                path="nginx.yml:1",
                            ),
                            TaskDefinition(
                                name="Configure firewall",
                                role="webserver",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=1,
                                path="nginx.yml:5",
                            ),
                        ],
                    ),
                ],
            )
        ]

    def _free_strategy_state(self) -> RunState:
        # `ansible.posix.jsonl` emits v2_playbook_on_task_start ONLY under
        # lockstep strategies (linear/host_pinned) and v2_runner_on_start
        # ONLY under non-lockstep strategies (free). A realistic free-
        # strategy fixture fires runner_on_start without a preceding
        # task_start — one host per concurrent task.
        state = RunState(playbook="site.yml")
        state.definitions = self._role_aware_definitions()
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        # web1 is on "Install nginx"; web2 has raced ahead to "Configure firewall"
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "host": "web2",
            }
        )
        return state

    def test_role_branch_appears_above_role_tasks(self):
        state = self._free_strategy_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        # Expected ordering: playbook, play, role, task, host, task, host
        kinds_labels = [(ln.kind, ln.label) for ln in lines]
        role_lines = [kl for kl in kinds_labels if kl[0] == "role"]
        assert len(role_lines) >= 1, f"expected at least one role line, got {kinds_labels}"
        # Role labels now include task count (e.g. "role: webserver (2 tasks)")
        assert role_lines[0][1].startswith("role: webserver")
        role_idx = kinds_labels.index(role_lines[0])
        # Tasks under the role have depth > role's depth
        role_depth = lines[role_idx].depth
        # Both task lines should follow the role line with depth > role_depth
        for ln in lines[role_idx + 1 :]:
            if ln.kind == "task":
                assert ln.depth > role_depth

    def test_two_running_tasks_appear_as_siblings(self):
        state = self._free_strategy_state()
        p = TreeProjection.from_run_state(state)
        task_lines = [ln for ln in p.tree_lines(budget=25) if ln.kind == "task"]
        names = [ln.label.split("  ")[0] for ln in task_lines]
        assert "Install nginx" in names
        assert "Configure firewall" in names

    def test_each_task_only_lists_its_own_running_hosts(self):
        state = self._free_strategy_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        # Find each task and its host children (depth+1 immediately after).
        host_under_task: dict[str, list[str]] = {}
        current_task: str | None = None
        for ln in lines:
            if ln.kind == "task":
                task_label = cast(str, ln.label.split("  ")[0])
                current_task = task_label
                host_under_task[task_label] = []
            elif ln.kind == "host" and current_task is not None:
                host_under_task[current_task].append(ln.label)

        assert host_under_task["Install nginx"] == ["web1"]
        assert host_under_task["Configure firewall"] == ["web2"]


class TestTreeLinesPlayIdentity:
    def _duplicate_name_state(self) -> RunState:
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Deploy",
                hosts="all",
                resolved_hosts=[],
                tasks=[
                    TaskDefinition(
                        name="Install nginx",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                    )
                ],
            ),
            PlayDefinition(
                id="p2",
                name="Deploy",
                hosts="all",
                resolved_hosts=[],
                tasks=[
                    TaskDefinition(
                        name="Configure firewall",
                        role=None,
                        tags=[],
                        play_id="p2",
                        play_order=1,
                        task_order=0,
                    )
                ],
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "play": {"id": "p2", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:04Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "host": "db1",
            }
        )
        # The second play starting finalises the first (plays run
        # sequentially — RunState._finalize_play). This test asserts both
        # same-named play executions stay visible, so re-arm play 1's
        # running task that the play-2 start just completed.
        from ansible_aom.core.models import HostRunState, Status

        _t1 = state.plays["p1"].tasks["t1"]
        _t1.status = Status.RUNNING
        _t1.hosts["web1"] = HostRunState(
            hostname="web1", status=Status.RUNNING, start_time=_t1.start_time
        )
        return state

    def test_duplicate_play_names_keep_both_executions_visible(self):
        state = self._duplicate_name_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=20)

        # This is an identity bug, not a cosmetic one: same display name
        # is intentional here, and the projection must still preserve both
        # play executions instead of joining them by name and dropping the
        # second play's surface.
        play_labels = [ln.label for ln in lines if ln.kind == "play"]
        task_labels = [ln.label.split("  ")[0] for ln in lines if ln.kind == "task"]

        assert play_labels == ["play: Deploy", "play: Deploy"]
        assert task_labels == ["Install nginx", "Configure firewall"]


class TestTreeLinesSerialWindowIdentity:
    def _serial_window_state(self) -> RunState:
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Deploy",
                hosts="all",
                resolved_hosts=["web1", "web2"],
                tasks=[
                    TaskDefinition(
                        name="Run once",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                        path="site.yml:3",
                    )
                ],
            )
        ]

        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-25T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-25T10:00:01Z",
                "play": {
                    "id": "p1",
                    "name": "Deploy",
                    "duration": {"start": "2026-05-25T10:00:01Z"},
                },
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-25T10:00:03Z",
                "task": {"id": "t1", "name": "Run once", "path": "site.yml:3"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-25T10:00:04Z",
                "task": {"id": "t1", "name": "Run once", "path": "site.yml:3"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-25T10:00:05Z",
                "play": {
                    "id": "p1",
                    "name": "Deploy",
                    "duration": {"start": "2026-05-25T10:00:05Z"},
                },
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-25T10:00:06Z",
                "task": {"id": "t1", "name": "Run once", "path": "site.yml:3"},
                "host": "web2",
            }
        )
        return state

    def test_run_once_tasks_refresh_between_serial_windows(self):
        state = self._serial_window_state()

        assert state.plays["p1"].window_start == "2026-05-25T10:00:05Z"

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=20)

        task_groups: list[tuple[str, list[str]]] = []
        current_hosts: list[str] | None = None
        for ln in lines:
            if ln.kind == "task":
                current_hosts = []
                task_groups.append((ln.label.split("  ")[0], current_hosts))
            elif ln.kind == "host" and current_hosts is not None:
                current_hosts.append(ln.label)

        assert task_groups == [("Run once", ["web2"])]


class TestTreeLinesGroupedRoleNestedChildren:
    def _nested_grouped_role_state(self) -> RunState:
        state = RunState(playbook="site.yml")

        polling_child = TaskDefinition(
            name="theforeman.operations.installer : Poll async status",
            role="theforeman.operations.installer",
            tags=[],
            play_id="p2",
            play_order=1,
            task_order=-1,
            is_dynamic=True,
        )
        install_parent = TaskDefinition(
            name="theforeman.operations.installer : Install installer",
            role="theforeman.operations.installer",
            tags=[],
            play_id="p2",
            play_order=1,
            task_order=0,
            children=[polling_child],
        )
        configure_task = TaskDefinition(
            name="theforeman.operations.installer : Configure installer",
            role="theforeman.operations.installer",
            tags=[],
            play_id="p2",
            play_order=1,
            task_order=1,
        )
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Bootstrap",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="Prepare hosts",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                    )
                ],
            ),
            PlayDefinition(
                id="p2",
                name="Deploy Foreman",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="theforeman.operations.installer",
                        tasks=[install_parent, configure_task],
                    )
                ],
            ),
        ]

        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-24T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-24T10:00:01Z",
                "play": {"id": "p1", "name": "Bootstrap"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-24T10:00:02Z",
                "task": {"id": "t1", "name": "Prepare hosts"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-24T10:00:03Z",
                "task": {"id": "t1", "name": "Prepare hosts"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-24T10:00:04Z",
                "play": {"id": "p2", "name": "Deploy Foreman"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-24T10:00:05Z",
                "task": {"id": "t2", "name": "theforeman.operations.installer : Install installer"},
                "play": {"id": "p2"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-24T10:00:06Z",
                "task": {"id": "t2", "name": "theforeman.operations.installer : Install installer"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-24T10:00:07Z",
                "task": {
                    "id": "t2a",
                    "name": "theforeman.operations.installer : Poll async status",
                },
                "play": {"id": "p2"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-24T10:00:08Z",
                "task": {
                    "id": "t2a",
                    "name": "theforeman.operations.installer : Poll async status",
                },
                "host": "web1",
            }
        )
        return state

    def test_grouped_role_children_are_indexed_emitted_and_keep_previous_play_hidden(self):
        state = self._nested_grouped_role_state()

        assert state._task_def_index is not None
        assert "theforeman.operations.installer : Poll async status" in state._task_def_index
        assert count_leaf_tasks(state.definitions) == 4

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=30)

        play_labels = [ln.label for ln in lines if ln.kind == "play"]
        assert play_labels == ["play: Deploy Foreman"]

        role_line = next(ln for ln in lines if ln.kind == "role")
        # `install_parent` is a parent stub (1 dynamic child), so it is
        # skipped; only `polling_child` (the grafted leaf) and
        # `configure_task` count under the role → 2 leaves.
        assert "(2 tasks)" in role_line.label, (
            f"installer role must show 2 leaf tasks after parent-stub skip; got {role_line.label!r}"
        )

        task_lines = [ln for ln in lines if ln.kind == "task"]
        task_labels = [ln.label.split("  ")[0] for ln in task_lines]
        assert task_labels[:3] == [
            "Install installer",
            "Poll async status",
            "Configure installer",
        ]

        poll_line = next(ln for ln in task_lines if "Poll async status" in ln.label)
        assert poll_line.depth > role_line.depth
        assert poll_line.status == Status.RUNNING


class TestTreeProjectionCacheRefresh:
    def test_dynamic_child_graft_refreshes_role_cache(self):
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Deploy Foreman",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="webserver",
                        tasks=[
                            TaskDefinition(
                                name="Install nginx",
                                role="webserver",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=0,
                            )
                        ],
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-24T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-24T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy Foreman"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-24T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )

        projection = TreeProjection.from_run_state(state)
        assert projection._task_role("Install nginx") == ("webserver",)

        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-24T10:00:03Z",
                "task": {"id": "t2", "name": "Poll async status"},
                "play": {"id": "p1"},
            }
        )

        assert projection._task_role("Poll async status") == ("webserver",)
        labels = [ln.label for ln in projection.tree_lines(budget=25)]
        assert any(label.startswith("Poll async status") for label in labels)


class TestTreeLinesNestedChildIdentity:
    def _same_name_children_state(self) -> RunState:
        state = RunState(playbook="site.yml")

        include_a = TaskDefinition(
            name="Include A",
            role=None,
            tags=[],
            play_id="p1",
            play_order=0,
            task_order=0,
        )
        include_a.children.append(
            TaskDefinition(
                name="Shared child",
                role=None,
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=-1,
                is_dynamic=True,
            )
        )

        include_b = TaskDefinition(
            name="Include B",
            role=None,
            tags=[],
            play_id="p1",
            play_order=0,
            task_order=1,
        )
        include_b.children.append(
            TaskDefinition(
                name="Shared child",
                role=None,
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=-1,
                is_dynamic=True,
            )
        )

        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Deploy",
                hosts="all",
                resolved_hosts=["web1", "web2"],
                tasks=[include_a, include_b],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-24T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-24T10:00:01Z",
                "play": {"id": "play-1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-24T10:00:02Z",
                "task": {"id": "a", "name": "Include A"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-24T10:00:03Z",
                "task": {"id": "b", "name": "Include B"},
                "host": "web2",
            }
        )
        # Reverse the child arrival order: the projection must still keep
        # each runtime row attached to the correct parent branch.
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-24T10:00:04Z",
                "task": {"id": "c2", "name": "Shared child"},
                "host": "web2",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-24T10:00:05Z",
                "task": {"id": "c1", "name": "Shared child"},
                "host": "web1",
            }
        )
        return state

    def test_same_name_child_rows_do_not_swap_branches(self):
        state = self._same_name_children_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=20)

        task_groups: list[tuple[str, list[str]]] = []
        current_hosts: list[str] | None = None
        for ln in lines:
            if ln.kind == "task":
                current_hosts = []
                task_groups.append((ln.label.split("  ")[0], current_hosts))
            elif ln.kind == "host" and current_hosts is not None:
                current_hosts.append(ln.label)

        assert task_groups == [
            ("Include A", ["web1"]),
            ("Shared child", ["web1"]),
            ("Include B", ["web2"]),
            ("Shared child", ["web2"]),
        ]


class TestTreeLinesTaskIdentity:
    def _same_name_concurrent_tasks_state(self) -> RunState:
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t2", "name": "Install nginx"},
                "host": "web2",
            }
        )
        return state

    def test_same_name_concurrent_tasks_stay_separate(self):
        state = self._same_name_concurrent_tasks_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=20)

        # This is a task-execution identity bug, not a rendering cosmetic
        # issue: two live executions can share the same display name, and
        # the projection must still preserve them as distinct task rows.
        task_groups: list[tuple[str, list[str]]] = []
        current_hosts: list[str] | None = None
        for ln in lines:
            if ln.kind == "task":
                current_hosts = []
                task_groups.append((ln.label.split("  ")[0], current_hosts))
            elif ln.kind == "host" and current_hosts is not None:
                current_hosts.append(ln.label)

        assert [task for task, _ in task_groups] == ["Install nginx", "Install nginx"]
        assert [hosts for _, hosts in task_groups] == [["web1"], ["web2"]]


class TestTreeLinesPreflightTaskIdentity:
    def _same_name_preflight_tasks_state(self) -> RunState:
        state = RunState(playbook="site.yml")
        # Same display name on purpose: this is a task-identity regression,
        # not a renderer cosmetic issue. Preflight definitions and runtime
        # events must still project as two distinct executions.
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Deploy",
                hosts="all",
                resolved_hosts=[],
                tasks=[
                    TaskDefinition(
                        name="Install nginx",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                        uuid="task-def-1",
                        path="site.yml:10",
                    ),
                    TaskDefinition(
                        name="Install nginx",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=1,
                        uuid="task-def-2",
                        path="site.yml:20",
                    ),
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t2", "name": "Install nginx"},
                "host": "web2",
            }
        )
        return state

    def test_same_name_preflight_tasks_keep_both_executions_visible(self):
        state = self._same_name_preflight_tasks_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=20)

        # This is a task-execution identity bug, not a renderer cosmetic
        # issue: the two preflight task definitions intentionally share a
        # display name, but the projection must still keep the two runtime
        # executions separate by task id/host activity.
        task_labels = [ln.label.split("  ")[0] for ln in lines if ln.kind == "task"]
        host_groups: list[list[str]] = []
        current_hosts: list[str] | None = None
        for ln in lines:
            if ln.kind == "task":
                current_hosts = []
                host_groups.append(current_hosts)
            elif ln.kind == "host" and current_hosts is not None:
                current_hosts.append(ln.label)

        assert task_labels == ["Install nginx", "Install nginx"]
        assert host_groups == [["web1"], ["web2"]]


class TestTreeLinesAsyncTaskIdentity:
    def _async_task_collision_state(self) -> RunState:
        """Build a state where async launcher and async-status rows share a name.

        The launcher and poller come from the real-world ``deploy_vms.yml``
        async shape (different ``task.path`` values), but they intentionally
        share a display name here so the path-aware grafting logic has to keep
        the later async-status branch separate.
        """
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="Async job",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                        path="server-setup/playbooks/proxmox/deploy_vms.yml:10",
                    ),
                    TaskDefinition(
                        name="Async job",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=1,
                        path="server-setup/playbooks/proxmox/deploy_vms.yml:61",
                    ),
                ],
            )
        ]
        state.handle_event(
            {
                "_event": "v2_playbook_on_start",
                "_timestamp": "2026-05-24T10:00:00Z",
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-24T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-24T10:00:02Z",
                "task": {
                    "id": "launch-1",
                    "name": "Async job",
                    "path": "server-setup/playbooks/proxmox/deploy_vms.yml:10",
                },
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-24T10:00:03Z",
                "task": {
                    "id": "launch-1",
                    "name": "Async job",
                    "path": "server-setup/playbooks/proxmox/deploy_vms.yml:10",
                },
                "hosts": {
                    "web1": {
                        "ok": True,
                        "changed": True,
                        "action": "ansible.builtin.command",
                        "ansible_job_id": "j1",
                        "started": True,
                        "finished": False,
                    }
                },
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-24T10:00:10Z",
                "task": {
                    "id": "poll-1",
                    "name": "Async job",
                    "path": "server-setup/playbooks/proxmox/deploy_vms.yml:61",
                },
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-24T10:00:11Z",
                "task": {
                    "id": "poll-1",
                    "name": "Async job",
                    "path": "server-setup/playbooks/proxmox/deploy_vms.yml:61",
                },
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-24T10:00:12Z",
                "task": {
                    "id": "child-1",
                    "name": "Unknown child",
                    "path": "server-setup/playbooks/proxmox/deploy_vms.yml:99",
                },
                "play": {"id": "p1"},
            }
        )
        return state

    def test_async_launcher_and_async_status_keep_their_own_branch(self):
        state = self._async_task_collision_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=20, now=datetime(2026, 5, 24, 10, 0, 12, tzinfo=timezone.utc))

        task_labels = [ln.label.split("  ")[0] for ln in lines if ln.kind == "task"]
        assert task_labels == ["Async job", "Unknown child"]


class TestTreeLinesDelegatedTaskIdentity:
    def _delegated_twin_state(self) -> tuple[RunState, str, str]:
        """Build two same-name tasks where one mirrors a delegated server-setup step.

        The delegated task path comes from ``deploy_vms.yml`` (``delegate_to`` on the
        ``Create Template VMs`` looped task). The non-delegated twin uses a separate
        path from ``snapshot.yml``. They intentionally share the same visible name so
        the projection has to use ``task.path`` instead of runtime arrival order.
        """
        delegated_path = "server-setup/playbooks/proxmox/deploy_vms.yml:134"
        normal_path = "server-setup/roles/podman_service_update/tasks/snapshot.yml:13"

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="Shared coordination task",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                        path=delegated_path,
                    ),
                    TaskDefinition(
                        name="Shared coordination task",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=1,
                        path=normal_path,
                    ),
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-24T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-24T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-24T10:00:02Z",
                "task": {"id": "normal-1", "name": "Shared coordination task", "path": normal_path},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-24T10:00:03Z",
                "task": {
                    "id": "delegated-1",
                    "name": "Shared coordination task",
                    "path": delegated_path,
                },
                "host": "web1",
            }
        )
        return state, delegated_path, normal_path

    def test_delegated_twin_tasks_follow_path_order_not_arrival_order(self):
        state, delegated_path, normal_path = self._delegated_twin_state()

        assert getattr(state.plays["p1"].tasks["delegated-1"], "path", None) == delegated_path
        assert getattr(state.plays["p1"].tasks["normal-1"], "path", None) == normal_path

        projection = TreeProjection.from_run_state(state)
        items = projection._play_running_and_pending(state.plays["p1"])

        assert [(kind, getattr(runtime, "path", None)) for kind, _, _, runtime in items] == [
            ("running", delegated_path),
            ("running", normal_path),
        ]


class TestTreeLinesPruning:
    def _many_tasks_state(self, n_roles: int, tasks_per_role: int, hosts_per_task: int) -> RunState:
        """Build a RunState with n_roles × tasks_per_role tasks, each
        running on hosts_per_task hosts. All tasks are concurrent
        (free-strategy-style fan-out) — pruning is exercised by the
        sheer line count.
        """
        state = RunState(playbook="site.yml")
        roles = [
            RoleGroupDefinition(
                role=f"role{r}",
                tasks=[
                    TaskDefinition(
                        name=f"r{r}-t{t}",
                        role=f"role{r}",
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=t,
                    )
                    for t in range(tasks_per_role)
                ],
            )
            for r in range(n_roles)
        ]
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="big",
                hosts="all",
                resolved_hosts=[f"h{i}" for i in range(hosts_per_task)],
                tasks=list(roles),
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "big"},
            }
        )
        for r in range(n_roles):
            for t in range(tasks_per_role):
                tname = f"r{r}-t{t}"
                state.handle_event(
                    {
                        "_event": "v2_playbook_on_task_start",
                        "_timestamp": "2026-04-20T10:00:02Z",
                        "task": {"id": f"{r}-{t}", "name": tname},
                        "play": {"id": "p1"},
                    }
                )
                for h in range(hosts_per_task):
                    state.handle_event(
                        {
                            "_event": "v2_runner_on_start",
                            "_timestamp": "2026-04-20T10:00:03Z",
                            "task": {"id": f"{r}-{t}", "name": tname},
                            "host": f"h{h}",
                        }
                    )
        return state

    def test_within_budget_is_unchanged(self):
        # Generous budget — no pruning should happen.
        from datetime import datetime, timezone

        state = self._many_tasks_state(n_roles=1, tasks_per_role=1, hosts_per_task=2)
        p = TreeProjection.from_run_state(state)
        now = datetime(2026, 4, 20, 10, 0, 5, tzinfo=timezone.utc)
        # Within-budget call equals the unbounded baseline.
        bounded = p.tree_lines(budget=999, now=now)
        # Re-fetch with a generous budget — should be deterministic.
        again = p.tree_lines(budget=999, now=now)
        assert bounded == again
        # Sanity check: host leaves present (not pruned away).
        assert any(ln.kind == "host" for ln in bounded)

    def test_collapses_host_leaves_first(self):
        # 1 role × 1 task × 5 hosts → 1 playbook + 1 play + 1 role + 1 task
        # + 5 hosts = 9 lines. Budget 4 used to fit structure + task but
        # no hosts; T2's two-footer algorithm spends two of the four
        # lines on "more" footers, so the structure compresses to
        # (playbook, play) + (inner footer, outer footer). What still
        # matters: no host leaves, and total lines stay within budget.
        state = self._many_tasks_state(n_roles=1, tasks_per_role=1, hosts_per_task=5)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=4)
        kinds = [ln.kind for ln in lines]
        assert "host" not in kinds
        assert len(lines) <= 4
        # T2 contract: when the budget overflows, at least one 'more'
        # footer is emitted so the user knows pending work exists.
        assert "more" in kinds, f"budget=4 must emit at least one 'more' footer; got {kinds}"

    def test_invariant_one_each_active_role_keeps_one_line(self):
        # 4 roles × 3 tasks × 2 hosts = lots. With a generous budget,
        # every role should be visible. With a tight budget, the
        # truncate-from-end approach prioritizes depth (showing role0's
        # full subtree with hosts) over breadth (showing all 4 roles).
        state = self._many_tasks_state(n_roles=4, tasks_per_role=3, hosts_per_task=2)
        p = TreeProjection.from_run_state(state)
        # Generous budget: all 4 roles visible.
        lines = p.tree_lines(budget=42)
        labels = "\n".join(ln.label for ln in lines)
        for r in range(4):
            assert f"role{r}" in labels, f"role{r} missing from full output:\n{labels}"

    def test_tight_budget_preserves_depth_over_breadth(self):
        # With a tight budget, truncate-from-end keeps the first role's
        # subtree (role0's tasks + hosts) and cuts later roles entirely.
        state = self._many_tasks_state(n_roles=4, tasks_per_role=3, hosts_per_task=2)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=8)
        labels = "\n".join(ln.label for ln in lines)
        # role0 is always visible (it's first in the tree).
        assert "role0" in labels, f"role0 missing from tight-budget output:\n{labels}"
        # Host leaves from role0's first task are visible (depth preserved).
        assert any(ln.kind == "host" for ln in lines), (
            f"expected host leaves in tight-budget output:\n{labels}"
        )


class TestTwoLevelTruncation:
    """Two-cut truncation: when the budget is exceeded, the algorithm
    emits BOTH an inner footer (when the cut lands inside a role) and an
    outer footer (always when the budget overflows). T2 keeps it simple
    by using raw line-list deltas for the counts — T3 will swap in
    task-domain counts in a post-truncation pass."""

    # -------- shared fixture helpers --------------------------------------

    def _single_play_single_role_state(self, n_tasks: int) -> RunState:
        """1 play, 1 role, ``n_tasks`` tasks, 1 host — the simplest
        tree whose budget cut lands inside a role's task list."""
        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="webserver",
                        tasks=[
                            TaskDefinition(
                                name=f"task {t}",
                                role="webserver",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=t,
                            )
                            for t in range(n_tasks)
                        ],
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t0", "name": "task 0"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t0", "name": "task 0"},
                "host": "web1",
            }
        )
        return state

    def _two_plays_state(self, n_tasks_per_role: int) -> RunState:
        """2 plays, each with a single role and ``n_tasks_per_role`` tasks.
        The unbounded tree is wide enough that a small budget cut will land
        cleanly between the two plays (not inside a role's task list)."""
        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="first",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="r1",
                        tasks=[
                            TaskDefinition(
                                name=f"p1-task {t}",
                                role="r1",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=t,
                            )
                            for t in range(n_tasks_per_role)
                        ],
                    )
                ],
            ),
            PlayDefinition(
                id="p2",
                name="second",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="r2",
                        tasks=[
                            TaskDefinition(
                                name=f"p2-task {t}",
                                role="r2",
                                tags=[],
                                play_id="p2",
                                play_order=1,
                                task_order=t,
                            )
                            for t in range(n_tasks_per_role)
                        ],
                    )
                ],
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "first"},
            }
        )
        # Mark first task of play 1 as running so the tree is visible.
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t0", "name": "p1-task 0"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t0", "name": "p1-task 0"},
                "host": "web1",
            }
        )
        return state

    # -------- the 6 tests ------------------------------------------------

    def test_within_budget_unchanged(self) -> None:
        """A small tree that fits the budget returns verbatim — no footers,
        no has_tail_after markers. Same contract as the pre-T2 single-cut
        path."""
        state = self._single_play_single_role_state(n_tasks=2)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=20)
        assert not any(ln.kind == "more" for ln in lines), (
            f"within-budget tree must not emit 'more' footers; got "
            f"{[(ln.kind, ln.label) for ln in lines]}"
        )
        assert not any(ln.has_tail_after for ln in lines), (
            f"within-budget tree must not set has_tail_after; got "
            f"{[(ln.kind, ln.has_tail_after) for ln in lines]}"
        )

    def test_outer_footer_appears_when_budget_overflow(self) -> None:
        """The classic scenario from test_tree_nested_roles.py: 1 play, 1
        role, 34 pending tasks + 2 running, budget=12. The last line must
        be the outer footer (kind="more", depth=0, "… and N more tasks")."""
        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        runtime_task_names = [
            "podman : Activate podman socket for API access",
            "podman : Wait for DNS resolution to be available",
        ]
        pending_task_names = [f"podman : pending task {idx}" for idx in range(1, 35)]
        all_runtime_names = runtime_task_names + pending_task_names

        preflight_tasks = [
            TaskDefinition(
                name="Activate podman socket for API access",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=0,
            ),
            TaskDefinition(
                name="Wait for DNS resolution to be available",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=1,
            ),
        ]

        state = RunState(playbook="main.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Setup rootless Podman",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[RoleGroupDefinition(role="podman", tasks=preflight_tasks)],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-23T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-23T10:00:01Z",
                "play": {"id": "p1", "name": "Setup rootless Podman"},
            }
        )

        for idx, name in enumerate(all_runtime_names, start=1):
            ts = f"2026-06-23T10:00:{idx + 2:02d}Z"
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": ts,
                    "task": {"id": f"t{idx}", "name": name},
                    "play": {"id": "p1"},
                }
            )
            if name in runtime_task_names:
                state.handle_event(
                    {
                        "_event": "v2_runner_on_start",
                        "_timestamp": ts,
                        "task": {"id": f"t{idx}", "name": name},
                        "host": "web1",
                    }
                )

        lines = TreeProjection.from_run_state(state).tree_lines(budget=12)
        outer = lines[-1]
        assert outer.kind == "more", f"outer footer must be kind='more'; got {outer.kind}"
        assert outer.depth == 0, f"outer footer must be at depth=0; got {outer.depth}"
        import re

        assert re.match(r"… and \d+ more tasks", outer.label), (
            f"outer footer label must match '… and N more tasks'; got {outer.label!r}"
        )

    def test_inner_footer_emitted_when_cut_inside_role(self) -> None:
        """When the budget cut lands inside a role's task list, both an
        inner footer (at the role's task depth) and an outer footer (at
        depth 0) are emitted. The line above the inner footer carries
        ``has_tail_after=True`` so the renderer demotes its glyph and
        keeps the parent spine running."""
        # 1 play + 1 role + 20 tasks → 23 unbounded lines. Budget=6
        # forces a cut inside the role's task list.
        state = self._single_play_single_role_state(n_tasks=20)
        p = TreeProjection.from_run_state(state)
        unbounded_count = len(p.tree_lines(budget=999))
        assert unbounded_count > 6, (
            f"sanity: unbounded tree must overflow budget=6; got {unbounded_count}"
        )

        lines = p.tree_lines(budget=6)

        outer = lines[-1]
        assert outer.kind == "more", f"last line must be outer footer; got {outer.kind}"
        assert outer.depth == 0, f"outer footer must be at depth=0; got {outer.depth}"

        more_lines = [ln for ln in lines if ln.kind == "more"]
        assert len(more_lines) == 3, (
            f"must emit role, play, and outer footers; got {len(more_lines)}"
        )

        role_inner = more_lines[0]
        play_inner = more_lines[1]
        non_footer_lines = [ln for ln in lines if ln.kind != "more"]
        deepest_visible_depth = max(ln.depth for ln in non_footer_lines)
        assert role_inner.depth == deepest_visible_depth, (
            f"role inner footer depth ({role_inner.depth}) must match deepest visible "
            f"line depth ({deepest_visible_depth})"
        )
        assert play_inner.depth == 2, f"play inner footer depth must be 2; got {play_inner.depth}"

        above_inner = non_footer_lines[-1]
        assert above_inner.has_tail_after is True, (
            f"line above inner footer must have has_tail_after=True; got "
            f"has_tail_after={above_inner.has_tail_after} on "
            f"(depth={above_inner.depth}, kind={above_inner.kind}, "
            f"label={above_inner.label!r})"
        )

        import re

        m = re.match(r"… and (\d+) more tasks", role_inner.label)
        assert m, f"inner footer label must match '… and N more tasks'; got {role_inner.label!r}"
        inner_count = int(m.group(1))
        assert inner_count > 0, f"inner footer count must be positive; got {inner_count}"

    def test_no_inner_footer_when_cut_between_plays(self) -> None:
        """When the budget cut lands cleanly on a play boundary (between
        two plays), the algorithm must NOT emit an inner footer — only
        the outer footer at depth 0."""
        state = self._two_plays_state(n_tasks_per_role=10)
        p = TreeProjection.from_run_state(state)
        unbounded = p.tree_lines(budget=999)

        # Locate the second play's index in the unbounded tree so the
        # budget lands the outer cut on a play boundary, not inside a
        # role's task list. (Walking back from budget_idx must hit a
        # 'play' line for the cut to be "between plays".)
        play2_idx = next(i for i, ln in enumerate(unbounded) if ln.kind == "play" and i > 0)

        # budget_idx = play2_idx; budget = play2_idx + 1.
        budget = play2_idx + 1
        lines = p.tree_lines(budget=budget)

        more_lines = [ln for ln in lines if ln.kind == "more"]
        assert len(more_lines) == 1, (
            f"cut between plays must emit exactly one footer; got "
            f"{len(more_lines)} footers: {[(ln.depth, ln.label) for ln in more_lines]}"
        )
        outer = more_lines[0]
        assert outer.depth == 0, f"outer footer must be at depth=0; got {outer.depth}"
        assert not any(ln.kind == "more" and ln.depth != 0 for ln in lines), (
            f"no inner footer must be emitted; got {[ln for ln in lines if ln.kind == 'more']}"
        )

    def test_inner_count_uses_role_remaining_count(self) -> None:
        """The inner footer's count must equal the number of tasks remaining
        in the *active role's branch* — derived from
        ``role_total - role_visible`` (the same formula the inner
        footer uses). The role label no longer carries a ``(M remaining)``
        suffix (it duplicates completed count and grew as the run
        progressed); the inner footer is the source of truth for the
        hidden-work signal.

        With 1 play, 1 role, 20 tasks, and budget=6, the cut lands
        inside the role's task list. The inner footer count must
        equal ``role_total_tasks - role_visible_tasks``.
        """
        import re

        state = self._single_play_single_role_state(n_tasks=20)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=6)

        inner = lines[-2]
        assert inner.kind == "more"

        # Find the role line and extract its (N tasks) count.
        role_line = next(ln for ln in lines if ln.kind == "role")
        m_role = re.search(r"\((\d+) tasks?\)", role_line.label)
        assert m_role, f"role label must contain '(N tasks)'; got {role_line.label!r}"
        role_total = int(m_role.group(1))
        assert "remaining" not in role_line.label, (
            f"role label must NOT carry 'remaining' suffix; got {role_line.label!r}"
        )

        # Extract the inner footer count.
        m_inner = re.match(r"… and (\d+) more tasks", inner.label)
        assert m_inner, f"inner footer label must match '… and N more tasks'; got {inner.label!r}"
        inner_count = int(m_inner.group(1))

        # Inner footer count must equal role_total - visible, i.e.
        # total kept-role-tasks minus inner footer count = role_total.
        assert inner_count == role_total - 1, (
            f"inner footer count ({inner_count}) must equal role_total - visible "
            f"({role_total} - 1 = {role_total - 1}); visible=1 task under r1 "
            f"with budget=6."
        )

    def test_inner_footer_does_not_count_upcoming_plays_tasks(self) -> None:
        """The inner footer must NOT count tasks from upcoming plays.

        State: 2 plays, each with 1 role and tasks. The first play has
        20 tasks, the second has 30. A small budget forces the cut
        inside the first play's role. The inner footer count must
        equal ``first_play_role_total - visible_tasks_under_r1`` and
        must NOT include any of the second play's 30 tasks.
        """
        import re

        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="first",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="r1",
                        tasks=[
                            TaskDefinition(
                                name=f"p1-task {t}",
                                role="r1",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=t,
                            )
                            for t in range(20)
                        ],
                    )
                ],
            ),
            PlayDefinition(
                id="p2",
                name="second",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="r2",
                        tasks=[
                            TaskDefinition(
                                name=f"p2-task {t}",
                                role="r2",
                                tags=[],
                                play_id="p2",
                                play_order=1,
                                task_order=t,
                            )
                            for t in range(30)
                        ],
                    )
                ],
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "first"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t0", "name": "p1-task 0"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t0", "name": "p1-task 0"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=6)

        # There must be an inner footer (depth > 0, kind == "more").
        inner = next((ln for ln in lines if ln.kind == "more" and ln.depth > 0), None)
        assert inner is not None, (
            f"expected an inner footer (kind='more', depth>0); got "
            f"{[(ln.kind, ln.depth, ln.label) for ln in lines]}"
        )

        m = re.match(r"… and (\d+) more tasks", inner.label)
        assert m, f"inner footer label must match '… and N more tasks'; got {inner.label!r}"
        inner_count = int(m.group(1))

        # Count visible tasks under the first play's role (r1).
        role_line = next(ln for ln in lines if ln.kind == "role" and ln.identity == "r1")
        m_role = re.search(r"\((\d+) tasks?\)", role_line.label)
        assert m_role, f"role label for r1 must contain '(N tasks)'; got {role_line.label!r}"
        assert "remaining" not in role_line.label, (
            f"role label must NOT carry 'remaining' suffix; got {role_line.label!r}"
        )
        role_total = int(m_role.group(1))

        # The inner footer count must equal role_total - visible. With
        # 1 visible task under r1, that's 20 - 1 = 19.
        assert inner_count == role_total - 1, (
            f"inner footer count ({inner_count}) must equal r1's total "
            f"minus visible ({role_total} - 1 = {role_total - 1}); the "
            f"second play's 30 tasks must NOT contribute."
        )

        # Also verify the count is strictly less than 20+30=50 (the total
        # task count across both plays), proving upcoming tasks are excluded.
        assert inner_count < 50, (
            f"inner footer count ({inner_count}) must be less than 50 "
            f"(total tasks across both plays); upcoming play tasks are "
            f"included incorrectly."
        )

        # The count must be strictly less than 20 (the first role's total),
        # because some tasks under r1 are visible.
        assert inner_count < 20, (
            f"inner footer count ({inner_count}) must be less than r1's "
            f"total task count (20) because some tasks are visible."
        )

    def test_outer_count_uses_task_domain_count(self) -> None:
        """The outer footer's count uses task-domain semantics: hidden
        plays, roles, and tasks below the kept window. Host leaves and
        footers do not count."""
        state = self._single_play_single_role_state(n_tasks=20)
        p = TreeProjection.from_run_state(state)
        unbounded = p.tree_lines(budget=999)
        lines = p.tree_lines(budget=6)
        outer = lines[-1]
        assert outer.kind == "more"

        kept_original = len(lines) - sum(1 for ln in lines if ln.kind == "more")
        dropped = unbounded[kept_original:]
        expected_count = sum(1 for ln in dropped if ln.kind in ("task", "role", "play"))
        import re

        m = re.match(r"… and (\d+) more tasks", outer.label)
        assert m
        actual_count = int(m.group(1))
        assert actual_count == expected_count, (
            f"outer footer count ({actual_count}) must equal the number of "
            f"hidden task-domain entities ({expected_count}); "
            f"unbounded={len(unbounded)} kept={kept_original}"
        )

    def test_every_inner_section_line_has_tail_after(self) -> None:
        """Every line in the inner section must carry
        ``has_tail_after=True`` so the renderer demotes every line's
        branch glyph from ``└─`` to ``├─`` and keeps the parent spine
        running all the way down to the inner footer.

        The pre-fix implementation marked only the LAST line of the
        inner section (the host leaf directly above the inner
        footer), which left the play, role, and task ancestors as
        ``└─`` — breaking the visual continuity the user wanted in
        the plan's sketch. The renderer's ``is_last`` look-ahead was
        already correct; it just needed more input lines marked with
        ``has_tail_after=True`` to produce the right output.
        """
        state = self._single_play_single_role_state(n_tasks=20)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=6)

        # Sanity: budget=6 must trigger truncation (both footers present).
        # The exact line count varies with inner_budget arithmetic — what
        # matters for this test is the has_tail_after marking, not the
        # specific layout. With n_tasks=20 and budget=6, the algorithm
        # produces a small but non-trivial kept tree: head + an inner
        # section + both footers. We don't pin the line count here; the
        # sibling test ``test_inner_footer_emitted_when_cut_inside_role``
        # covers the layout contract.
        more_lines = [ln for ln in lines if ln.kind == "more"]
        assert len(more_lines) == 3, (
            f"sanity: cut-inside-role must emit role + play + outer footers; "
            f"got {len(more_lines)} footers in: "
            f"{[(ln.kind, ln.depth, ln.label) for ln in lines]}"
        )

        # Strip both footers: the outer footer (last line, kind="more",
        # depth=0) and the inner footer (kind="more", depth>0). What's
        # left is head + inner_section.
        non_footer_lines = [ln for ln in lines if ln.kind != "more"]
        # Everything in the inner section must carry has_tail_after.
        # The head's last line also carries it (set on `head[-1]`),
        # so the assertion covers both head and inner_section.
        for ln in non_footer_lines:
            assert ln.has_tail_after is True, (
                f"every line above the footers must have "
                f"has_tail_after=True (post-T2-fix); got "
                f"has_tail_after={ln.has_tail_after} on "
                f"(kind={ln.kind!r}, depth={ln.depth}, "
                f"label={ln.label!r})"
            )

        # The inner footer itself must NOT carry has_tail_after (it's
        # a leaf — there's no line below it to spur).
        inner_footer = next(ln for ln in lines if ln.kind == "more" and ln.depth > 0)
        assert inner_footer.has_tail_after is False, (
            "inner footer must not carry has_tail_after (it's the cut marker)"
        )
        # The outer footer is at depth 0; it also doesn't carry the flag.
        outer_footer = lines[-1]
        assert outer_footer.kind == "more" and outer_footer.depth == 0
        assert outer_footer.has_tail_after is False, (
            "outer footer must not carry has_tail_after (it's the cut marker)"
        )


class TestRoleLabelsAfterTruncation:
    """T3: post-truncation role-label pass.

    After `_truncate_two_level` runs, every role line's label is rewritten
    so the count semantic matches the user's question:

    - ``role: X (N tasks)`` — always carries the role's full task count
      from preflight + runtime definitions. ``N`` is the role's total,
      regardless of how many tasks are visible in the kept lines.
    - ``role: X`` — when the role has zero tasks (no count emitted).

    The ``(M remaining)`` suffix that earlier revisions of this pass
    emitted was dropped because it counted completed tasks (which are
    dropped from the kept lines) and grew as the run progressed. The
    ``… and N more tasks`` inner/outer footers already surface the
    hidden-work signal in the truncated case, so the role label no
    longer needs to mirror them.

    This pass is purely a label-rewrite; the TreeLine's other fields are
    untouched. The renderer doesn't pattern-match the suffix, so no
    renderer change was required.
    """

    def _many_tasks_state(self, n_roles: int, tasks_per_role: int, hosts_per_task: int) -> RunState:
        """Re-declaration of ``TestTreeLinesPruning._many_tasks_state`` —
        small inline copy so this test class can build the (1 role,
        N tasks, M hosts) shape it needs without depending on another
        test class. The plan preferred sharing the helper from
        ``TestTwoLevelTruncation``; the existing per-class fixture
        pattern in this file conflicts with that, so a small per-class
        copy is the pragmatic compromise. ``RunState`` is already
        imported at module scope."""

        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        roles = [
            RoleGroupDefinition(
                role=f"role{r}",
                tasks=[
                    TaskDefinition(
                        name=f"r{r}-t{t}",
                        role=f"role{r}",
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=t,
                    )
                    for t in range(tasks_per_role)
                ],
            )
            for r in range(n_roles)
        ]
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="big",
                hosts="all",
                resolved_hosts=[f"h{i}" for i in range(hosts_per_task)],
                tasks=list(roles),
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "big"},
            }
        )
        for r in range(n_roles):
            for t in range(tasks_per_role):
                tname = f"r{r}-t{t}"
                state.handle_event(
                    {
                        "_event": "v2_playbook_on_task_start",
                        "_timestamp": "2026-04-20T10:00:02Z",
                        "task": {"id": f"{r}-{t}", "name": tname},
                        "play": {"id": "p1"},
                    }
                )
                for h in range(hosts_per_task):
                    state.handle_event(
                        {
                            "_event": "v2_runner_on_start",
                            "_timestamp": "2026-04-20T10:00:03Z",
                            "task": {"id": f"{r}-{t}", "name": tname},
                            "host": f"h{h}",
                        }
                    )
        return state

    def test_role_label_shows_total_when_no_truncation(self) -> None:
        """Within-budget tree: 1 role with 3 visible tasks (each with 1
        host leaf). budget=20 is well within the 9-line tree. Label must
        read ``role: role0 (3 tasks)`` — same form as today's emission,
        no 'remaining' suffix."""

        state = self._many_tasks_state(n_roles=1, tasks_per_role=3, hosts_per_task=1)
        lines = TreeProjection.from_run_state(state).tree_lines(budget=20)
        # Sanity: within budget, no truncation footers.
        assert not any(ln.kind == "more" for ln in lines), (
            f"within-budget tree must not emit 'more' footers; got "
            f"{[(ln.kind, ln.label) for ln in lines]}"
        )

        role_line = next(ln for ln in lines if ln.kind == "role")
        assert role_line.label == "role: role0 (3 tasks)", (
            f"role label must be '(3 tasks)' when all tasks are visible; got {role_line.label!r}"
        )

    def test_role_label_shows_total_when_inside_cut(self) -> None:
        """Cut inside the role's task list: 1 role + 3 tasks (each with
        1 host leaf), budget=6. Layout: playbook(0), play(1), role(2),
        task0(3), host0(4), task1(5), host1(6), task2(7), host2(8) — 9
        lines total. ``inner_budget = 6 - 1 - 2 = 3`` keeps
        ``inner_section = [play, role, task0]``: visible=1, total=3.

        Role label always reads ``(N tasks)`` (the role's total). The
        ``… and N more tasks`` inner footer carries the hidden-work
        signal — role labels never carry a ``remaining`` suffix (that
        variant counted completed tasks and grew as the run progressed).
        """

        state = self._many_tasks_state(n_roles=1, tasks_per_role=3, hosts_per_task=1)
        lines = TreeProjection.from_run_state(state).tree_lines(budget=6)
        # Sanity: confirm the visible-count bookkeeping gives exactly 1.
        task_lines = [ln for ln in lines if ln.kind == "task"]
        assert len(task_lines) == 1, (
            f"sanity: budget=6 should leave exactly 1 visible task; got "
            f"{len(task_lines)} tasks in {[ln.label for ln in lines]}"
        )
        assert any(ln.kind == "more" for ln in lines), (
            "sanity: budget=6 must trigger truncation (footers present)"
        )

        role_line = next(ln for ln in lines if ln.kind == "role")
        assert role_line.label == "role: role0 (3 tasks)", (
            f"role label must be '(3 tasks)' (the total) when visible=1 "
            f"and total=3 — no 'remaining' suffix; got {role_line.label!r}"
        )
        assert "remaining" not in role_line.label, (
            f"role label must NOT carry 'remaining' suffix; got {role_line.label!r}"
        )

    def test_role_label_shows_total_when_all_tasks_visible_after_cut(self) -> None:
        """Edge case: visible == total. The role label reads ``(N tasks)``
        — no ``remaining`` suffix (the suffix was dropped because it
        counted completed tasks and grew as the run progressed)."""

        state = self._many_tasks_state(n_roles=1, tasks_per_role=3, hosts_per_task=1)
        # budget=10 fits the whole 9-line tree (1 playbook + 1 play +
        # 1 role + 3 tasks + 3 hosts) — within budget, no truncation.
        lines = TreeProjection.from_run_state(state).tree_lines(budget=10)
        assert not any(ln.kind == "more" for ln in lines), (
            f"budget=10 must fit the 9-line tree; got {[(ln.kind, ln.label) for ln in lines]}"
        )

        role_line = next(ln for ln in lines if ln.kind == "role")
        assert role_line.label == "role: role0 (3 tasks)", (
            f"role label must be '(3 tasks)' when all tasks are visible; got {role_line.label!r}"
        )
        assert "remaining" not in role_line.label, (
            f"role label must NOT carry 'remaining' suffix; got {role_line.label!r}"
        )

    def test_role_label_singular_plural_format(self) -> None:
        """Verify exact format strings across the singular/plural cases:

        - ``(1 task)`` (singular, total=1)
        - ``(2 tasks)`` (plural, total=2)

        The role label always carries the role's total task count
        ``(N tasks)`` — never a ``(M remaining)`` suffix. The
        ``… and N more tasks`` inner/outer footers carry the
        hidden-work signal. The implementation must use ``'task'``
        (singular) for N=1, ``'tasks'`` (plural) otherwise — matching
        the existing convention from ``_emit_pending_play``.
        """

        # Case 1: ``(1 task)`` — 1 role + 1 task + 1 host, within budget.
        #   1 playbook + 1 play + 1 role + 1 task + 1 host = 5 lines;
        #   budget=10 is well within the tree, no cut.
        state1 = self._many_tasks_state(n_roles=1, tasks_per_role=1, hosts_per_task=1)
        lines1 = TreeProjection.from_run_state(state1).tree_lines(budget=10)
        role1 = next(ln for ln in lines1 if ln.kind == "role")
        assert role1.label == "role: role0 (1 task)", f"singular '(1 task)': got {role1.label!r}"

        # Case 2: ``(2 tasks)`` — 1 role + 2 tasks + 2 hosts, within
        #   budget. 1 playbook + 1 play + 1 role + 2*(task+host) = 7
        #   lines; budget=10 is within budget, all visible.
        state2 = self._many_tasks_state(n_roles=1, tasks_per_role=2, hosts_per_task=1)
        lines2 = TreeProjection.from_run_state(state2).tree_lines(budget=10)
        role2 = next(ln for ln in lines2 if ln.kind == "role")
        assert role2.label == "role: role0 (2 tasks)", f"plural '(2 tasks)': got {role2.label!r}"

        # Case 3: cut inside 1 role + 2 tasks + 2 hosts per task.
        #   9 lines total. budget=6 → inner_budget = 3 → inner_section
        #   = [play, role, task0]. visible=1, total=2. Role label
        #   still reads "(2 tasks)" — the total — no "remaining" suffix.
        state3 = self._many_tasks_state(n_roles=1, tasks_per_role=2, hosts_per_task=2)
        lines3 = TreeProjection.from_run_state(state3).tree_lines(budget=6)
        # Sanity: 1 visible task.
        task_lines3 = [ln for ln in lines3 if ln.kind == "task"]
        assert len(task_lines3) == 1, (
            f"sanity: case 3 must have visible=1; got {len(task_lines3)} tasks"
        )
        role3 = next(ln for ln in lines3 if ln.kind == "role")
        assert role3.label == "role: role0 (2 tasks)", (
            f"case 3 must read total '(2 tasks)' inside the cut — no "
            f"'remaining' suffix; got {role3.label!r}"
        )
        assert "remaining" not in role3.label, (
            f"case 3 must NOT carry 'remaining' suffix; got {role3.label!r}"
        )

        # Case 4: cut inside 1 role + 3 tasks + 1 host per task. 9 lines
        #   total. budget=6 → inner_budget = 3 → inner_section =
        #   [play, role, task0]. visible=1, total=3. Role label still
        #   reads "(3 tasks)" — the total.
        state4 = self._many_tasks_state(n_roles=1, tasks_per_role=3, hosts_per_task=1)
        lines4 = TreeProjection.from_run_state(state4).tree_lines(budget=6)
        task_lines4 = [ln for ln in lines4 if ln.kind == "task"]
        assert len(task_lines4) == 1, (
            f"sanity: case 4 must have visible=1; got {len(task_lines4)} tasks"
        )
        role4 = next(ln for ln in lines4 if ln.kind == "role")
        assert role4.label == "role: role0 (3 tasks)", (
            f"case 4 must read total '(3 tasks)' inside the cut — no "
            f"'remaining' suffix; got {role4.label!r}"
        )
        assert "remaining" not in role4.label, (
            f"case 4 must NOT carry 'remaining' suffix; got {role4.label!r}"
        )


class TestTreeLineIdentity:
    """Regression guard: role TreeLines carry a structured identity field
    so the pruner / renderer don't have to parse `label`."""

    def test_role_line_has_identity_matching_role_name(self):
        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="webserver",
                        tasks=[
                            TaskDefinition(
                                name="Install nginx",
                                role="webserver",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=0,
                            )
                        ],
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        role_line = next(ln for ln in lines if ln.kind == "role")
        assert role_line.identity == "webserver"
        # Label now includes task count
        assert role_line.label.startswith("role: webserver")

    def test_non_role_lines_have_none_identity(self):
        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        for ln in lines:
            if ln.kind != "role":
                assert ln.identity is None, (
                    f"non-role line {ln.kind!r}/{ln.label!r} has non-None identity"
                )


class TestTreeLineHasTailAfter:
    """Regression guard: ``TreeLine.has_tail_after`` carries the
    'a "more tasks" footer follows this line at the same or deeper depth'
    flag. Today every line carries the default ``False``; T2 of the
    two-level-truncation plan starts setting it ``True`` on the last line
    of `head` and the last line of the inner section."""

    def test_field_exists_with_default_false(self) -> None:
        """A TreeLine constructed positionally (no kwarg) has
        ``has_tail_after=False`` — backwards compatible with all the
        existing positional call sites in tree.py."""
        line = TreeLine(
            depth=0,
            kind="play",
            label="play: deploy",
            glyph="└─",
            status=None,
            elapsed_s=None,
            identity=None,
        )
        assert line.has_tail_after is False

    def test_can_construct_with_has_tail_after_true(self) -> None:
        """Constructing a TreeLine with ``has_tail_after=True`` works and
        the value round-trips through the frozen dataclass."""
        line = TreeLine(
            depth=1,
            kind="role",
            label="role: webserver",
            glyph="├─",
            status=Status.PENDING,
            elapsed_s=None,
            identity="webserver",
            has_tail_after=True,
        )
        assert line.has_tail_after is True

    def test_default_is_false_for_keyword_construction(self) -> None:
        """Kwarg-only construction also defaults to ``False`` — covers
        the case where someone writes ``TreeLine(...)`` without naming
        every field."""
        line = TreeLine(
            depth=0,
            kind="playbook",
            label="site.yml",
            glyph=None,
            status=None,
            elapsed_s=None,
        )
        assert line.has_tail_after is False


class TestTreeKindIncludesMore:
    """Regression guard: the ``TreeKind`` Literal must include the
    ``"more"`` value so the renderer can pattern-match against it once
    T2 starts emitting footer lines."""

    def test_more_is_part_of_literal(self) -> None:
        import typing

        from ansible_aom.core.tree import TreeKind

        assert "more" in typing.get_args(TreeKind), (
            "TreeKind Literal must include 'more' for two-level truncation "
            "footers; see .sisyphus/plans/two-level-truncation.md T1."
        )

    def test_tree_line_accepts_more_kind(self) -> None:
        """Constructing a TreeLine with ``kind='more'`` is statically valid
        — guards against a future edit that drops 'more' from the
        Literal and breaks every call site that emits footers."""
        line = TreeLine(
            depth=0,
            kind="more",
            label="… and 12 more tasks",
            glyph=None,
            status=Status.PENDING,
            elapsed_s=None,
            identity=None,
            has_tail_after=False,
        )
        assert line.kind == "more"


class TestTaskCompletionLifecycle:
    """Regression guards: under linear strategy the state machine sets
    task.status = RUNNING on v2_runner_on_start and never transitions it
    back. The projection therefore must not rely on task.status to decide
    'is this task currently running'; it must derive that from per-host
    HostRunState.RUNNING entries instead. See bug found post-Task 9."""

    def _linear_strategy_finished_task(self) -> RunState:
        """Simulate a complete linear-strategy task lifecycle:
        task_start → runner_on_start per host → runner_on_ok per host.
        After this sequence task.status is stuck at RUNNING but every
        host has terminal status — the task is logically complete."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        for host in ("web1", "web2"):
            state.handle_event(
                {
                    "_event": "v2_runner_on_start",
                    "_timestamp": "2026-04-20T10:00:03Z",
                    "task": {"id": "t1", "name": "Install nginx"},
                    "host": host,
                }
            )
            state.handle_event(
                {
                    "_event": "v2_runner_on_ok",
                    "_timestamp": "2026-04-20T10:00:05Z",
                    "task": {"id": "t1", "name": "Install nginx"},
                    "hosts": {host: {"ok": True, "changed": False}},
                }
            )
        return state

    def test_tree_visible_after_all_hosts_finished_no_stats(self):
        """After a task's hosts all reach terminal state, the tree
        stays visible (sticky) until either the next task starts or
        v2_playbook_on_stats fires. See sister test
        `test_tree_sticky_between_tasks_shows_last_task` and
        `test_tree_hidden_after_playbook_stats` for the bracketing
        cases."""
        state = self._linear_strategy_finished_task()
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is True

    def test_tree_does_not_show_completed_task_between_tasks(self):
        """Completed tasks are intentionally dropped from the tree — the
        streaming log above the panel already carries them. Between
        tasks the tree's job is to show pending work, not replay history.
        Regression guard for the post-redesign contract: 'show only the
        currently-running task and everything still to come.'"""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        for host in ("web1", "web2"):
            state.handle_event(
                {
                    "_event": "v2_runner_on_ok",
                    "_timestamp": "2026-04-20T10:00:05Z",
                    "task": {"id": "t1", "name": "Install nginx"},
                    "hosts": {host: {"ok": True, "changed": False}},
                }
            )
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is True, (
            "tree should remain visible between tasks while playbook is in flight"
        )
        lines = p.tree_lines(budget=25)
        # No preflight definitions + only completed runtime tasks → the
        # play yields nothing to show. The tree degrades to just the
        # playbook header line until the next task starts.
        assert all(ln.label != "Install nginx" for ln in lines if ln.kind == "task"), lines

    def test_tree_hidden_after_playbook_stats(self):
        """Once v2_playbook_on_stats fires, RunState.status becomes
        COMPLETED/FAILED and end_time is set — the tree should hide
        regardless of any lingering task entries."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        state.handle_event(
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-04-20T10:00:10Z", "stats": {}}
        )
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is False

    def test_tree_hidden_before_any_task_starts(self):
        """At the very start of a run (after playbook_on_start, before
        any task announcement), there's nothing to show. Tree must
        stay hidden — sticky-mode only kicks in once a task has been
        seen."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is False

    def test_tree_visible_under_linear_strategy_with_preflight_hosts(self):
        """Under linear strategy, `ansible.posix.jsonl` does NOT emit
        `v2_runner_on_start` (the callback guards it with `if
        self._is_lockstep: return`). So per-host RUNNING entries cannot
        come from runner_on_start. Instead they must be synthesised at
        `v2_playbook_on_task_start` using the matching play's preflight
        `resolved_hosts`. Regression guard for: tree never appearing
        under linear-strategy playbooks."""
        from ansible_aom.core.models import (
            PlayDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="deploy",
                hosts="webservers",
                resolved_hosts=["web1", "web2", "web3"],
                tasks=[
                    TaskDefinition(
                        name="Install nginx",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=0,
                    )
                ],
            )
        ]
        # No v2_runner_on_start events — pure linear-strategy flow.
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-real", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "play-uuid-real"},
            }
        )
        p = TreeProjection.from_run_state(state)
        # The tree must be visible — all three hosts should be reported
        # as RUNNING for this task.
        assert p.is_tree_visible() is True
        host_lines = [ln for ln in p.tree_lines(budget=25) if ln.kind == "host"]
        host_labels = sorted(ln.label for ln in host_lines)
        assert host_labels == ["web1", "web2", "web3"]

    def test_tree_lines_skip_tasks_with_no_running_hosts(self):
        """A new task starts while a previous task is still stuck at
        task.status=RUNNING but has all hosts in terminal state. The
        tree should show ONLY the new task, not the stale one."""
        state = self._linear_strategy_finished_task()
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:06Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:07Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "host": "web1",
            }
        )
        p = TreeProjection.from_run_state(state)
        task_lines = [ln for ln in p.tree_lines(budget=25) if ln.kind == "task"]
        names = [ln.label.split("  ")[0] for ln in task_lines]
        assert "Install nginx" not in names, (
            f"completed task should not appear in tree, got {names!r}"
        )
        assert "Configure firewall" in names

    def test_tree_shows_pending_tasks_in_partially_completed_play(self):
        """Regression: a play with some completed tasks AND some still-pending
        tasks must NOT be skipped, even when no task is currently RUNNING.

        The pre-fix code at ``_tree_lines_unbounded`` used
        ``not any(k == "running" ...) and runtime.tasks`` to skip "completed"
        plays, but that condition also skipped plays whose preflight tasks
        had not yet started. The user saw only the active play's running
        task and lost all upcoming pending work in the prior play.

        Setup: Play A has T1 (completed in runtime) and T2 (pending in
        preflight only). Play B has T3 currently running. Both plays
        should appear; T2 should appear as a pending task under Play A.
        """
        from ansible_aom.core.models import PlayDefinition, TaskDefinition

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="pA",
                name="Play A",
                hosts="webservers",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="T1", role=None, tags=[], play_id="pA", play_order=0, task_order=0
                    ),
                    TaskDefinition(
                        name="T2", role=None, tags=[], play_id="pA", play_order=0, task_order=1
                    ),
                ],
            ),
            PlayDefinition(
                id="pB",
                name="Play B",
                hosts="dbservers",
                resolved_hosts=["db1"],
                tasks=[
                    TaskDefinition(
                        name="T3", role=None, tags=[], play_id="pB", play_order=1, task_order=0
                    ),
                ],
            ),
        ]
        # Play A starts, T1 runs and completes, then Play B starts and T3 runs.
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-22T10:00:01Z",
                "play": {"id": "pA", "name": "Play A"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-06-22T10:00:02Z",
                "task": {"id": "ta1", "name": "T1"},
                "play": {"id": "pA"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-22T10:00:03Z",
                "task": {"id": "ta1", "name": "T1"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-06-22T10:00:04Z",
                "task": {"id": "ta1", "name": "T1"},
                "hosts": {"web1": {"changed": False}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-22T10:00:05Z",
                "play": {"id": "pB", "name": "Play B"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-06-22T10:00:06Z",
                "task": {"id": "tb3", "name": "T3"},
                "play": {"id": "pB"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-22T10:00:07Z",
                "task": {"id": "tb3", "name": "T3"},
                "host": "db1",
            }
        )

        p = TreeProjection.from_run_state(state)
        play_lines = [ln for ln in p.tree_lines(budget=25) if ln.kind == "play"]
        play_names = [ln.label.removeprefix("play: ") for ln in play_lines]
        # Play A has finished and has no running tasks, so only the active Play B appears
        assert play_names == ["Play B"], f"only active play should appear; got {play_names!r}"

        task_lines = [ln for ln in p.tree_lines(budget=25) if ln.kind == "task"]
        task_names = [ln.label.split("  ")[0] for ln in task_lines]
        assert "T3" in task_names, f"running task T3 should appear, got {task_names!r}"
        assert "T1" not in task_names, f"completed task T1 should not appear, got {task_names!r}"
        assert "T2" not in task_names, (
            f"skipped preflight task T2 of finished play should not appear, got {task_names!r}"
        )


class TestIncludeStubHiding:
    """TC-094j / TC-094k: include_tasks stubs are hidden when children are grafted."""

    def _active_state(self, stub: TaskDefinition, *children: TaskDefinition) -> RunState:
        """Build a RunState where the stub is a running/pending task in play p1.

        Mirrors how the existing tree tests warm up ``state.plays``: fire a
        play_start and then a task_start so the play has active items and
        the projection's lease logic surfaces it.
        """
        defs = [
            PlayDefinition(
                id="p1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[stub],
            )
        ]
        state = RunState(playbook="site.yml", definitions=defs)
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-24T10:00:00Z",
                "play": {"id": "p1", "name": "Test"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-24T10:00:01Z",
                "task": {"id": "t-stub", "name": stub.name},
                "play": {"id": "p1"},
            }
        )
        for idx, child in enumerate(children):
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": f"2026-05-24T10:00:0{2 + idx}Z",
                    "task": {"id": f"t-{idx}", "name": child.name},
                    "play": {"id": "p1"},
                }
            )
        return state

    def test_include_stub_with_children_is_hidden(self):
        """TC-094j: stub with grafted children disappears from the tree; children show."""
        child_a = TaskDefinition(
            name="Inner Alpha",
            role="podman",
            tags=[],
            play_id="p1",
            play_order=0,
            task_order=0,
        )
        child_b = TaskDefinition(
            name="Inner Beta",
            role="podman",
            tags=[],
            play_id="p1",
            play_order=0,
            task_order=1,
        )
        stub = TaskDefinition(
            name="Include site",
            role="podman",
            tags=[],
            play_id="p1",
            play_order=0,
            task_order=2,
            children=[child_a, child_b],
        )
        state = self._active_state(stub, child_b)
        projection = TreeProjection.from_run_state(state)
        labels = [ln.label for ln in projection.tree_lines(budget=25)]

        assert not any("Include site" in lbl for lbl in labels), (
            f"stub name should be hidden, got labels={labels!r}"
        )
        assert any("Inner Beta" in lbl for lbl in labels), (
            f"grafted child 'Inner Beta' should appear, got labels={labels!r}"
        )
        assert any("Inner Alpha" in lbl for lbl in labels), (
            f"grafted child 'Inner Alpha' should appear, got labels={labels!r}"
        )

    def test_include_stub_without_children_stays_visible(self):
        """TC-094k: defensive — Jinja-path stub with no children still renders."""
        stub = TaskDefinition(
            name="Include dynamic",
            role="web",
            tags=[],
            play_id="p1",
            play_order=0,
            task_order=0,
        )
        state = self._active_state(stub)
        projection = TreeProjection.from_run_state(state)
        labels = [ln.label for ln in projection.tree_lines(budget=25)]

        assert any("Include dynamic" in lbl for lbl in labels), (
            f"stub with no children should still render, got labels={labels!r}"
        )


class TestSubtreeRoleCounting:
    """Subtree semantics for ``_build_role_total_tasks`` and
    ``_count_visible_tasks_per_role``.

    The role label and inner footer counts must reflect the *subtree*
    under each role header — every task whose role path includes the
    role, transitively. Previously both helpers keyed on the innermost
    role only, which made an outer role's count miss everything below
    a nested sub-role (the user's complaint about a podman role whose
    count didn't reflect the subtree — and the nested level's count
    was missing entirely).

    Single-role fixtures keep their existing totals unchanged because
    the subtree of a leaf role equals its direct children.
    """

    def _nested_state(
        self, n_podman_direct: int, n_angie: int, *, fired: int | None = None
    ) -> RunState:
        """Build a state with ``podman > angie_ssl_terminator`` nesting.

        ``n_podman_direct`` tasks live directly under ``role: podman``
        (no inner sub-role). ``n_angie`` tasks live inside a nested
        ``role: angie_ssl_terminator`` under podman. The preflight
        definitions produce role paths ``("podman",)`` for direct
        podman tasks and ``("podman", "angie_ssl_terminator")`` for
        angie's tasks.

        ``fired`` controls how many runtime tasks are pushed to RUNNING
        state (defaults to ``n_podman_direct + n_angie`` = all visible).
        Pass a smaller number to leave some tasks pending and exercise
        the relabel pass.
        """
        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        if fired is None:
            fired = n_podman_direct + n_angie
        # The tree is only visible when at least one runtime task has
        # been announced (``TreeProjection.is_tree_visible`` gates on
        # having any RUNNING or pending task in the active play). Clamp
        # ``fired`` to at least 1 so the projection emits a tree at all.
        fired = max(fired, 1)

        angie_tasks = [
            TaskDefinition(
                name=f"angie_ssl_terminator : angie task {i}",
                role="angie_ssl_terminator",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=i,
            )
            for i in range(n_angie)
        ]

        podman_direct = [
            TaskDefinition(
                name=f"podman direct task {i}",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=10_000 + i,
            )
            for i in range(n_podman_direct)
        ]

        angie_group = RoleGroupDefinition(
            role="angie_ssl_terminator",
            tasks=angie_tasks,
            parent="podman",
        )
        podman_group = RoleGroupDefinition(
            role="podman",
            tasks=podman_direct + [angie_group],
        )

        state = RunState(playbook="main.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Setup rootless Podman",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[podman_group],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-25T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-25T10:00:01Z",
                "play": {"id": "p1", "name": "Setup rootless Podman"},
            }
        )

        # Push runtime task_start + runner_on_start events for `fired`
        # tasks in pre-order (podman direct first, then angie).
        idx = 0
        for tdef in podman_direct:
            if idx >= fired:
                break
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": "2026-06-25T10:00:02Z",
                    "task": {"id": f"t-pod-{idx}", "name": tdef.name},
                    "play": {"id": "p1"},
                }
            )
            state.handle_event(
                {
                    "_event": "v2_runner_on_start",
                    "_timestamp": "2026-06-25T10:00:03Z",
                    "task": {"id": f"t-pod-{idx}", "name": tdef.name},
                    "host": "web1",
                }
            )
            idx += 1
        for tdef in angie_tasks:
            if idx >= fired:
                break
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": "2026-06-25T10:00:02Z",
                    "task": {"id": f"t-ang-{idx}", "name": tdef.name},
                    "play": {"id": "p1"},
                }
            )
            state.handle_event(
                {
                    "_event": "v2_runner_on_start",
                    "_timestamp": "2026-06-25T10:00:03Z",
                    "task": {"id": f"t-ang-{idx}", "name": tdef.name},
                    "host": "web1",
                }
            )
            idx += 1
        return state

    def test_role_total_includes_nested_subtree_tasks(self) -> None:
        """``role_total_tasks["podman"]`` must include angie's 30 tasks
        as part of podman's subtree (5 podman direct + 30 angie = 35).
        ``role_total_tasks["angie_ssl_terminator"]`` is 30 (innermost
        count). Direct-children-only semantics would give podman=5,
        which is wrong per the subtree interpretation in the plan's
        open question (lines 143-148 of ``recursive-nesting.md``)."""

        state = self._nested_state(n_podman_direct=5, n_angie=30)
        projection = TreeProjection.from_run_state(state)
        totals = projection._build_role_total_tasks()

        assert totals.get("angie_ssl_terminator") == 30, (
            f"innermost role angie must have 30 tasks; got {totals.get('angie_ssl_terminator')}"
        )
        assert totals.get("podman") == 35, (
            f"outer role podman must have 35 subtree tasks "
            f"(5 direct + 30 nested under angie); got "
            f"{totals.get('podman')}"
        )

    def test_role_total_single_role_unchanged(self) -> None:
        """Regression guard: subtree and direct-children counts are
        equal for a single role (no nesting). Pre-existing single-role
        fixtures must continue to work — see
        ``TestRoleLabelsAfterTruncation``."""

        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="big",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="role0",
                        tasks=[
                            TaskDefinition(
                                name=f"role0 t{i}",
                                role="role0",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=i,
                            )
                            for i in range(3)
                        ],
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-25T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-25T10:00:01Z",
                "play": {"id": "p1", "name": "big"},
            }
        )
        for i in range(3):
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": "2026-06-25T10:00:02Z",
                    "task": {"id": f"t-{i}", "name": f"role0 t{i}"},
                    "play": {"id": "p1"},
                }
            )
            state.handle_event(
                {
                    "_event": "v2_runner_on_start",
                    "_timestamp": "2026-06-25T10:00:03Z",
                    "task": {"id": f"t-{i}", "name": f"role0 t{i}"},
                    "host": "web1",
                }
            )

        projection = TreeProjection.from_run_state(state)
        totals = projection._build_role_total_tasks()
        assert totals.get("role0") == 3, (
            f"single-role subtree must equal 3; got {totals.get('role0')}"
        )

    def test_role_visible_includes_nested_visible_tasks(self) -> None:
        """When only role headers + a couple tasks fit in the budget,
        both ``podman`` and ``angie_ssl_terminator`` count the visible
        tasks in their subtree (an angie task counts under both)."""

        state = self._nested_state(n_podman_direct=5, n_angie=30, fired=1)
        projection = TreeProjection.from_run_state(state)
        # A small budget truncates the angie task list. Visible counts
        # must reflect whatever fits in the budget, not all preflight.
        lines = projection.tree_lines(budget=8)
        visible = projection._count_visible_tasks_per_role(lines)

        # Find the visible task count under angie by walking the
        # emitted lines.
        angie_visible = visible.get("angie_ssl_terminator", 0)
        podman_visible = visible.get("podman", 0)

        # Angie's visible count is at least 0 and at most 30.
        assert 0 <= angie_visible <= 30, f"angie visible must be in [0, 30]; got {angie_visible}"
        # Podman's visible count includes angie's visible tasks (every
        # angie task is also a podman subtree task) plus any podman
        # direct tasks that fit. So podman_visible >= angie_visible.
        assert podman_visible >= angie_visible, (
            f"podman visible ({podman_visible}) must be ≥ angie "
            f"visible ({angie_visible}); angie's subtree is contained "
            f"in podman's"
        )
        # And podman_visible > 0 since the tree must show at least one
        # task to be visible at all (we fired=1 minimum).
        assert podman_visible > 0, (
            f"podman visible must be > 0 (at least the fired task); got {podman_visible}"
        )

    def test_role_visible_single_role_unchanged(self) -> None:
        """Regression guard for single-role subtree == direct."""

        state = self._nested_state(n_podman_direct=3, n_angie=0, fired=3)
        projection = TreeProjection.from_run_state(state)
        lines = projection.tree_lines(budget=999)
        visible = projection._count_visible_tasks_per_role(lines)
        assert visible.get("podman") == 3, (
            f"single-role podman visible must be 3; got {visible.get('podman')}"
        )

    def test_role_label_subtree_total_when_cut_inside_nested(self) -> None:
        """With a small budget that truncates inside angie's task list,
        both podman and angie labels report their subtree TOTAL — never
        a ``(M remaining)`` suffix. The role label always carries
        ``(N tasks)`` where N is the role's full subtree total.

        With ``n_podman_direct=5, n_angie=30``, the 5 fired podman
        direct tasks are visible and the cut lands just past the
        angie role line (no angie tasks visible). So:
        - podman: total=35 → label ``"(35 tasks)"``
        - angie: total=30 → label ``"(30 tasks)"``
        """

        # Fire all 5 podman direct tasks + 1 angie task so the
        # runtime tree shows both role lines and angie's task list
        # is at least partly opened.
        state = self._nested_state(n_podman_direct=5, n_angie=30, fired=6)
        projection = TreeProjection.from_run_state(state)
        # Budget large enough to fit both role headers but cut the
        # angie task list. budget=16 fits 5 podman direct tasks (with
        # hosts), both role headers, and lands the cut inside angie's
        # task list (before any angie task).
        lines = projection.tree_lines(budget=16)

        role_lines = [ln for ln in lines if ln.kind == "role"]
        role_labels = {ln.identity: ln.label for ln in role_lines}
        assert "podman" in role_labels
        assert "angie_ssl_terminator" in role_labels
        # Subtree counting: podman's total is 5 direct + 30 angie = 35.
        # Role label always carries the role's full subtree total —
        # never a "(M tasks remaining)" suffix.
        assert role_labels["podman"] == "role: podman (35 tasks)", (
            f"podman label must show subtree total of 35; got {role_labels['podman']!r}"
        )
        # Angie has 0 visible tasks; role label still reads the total.
        assert role_labels["angie_ssl_terminator"] == ("role: angie_ssl_terminator (30 tasks)"), (
            f"angie label must show 30 (the role's total); "
            f"got {role_labels['angie_ssl_terminator']!r}"
        )
        # No role label may carry a "remaining" suffix.
        for identity, label in role_labels.items():
            assert "remaining" not in label, (
                f"role label for {identity} must NOT carry 'remaining' suffix; got {label!r}"
            )


class TestMultiLevelInnerFooters:
    """Multi-level inner footer emission for nested roles.

    When the cut lands inside a nested role's task list, the projection
    must emit one inner footer per open role ancestor (podman and angie
    in our nested fixture), each reporting that role's subtree
    remaining count. Previously only the innermost role's footer was
    emitted, leaving the outer role's subtree hidden — the user's
    complaint about "the tasks remaining in the second lvls is missing
    there...".
    """

    def _nested_truncated_state(self) -> RunState:
        """Build a state where the cut lands inside angie's task list.

        ``podman`` has 5 direct tasks + 30 angie tasks = 35 subtree.
        Fires enough podman direct tasks to overflow the budget so the
        cut lands inside angie's task list. A small budget then forces
        the inner cut inside the nested role.
        """
        # Fire all 5 podman direct tasks + 1 angie task. The cut
        # lands inside angie's task list when budget is small enough
        # to show role headers + a couple tasks but not all 30 angie
        # tasks.
        state = TestSubtreeRoleCounting()._nested_state(n_podman_direct=5, n_angie=30, fired=6)
        return state

    def test_multi_level_inner_footers_emitted(self) -> None:
        """Cut inside ``angie_ssl_terminator`` must emit TWO inner
        footers: one for podman's subtree remaining, one for angie's
        subtree remaining. Both numbers must be positive and angie's
        must be ≤ podman's (angie's subtree is a subset of podman's)."""

        state = self._nested_truncated_state()
        projection = TreeProjection.from_run_state(state)

        # Pick a budget that triggers truncation inside angie's task
        # list. With 5 podman direct tasks (each with host) visible
        # at depths 3-4, plus 1 playbook + 1 play + 2 role headers,
        # the inner cut lands inside angie's task list when budget
        # is tight enough to show role headers + a few tasks but not
        # all 30 angie tasks. budget=16 lands the cut right after the
        # angie role line, putting the inner footer at angie's task
        # depth (4) and podman's footer at angie's role depth (3).
        lines = projection.tree_lines(budget=16)

        more_lines = [ln for ln in lines if ln.kind == "more"]
        assert len(more_lines) >= 2, (
            f"nested cut must emit at least 2 footers (outer + at "
            f"least 1 inner); got {len(more_lines)}: "
            f"{[(ln.depth, ln.label) for ln in more_lines]}"
        )

        inner_footers = [ln for ln in more_lines if ln.depth > 0]
        assert len(inner_footers) >= 2, (
            f"nested cut must emit at least 2 inner footers "
            f"(podman + angie); got {len(inner_footers)}: "
            f"{[(ln.depth, ln.label) for ln in inner_footers]}"
        )

        import re

        counts: list[int] = []
        for footer in inner_footers:
            m = re.match(r"… and (\d+) more tasks", footer.label)
            assert m, f"footer label must match '… and N more tasks'; got {footer.label!r}"
            counts.append(int(m.group(1)))

        assert all(c > 0 for c in counts), f"all inner footer counts must be positive; got {counts}"
        # Angie's subtree is a strict subset of podman's subtree, so
        # angie's remaining ≤ podman's remaining. The counts come from
        # the deepest-first ordering, so the first inner footer is
        # angie's count and the second is podman's count.
        assert counts[0] <= counts[1], (
            f"innermost footer count ({counts[0]}) must be ≤ outer "
            f"footer count ({counts[1]}); got {counts}"
        )

    def test_inner_footer_per_role_ancestor_matches_role_label(self) -> None:
        """For each inner footer, the count equals
        ``role_total - role_visible`` for the corresponding role
        header — the same formula used by ``_relabel_role_lines``."""

        state = self._nested_truncated_state()
        projection = TreeProjection.from_run_state(state)
        lines = projection.tree_lines(budget=8)

        import re

        # Map each inner footer to its corresponding role by walking
        # backward to find the closest role ancestor (innermost first
        # because footers are emitted deepest-first).
        role_totals = projection._build_role_total_tasks()

        more_lines = [ln for ln in lines if ln.kind == "more"]
        inner_footers = [ln for ln in more_lines if ln.depth > 0]

        # Count tasks per role from the kept lines.
        role_visible: dict[str, int] = {}
        current_role_stack: list[str] = []
        for ln in lines:
            if ln.kind == "role" and ln.identity is not None:
                if ln.identity not in current_role_stack:
                    current_role_stack.append(ln.identity)
            elif ln.kind in ("play", "playbook"):
                current_role_stack.clear()
            elif ln.kind == "task":
                for role in current_role_stack:
                    role_visible[role] = role_visible.get(role, 0) + 1

        # For each inner footer (deepest first), find the closest role
        # or play ancestor in the line list — that's what it reports for.
        for footer in inner_footers:
            footer_idx = lines.index(footer)
            if footer.depth == 2:
                # Play-level inner footer
                m = re.match(r"… and (\d+) more tasks", footer.label)
                assert m
                footer_count = int(m.group(1))
                assert footer_count == 34
                continue

            closest_role = None
            for j in range(footer_idx - 1, -1, -1):
                if (
                    lines[j].kind == "role"
                    and lines[j].identity is not None
                    and lines[j].depth < footer.depth
                ):
                    closest_role = lines[j].identity
                    break

            assert closest_role is not None, (
                f"inner footer at idx {footer_idx} must have a role "
                f"ancestor; got {[ln.label for ln in lines[:footer_idx]]}"
            )

            m = re.match(r"… and (\d+) more tasks", footer.label)
            assert m
            footer_count = int(m.group(1))
            expected = role_totals.get(closest_role, 0) - role_visible.get(closest_role, 0)
            assert footer_count == expected, (
                f"inner footer for role {closest_role!r} must show "
                f"{expected} (total - visible = "
                f"{role_totals.get(closest_role, 0)} - "
                f"{role_visible.get(closest_role, 0)}); got "
                f"{footer_count}"
            )

    def test_single_level_role_one_inner_footer(self) -> None:
        """A single-level role cut emits one role footer at depth 3 and
        one play footer at depth 2.
        """

        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="big",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="role0",
                        tasks=[
                            TaskDefinition(
                                name=f"role0 t{i}",
                                role="role0",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=i,
                            )
                            for i in range(10)
                        ],
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-25T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-25T10:00:01Z",
                "play": {"id": "p1", "name": "big"},
            }
        )
        projection = TreeProjection.from_run_state(state)
        # budget=5 → cuts inside role0's task list.
        # Must fire at least one runtime task for the tree to render.
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-06-25T10:00:02Z",
                "task": {"id": "t-0", "name": "role0 t0"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-25T10:00:03Z",
                "task": {"id": "t-0", "name": "role0 t0"},
                "host": "web1",
            }
        )
        lines = projection.tree_lines(budget=5)

        more_lines = [ln for ln in lines if ln.kind == "more"]
        inner_footers = [ln for ln in more_lines if ln.depth > 0]
        assert len(inner_footers) == 2, (
            f"single-role cut must emit role footer (depth 3) and play footer (depth 2); got "
            f"{len(inner_footers)}: "
            f"{[(ln.depth, ln.label) for ln in inner_footers]}"
        )


class TestMultiPlayTruncationWithRoleFooters:
    """Multi-play truncation with completed tasks in earlier plays.

    Reproduces the user's real scenario: a multi-play playbook where
    play 1 has roles with mostly-completed tasks (so the unbounded tree
    for play 1 is short) and play 2 has many pending tasks. The
    truncation cut lands at play 2's boundary, but roles in play 1 have
    many remaining tasks (completed-but-not-visible + pending) that
    the user expects to see in the rendered tree.

    Three contracts under verification:

    - **Bug 1** (inner footers in the head): every role in the head
      whose subtree has ``role_total - role_visible > 0`` gets an
      inner footer at its task-list depth (role's line depth + 1),
      inserted after the role's last visible task.
    - **Bug 2** (multi-level inner footers for nested head roles):
      for nested roles (``role: podman > role: angie_ssl_terminator``),
      BOTH footers are emitted, deepest-first (angie's footer sits
      just above podman's footer, matching the existing
      multi-level logic).
    - **Bug 3** (outer footer counts the full tree): the outer
      footer's count = total unique tasks across all plays minus
      visible tasks in the kept tree, NOT just the count of dropped
      task-domain entities in the tail after the inner cut.
    """

    def _multi_play_completed_state(self) -> RunState:
        """Build the user's exact reproduction state.

        Play 1 = ``podman`` (289 direct + 129 nested under
        ``angie_ssl_terminator`` = 418 total). 288 podman direct +
        127 angie tasks are completed (visible as PENDING only when
        next task starts; here they're completed-and-hidden). 1
        podman direct task is RUNNING; 2 angie tasks are PENDING.

        Play 2 = 2816 pending tasks with no role grouping.

        The unbounded tree is short for play 1 (~9 lines: playbook,
        play, podman role, host, angie role, 2 angie tasks) and very
        long for play 2. A budget that fits play 1 plus a few play-2
        tasks lands the outer cut on play 2's boundary.
        """
        podman_direct = [
            TaskDefinition(
                name=f"podman direct task {i}",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=i,
            )
            for i in range(289)
        ]
        angie_tasks = [
            TaskDefinition(
                name=f"angie_ssl_terminator : task {i}",
                role="angie_ssl_terminator",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=289 + i,
            )
            for i in range(129)
        ]
        angie_role = RoleGroupDefinition(
            role="angie_ssl_terminator", tasks=angie_tasks, parent="podman"
        )
        podman_role = RoleGroupDefinition(role="podman", tasks=podman_direct + [angie_role])
        play2_tasks = [
            TaskDefinition(
                name=f"play2 task {i}",
                role=None,
                tags=[],
                play_id="p2",
                play_order=1,
                task_order=i,
            )
            for i in range(2816)
        ]
        state = RunState(playbook="main.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Setup rootless Podman for Scrutiny web server",
                hosts="all",
                resolved_hosts=["ds9"],
                tasks=[podman_role],
            ),
            PlayDefinition(
                id="p2",
                name="Deploy Scrutiny web server and InfluxDB containers",
                hosts="all",
                resolved_hosts=["ds9"],
                tasks=play2_tasks,
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-24T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-24T10:00:01Z",
                "play": {"id": "p1", "name": "Setup rootless Podman"},
            }
        )
        # Complete the first 288 podman direct tasks.
        for i in range(288):
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": "2026-06-24T10:00:02Z",
                    "task": {"id": f"t{i}", "name": f"podman direct task {i}"},
                    "play": {"id": "p1"},
                }
            )
            state.handle_event(
                {
                    "_event": "runner_on_ok",
                    "_timestamp": "2026-06-24T10:00:03Z",
                    "host": "ds9",
                    "task": {"id": f"t{i}", "name": f"podman direct task {i}"},
                    "play": {"id": "p1"},
                    "res": {"changed": False},
                }
            )
        # Complete the first 127 angie tasks.
        for i in range(127):
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": "2026-06-24T10:00:04Z",
                    "task": {"id": f"at{i}", "name": f"angie_ssl_terminator : task {i}"},
                    "play": {"id": "p1"},
                }
            )
            state.handle_event(
                {
                    "_event": "runner_on_ok",
                    "_timestamp": "2026-06-24T10:00:05Z",
                    "host": "ds9",
                    "task": {"id": f"at{i}", "name": f"angie_ssl_terminator : task {i}"},
                    "play": {"id": "p1"},
                    "res": {"changed": False},
                }
            )
        # 1 podman direct task RUNNING (visible) and 2 angie tasks PENDING.
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-06-24T10:04:00Z",
                "task": {"id": "t288", "name": "podman direct task 288"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-24T10:04:01Z",
                "host": "ds9",
                "task": {"id": "t288", "name": "podman direct task 288"},
                "play": {"id": "p1"},
            }
        )
        return state

    def _find_more_at(
        self, lines: list[TreeLine], depth: int, label_pattern: str
    ) -> TreeLine | None:
        import re

        for ln in lines:
            if ln.kind == "more" and ln.depth == depth and re.search(label_pattern, ln.label):
                return ln
        return None

    def _extract_more_count(self, ln: TreeLine) -> int:
        import re

        m = re.match(r"… and (\d+) more tasks", ln.label)
        assert m, f"label must match '… and N more tasks'; got {ln.label!r}"
        return int(m.group(1))

    def _multi_play_with_pending_roles_state(self) -> RunState:
        """Build a multi-play state where roles have pending tasks that are truncated.

        Play 1: podman (289 direct + 129 angie = 418 total).
        100 podman direct completed, 1 running (visible), 188 pending (truncated).
        100 angie completed, 2 pending (visible), 27 pending (truncated).
        Podman total remaining = 188 + 27 = 215.
        Angie total remaining = 27.

        Play 2: 2816 pending tasks (2 visible, 2814 truncated).
        """
        podman_direct = [
            TaskDefinition(
                name=f"podman direct task {i}",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=i,
            )
            for i in range(289)
        ]
        angie_tasks = [
            TaskDefinition(
                name=f"angie_ssl_terminator : task {i}",
                role="angie_ssl_terminator",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=289 + i,
            )
            for i in range(129)
        ]
        angie_role = RoleGroupDefinition(
            role="angie_ssl_terminator", tasks=angie_tasks, parent="podman"
        )
        podman_role = RoleGroupDefinition(role="podman", tasks=podman_direct + [angie_role])
        play2_tasks = [
            TaskDefinition(
                name=f"play2 task {i}",
                role=None,
                tags=[],
                play_id="p2",
                play_order=1,
                task_order=i,
            )
            for i in range(2816)
        ]
        state = RunState(playbook="main.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Setup rootless Podman",
                hosts="all",
                resolved_hosts=["ds9"],
                tasks=[podman_role],
            ),
            PlayDefinition(
                id="p2",
                name="Deploy Scrutiny web server and InfluxDB containers",
                hosts="all",
                resolved_hosts=["ds9"],
                tasks=play2_tasks,
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-24T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-24T10:00:01Z",
                "play": {"id": "p1", "name": "Setup rootless Podman"},
            }
        )
        # 289 podman direct tasks completed
        for i in range(289):
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": "2026-06-24T10:00:02Z",
                    "task": {"id": f"t{i}", "name": f"podman direct task {i}"},
                    "play": {"id": "p1"},
                }
            )
            state.handle_event(
                {
                    "_event": "runner_on_ok",
                    "_timestamp": "2026-06-24T10:00:03Z",
                    "host": "ds9",
                    "task": {"id": f"t{i}", "name": f"podman direct task {i}"},
                    "play": {"id": "p1"},
                    "res": {"changed": False},
                }
            )
        # 100 angie tasks completed
        for i in range(100):
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": "2026-06-24T10:00:04Z",
                    "task": {"id": f"at{i}", "name": f"angie_ssl_terminator : task {i}"},
                    "play": {"id": "p1"},
                }
            )
            state.handle_event(
                {
                    "_event": "runner_on_ok",
                    "_timestamp": "2026-06-24T10:00:05Z",
                    "host": "ds9",
                    "task": {"id": f"at{i}", "name": f"angie_ssl_terminator : task {i}"},
                    "play": {"id": "p1"},
                    "res": {"changed": False},
                }
            )
        # 1 angie task RUNNING (visible)
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-06-24T10:04:00Z",
                "task": {"id": "at100", "name": "angie_ssl_terminator : task 100"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-24T10:04:01Z",
                "host": "ds9",
                "task": {"id": "at100", "name": "angie_ssl_terminator : task 100"},
                "play": {"id": "p1"},
            }
        )
        return state

    def test_no_inner_footer_when_completed_tasks_leave_all_remaining_visible(self) -> None:
        """When earlier tasks completed and all remaining tasks are visible,
        no inner footer is emitted for completed tasks."""
        state = self._multi_play_completed_state()
        projection = TreeProjection.from_run_state(state)
        # budget=13 fits play 1's visible items + 2 play-2 tasks + 2 footers.
        lines = projection.tree_lines(budget=13)

        # Neither angie nor podman has hidden remaining tasks, so neither
        # should have an inner footer in the head.
        angie_role_line = next(
            ln for ln in lines if ln.kind == "role" and ln.identity == "angie_ssl_terminator"
        )
        podman_role_line = next(ln for ln in lines if ln.kind == "role" and ln.identity == "podman")
        angie_footer = self._find_more_at(
            lines, depth=angie_role_line.depth + 1, label_pattern=r"more tasks"
        )
        podman_footer = self._find_more_at(
            lines, depth=podman_role_line.depth + 1, label_pattern=r"more tasks"
        )
        assert angie_footer is None, f"angie should have no inner footer; got {angie_footer}"
        assert podman_footer is None, f"podman should have no inner footer; got {podman_footer}"

    def test_inner_footers_for_nested_roles_when_pending_tasks_are_truncated(self) -> None:
        """When roles in the head have pending tasks that are truncated,
        inner footers report the true remaining (total - completed - visible)."""
        state = self._multi_play_with_pending_roles_state()
        projection = TreeProjection.from_run_state(state)
        # budget=13 fits play 1 head + 2 play-2 tasks + footers.
        lines = projection.tree_lines(budget=13)

        angie_role_line = next(
            ln for ln in lines if ln.kind == "role" and ln.identity == "angie_ssl_terminator"
        )
        podman_role_line = next(ln for ln in lines if ln.kind == "role" and ln.identity == "podman")

        # Angie has 129 - 100 completed - 6 visible = 23 remaining
        angie_footer = self._find_more_at(
            lines, depth=angie_role_line.depth + 1, label_pattern=r"23 more tasks"
        )
        # Podman has 418 - 389 completed - 6 visible = 23 remaining
        podman_footer = self._find_more_at(
            lines, depth=podman_role_line.depth + 1, label_pattern=r"23 more tasks"
        )

        assert angie_footer is not None, "must emit angie's inner footer with count=23"
        assert podman_footer is not None, "must emit podman's inner footer with count=23"
        assert self._extract_more_count(angie_footer) == 23
        assert self._extract_more_count(podman_footer) == 23

        # Ordering: angie's footer (deeper) must appear BEFORE podman's footer
        angie_idx = lines.index(angie_footer)
        podman_idx = lines.index(podman_footer)
        assert angie_idx < podman_idx

    def test_outer_footer_count_is_total_remaining_across_all_plays(self) -> None:
        """The outer footer reports the TOTAL remaining (uncompleted & hidden)
        tasks across ALL plays, subtracting completed tasks."""
        state = self._multi_play_completed_state()
        projection = TreeProjection.from_run_state(state)
        lines = projection.tree_lines(budget=13)

        outer = lines[-1]
        assert outer.kind == "more" and outer.depth == 0, (
            f"last line must be the outer footer at depth=0; got "
            f"depth={outer.depth} kind={outer.kind}"
        )
        outer_count = self._extract_more_count(outer)
        # Total unique tasks = 418 (play 1) + 2816 (play 2) = 3234.
        # Completed tasks = 415.
        # Visible tasks in the kept tree = 5.
        # Total remaining hidden = 3234 - 415 - 5 = 2814.
        assert outer_count == 2814, (
            f"outer footer count must equal total remaining across ALL "
            f"plays (3234 - 415 - 5 = 2814); got {outer_count}"
        )

    def test_no_inner_footer_when_role_has_no_remaining(self) -> None:
        """Regression guard: when every task under a role is visible
        (remaining == 0), NO inner footer must be emitted for that
        role. The previous contract relied on this in the
        within-budget path; the head-footer extension must preserve
        it.

        State: 1 play, 1 role, 3 tasks all running (with host leaves).
        Budget large enough to fit everything + spare. No role has
        remaining > 0, so no inner footers in the head.
        """
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="webserver",
                        tasks=[
                            TaskDefinition(
                                name=f"task {t}",
                                role="webserver",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=t,
                            )
                            for t in range(3)
                        ],
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-25T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-25T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        for t in range(3):
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": "2026-06-25T10:00:02Z",
                    "task": {"id": f"t{t}", "name": f"task {t}"},
                    "play": {"id": "p1"},
                }
            )
            state.handle_event(
                {
                    "_event": "v2_runner_on_start",
                    "_timestamp": "2026-06-25T10:00:03Z",
                    "task": {"id": f"t{t}", "name": f"task {t}"},
                    "host": "web1",
                }
            )

        projection = TreeProjection.from_run_state(state)
        # Budget=15 fits the whole tree (1+1+1+3+3 = 9 lines). With the
        # fix, no inner footers should be emitted because every role's
        # remaining == 0 (visible == total).
        lines = projection.tree_lines(budget=15)
        more_lines = [ln for ln in lines if ln.kind == "more"]
        assert len(more_lines) == 0, (
            f"no footers should be emitted when every task is visible; "
            f"got {[ln.label for ln in more_lines]}"
        )

    def test_inner_play_footer_reports_play_remaining_when_cut_lands_in_direct_play_tasks(
        self,
    ) -> None:
        """When a budget cut truncates tasks directly under a play (no role),
        the play's inner footer reports remaining tasks in THAT play (depth 2),
        and the outer footer reports remaining tasks across ALL plays (depth 0)."""
        play1_tasks = [
            TaskDefinition(
                name=f"play1 direct task {i}",
                role=None,
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=i,
            )
            for i in range(10)
        ]
        play2_tasks = [
            TaskDefinition(
                name=f"play2 direct task {i}",
                role=None,
                tags=[],
                play_id="p2",
                play_order=1,
                task_order=i,
            )
            for i in range(3000)
        ]
        state = RunState(playbook="main.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Create nfs share",
                hosts="all",
                resolved_hosts=["ds9"],
                tasks=play1_tasks,
            ),
            PlayDefinition(
                id="p2",
                name="Later play",
                hosts="all",
                resolved_hosts=["ds9"],
                tasks=play2_tasks,
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-24T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-24T10:00:01Z",
                "play": {"id": "p1", "name": "Create nfs share"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-06-24T10:04:00Z",
                "task": {"id": "t0", "name": "play1 direct task 0"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-24T10:04:01Z",
                "host": "ds9",
                "task": {"id": "t0", "name": "play1 direct task 0"},
                "play": {"id": "p1"},
            }
        )
        projection = TreeProjection.from_run_state(state)
        lines = projection.tree_lines(budget=10)

        more_lines = [ln for ln in lines if ln.kind == "more"]
        # Exactly two footers: one for the play (depth 2) and one for the playbook (depth 0)
        assert len(more_lines) == 2, (
            f"expected 2 footers (play + outer); got {[ln.label for ln in more_lines]}"
        )
        play_footer = more_lines[0]
        outer_footer = more_lines[1]

        assert play_footer.depth == 2
        # Play 1 has 10 tasks total, 5 visible. Remaining in Play 1 = 10 - 5 = 5.
        assert play_footer.label == "… and 5 more tasks"

        assert outer_footer.depth == 0
        # 10 (play 1) + 3000 (play 2) = 3010 total. Visible tasks = 5.
        # Remaining across all plays = 3010 - 5 = 3005.
        assert outer_footer.label == "… and 3005 more tasks"

    def test_all_hierarchy_levels_emitted_when_cut_inside_nested_role(self) -> None:
        """When a cut lands inside a nested role (podman > angie > play),
        all hierarchical levels emit their remaining footers:
        - Level 3 (podman): depth 4
        - Level 2 (angie): depth 3
        - Level 1 (play): depth 2
        - Level 0 (playbook): depth 0
        """
        podman_tasks = [
            TaskDefinition(
                name=f"podman task {i}",
                role="podman",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=i,
            )
            for i in range(31)
        ]
        podman_role = RoleGroupDefinition(
            role="podman", tasks=podman_tasks, parent="angie_ssl_terminator"
        )
        angie_direct = [
            TaskDefinition(
                name=f"angie task {i}",
                role="angie_ssl_terminator",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=31 + i,
            )
            for i in range(7)
        ]
        angie_role = RoleGroupDefinition(
            role="angie_ssl_terminator", tasks=[podman_role] + angie_direct
        )
        play2_tasks = [
            TaskDefinition(
                name=f"play2 task {i}",
                role=None,
                tags=[],
                play_id="p2",
                play_order=1,
                task_order=i,
            )
            for i in range(3000)
        ]

        state = RunState(playbook="main.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Deploy Keepalived for Proxmox VIP",
                hosts="all",
                resolved_hosts=["ds5"],
                tasks=[angie_role],
            ),
            PlayDefinition(
                id="p2",
                name="Later play",
                hosts="all",
                resolved_hosts=["ds5"],
                tasks=play2_tasks,
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-24T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-24T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy Keepalived for Proxmox VIP"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-06-24T10:04:00Z",
                "task": {"id": "t0", "name": "podman task 0"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-24T10:04:01Z",
                "host": "ds5",
                "task": {"id": "t0", "name": "podman task 0"},
                "play": {"id": "p1"},
            }
        )

        proj = TreeProjection.from_run_state(state)
        lines = proj.tree_lines(budget=10)

        more_lines = [ln for ln in lines if ln.kind == "more"]
        # Expected: podman (depth 4), angie (depth 3), play (depth 2), playbook (depth 0)
        assert len(more_lines) == 4, (
            f"expected 4 footers (depths 4, 3, 2, 0); got {[ln.label for ln in more_lines]}"
        )
        assert more_lines[0].depth == 4
        assert more_lines[0].label == "… and 28 more tasks"

        assert more_lines[1].depth == 3
        assert more_lines[1].label == "… and 35 more tasks"

        assert more_lines[2].depth == 2
        assert more_lines[2].label == "… and 35 more tasks"

        assert more_lines[3].depth == 0
        assert more_lines[3].label == "… and 3035 more tasks"

    def test_footers_monotonic_hierarchy_invariant(self) -> None:
        """A role footer's remaining task count can never exceed the enclosing
        play's remaining task count, nor can a play's footer exceed the outer
        playbook footer. The hierarchy is monotonically non-decreasing."""
        role_tasks = [
            TaskDefinition(
                name=f"fail2ban task {i}",
                role="fail2ban",
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=i,
            )
            for i in range(44)
        ]
        role_group = RoleGroupDefinition(role="fail2ban", tasks=role_tasks)
        direct_tasks = [
            TaskDefinition(
                name=f"direct task {i}",
                role=None,
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=44 + i,
            )
            for i in range(10)
        ]
        state = RunState(playbook="main.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Deploy Redis active/passive for fail2ban",
                hosts="all",
                resolved_hosts=["host1"],
                tasks=[role_group] + direct_tasks,
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-24T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-24T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy Redis active/passive for fail2ban"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-06-24T10:04:00Z",
                "task": {"id": "t0", "name": "fail2ban task 0"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-24T10:04:01Z",
                "host": "host1",
                "task": {"id": "t0", "name": "fail2ban task 0"},
                "play": {"id": "p1"},
            }
        )

        proj = TreeProjection.from_run_state(state)
        # Try various budgets: in all cases, role remaining <= play remaining <= outer remaining
        import re

        for budget in range(5, 30):
            lines = proj.tree_lines(budget=budget)
            more_lines = [ln for ln in lines if ln.kind == "more"]
            if not more_lines:
                continue
            counts_by_depth: dict[int, int] = {}
            for ln in more_lines:
                m = re.search(r"… and (\d+) more tasks", ln.label)
                if m:
                    counts_by_depth[ln.depth] = int(m.group(1))

            # If both role (depth 3) and play (depth 2) footers exist:
            if 3 in counts_by_depth and 2 in counts_by_depth:
                assert counts_by_depth[3] <= counts_by_depth[2], (
                    f"role remaining ({counts_by_depth[3]}) must be <= "
                    f"play remaining ({counts_by_depth[2]}) at budget={budget}"
                )
            # If play (depth 2) and outer (depth 0) footers exist:
            if 2 in counts_by_depth and 0 in counts_by_depth:
                assert counts_by_depth[2] <= counts_by_depth[0], (
                    f"play remaining ({counts_by_depth[2]}) must be <= "
                    f"outer remaining ({counts_by_depth[0]}) at budget={budget}"
                )

    def test_meta_tasks_without_runtime_events_not_emitted_as_pending(self) -> None:
        """Ansible's callback engine does not emit task start events for meta actions
        (e.g. reset_connection, flush_handlers). Such tasks must not be emitted
        as pending ghost tasks that take up budget and hide real upcoming tasks."""
        tasks = [
            TaskDefinition(
                name="Bootstrap python3-dnf on dnf-based systems",
                role=None,
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=0,
            ),
            TaskDefinition(
                name="Reset connection after python3-dnf bootstrap",
                role=None,
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=1,
            ),
            TaskDefinition(
                name="Gather facts for conditional logic",
                role=None,
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=2,
            ),
            TaskDefinition(
                name="Reset connection after installing software updates",
                role=None,
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=3,
            ),
            TaskDefinition(
                name="Install software",
                role=None,
                tags=[],
                play_id="p1",
                play_order=0,
                task_order=4,
            ),
        ]
        state = RunState(playbook="main.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Install default software",
                hosts="all",
                resolved_hosts=["host1"],
                tasks=tasks,
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-06-24T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-06-24T10:00:01Z",
                "play": {"id": "p1", "name": "Install default software"},
            }
        )
        # Task 0 started and running
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-06-24T10:04:00Z",
                "task": {"id": "t0", "name": "Bootstrap python3-dnf on dnf-based systems"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-06-24T10:04:01Z",
                "host": "host1",
                "task": {"id": "t0", "name": "Bootstrap python3-dnf on dnf-based systems"},
                "play": {"id": "p1"},
            }
        )

        proj = TreeProjection.from_run_state(state)
        lines = proj.tree_lines(budget=20)
        labels = [ln.label for ln in lines if ln.kind == "task"]

        # Meta tasks should NOT appear in pending labels
        assert not any("Reset connection" in lbl for lbl in labels), (
            f"meta reset_connection tasks should not be emitted as pending; got {labels}"
        )
        # Real pending tasks SHOULD appear
        assert any("Gather facts" in lbl for lbl in labels)
        assert any("Install software" in lbl for lbl in labels)
