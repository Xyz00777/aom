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
        # Finish web1 — when at least one host is still RUNNING
        # (web2), both hosts appear under the task. web1 shows ● (OK),
        # web2 shows ◐ (RUNNING).
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
        host_labels = [ln.label for ln in host_lines]
        assert host_labels == ["web1", "web2"]
        web1_hl = next(hl for hl in host_lines if hl.label == "web1")
        web2_hl = next(hl for hl in host_lines if hl.label == "web2")
        assert web1_hl.status == Status.OK
        assert web2_hl.status == Status.RUNNING

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
        assert "(3 tasks)" in role_line.label

        task_lines = [ln for ln in lines if ln.kind == "task"]
        task_labels = [ln.label.split("  ")[0] for ln in task_lines]
        assert task_labels[:3] == [
            "theforeman.operations.installer : Install installer",
            "theforeman.operations.installer : Poll async status",
            "theforeman.operations.installer : Configure installer",
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
        assert projection._task_role("Install nginx") == "webserver"

        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-24T10:00:03Z",
                "task": {"id": "t2", "name": "Poll async status"},
                "play": {"id": "p1"},
            }
        )

        assert projection._task_role("Poll async status") == "webserver"
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
        # + 5 hosts = 9 lines. Budget 4 fits the structure + task but no hosts;
        # budget 5 fits one host as well (truncate-from-end preserves the
        # active play's depth over upcoming breadth).
        state = self._many_tasks_state(n_roles=1, tasks_per_role=1, hosts_per_task=5)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=4)
        kinds = [ln.kind for ln in lines]
        assert "task" in kinds
        assert "host" not in kinds
        assert len(lines) <= 4

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

    def test_collapsed_role_summary_format(self):
        # Force collapse: many hosts so truncation still overflows after
        # dropping hosts. 4 roles × 1 task × 10 hosts = 47 unbounded lines.
        # After dropping hosts (stage b): 7 lines. With budget 5, roles
        # get collapsed (stage c).
        state = self._many_tasks_state(n_roles=4, tasks_per_role=1, hosts_per_task=10)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=5)
        role_summary_lines = [
            ln for ln in lines if ln.kind == "role" and "tasks running" in ln.label
        ]
        # Format check: "role: roleN  (M tasks running on K hosts)"
        for ln in role_summary_lines:
            assert ln.label.startswith("role: role")
            assert "tasks running on" in ln.label
            assert "hosts)" in ln.label


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
                    TaskDefinition(name="T1", role=None, tags=[], play_id="pA", play_order=0, task_order=0),
                    TaskDefinition(name="T2", role=None, tags=[], play_id="pA", play_order=0, task_order=1),
                ],
            ),
            PlayDefinition(
                id="pB",
                name="Play B",
                hosts="dbservers",
                resolved_hosts=["db1"],
                tasks=[
                    TaskDefinition(name="T3", role=None, tags=[], play_id="pB", play_order=1, task_order=0),
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
        assert play_names == ["Play A", "Play B"], (
            f"both plays should appear; got {play_names!r}"
        )

        task_lines = [ln for ln in p.tree_lines(budget=25) if ln.kind == "task"]
        task_names = [ln.label.split("  ")[0] for ln in task_lines]
        # T1 is completed and should NOT appear.
        # T2 is pending and MUST appear (this was the bug).
        # T3 is running and should appear.
        assert "T1" not in task_names, f"completed task T1 should not appear, got {task_names!r}"
        assert "T2" in task_names, (
            f"pending task T2 should appear (regression: it was being skipped "
            f"because Play A had T1 completed and no running tasks), got {task_names!r}"
        )
        assert "T3" in task_names, f"running task T3 should appear, got {task_names!r}"
