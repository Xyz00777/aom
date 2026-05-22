"""Regression tests for tree projection bugs:

1. _classify must treat RUNNING tasks with empty hosts as "running"
   (not "pending"), so the ◐ icon appears and host-leaf space is reserved.

2. Runtime role labels must show total task count from definitions
   (not shrinking as tasks complete).
"""

from __future__ import annotations

from ansible_aom.core.models import (
    PlayDefinition,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
)
from ansible_aom.core.tree import TreeProjection


class TestClassifyRunningWithEmptyHosts:
    """Regression guard: a task with RUNNING status but no host entries yet
    (e.g. between task_start and the first runner_on_start event under free
    strategy, or linear strategy without preflight resolved_hosts) must be
    classified as "running" — the ◐ icon and host-leaf reservation depend on it.

    Previously _classify returned "pending" when runtime.hosts was empty,
    causing the tree to show □ for a task that was actually RUNNING.
    """

    def _running_task_no_hosts_state(self) -> RunState:
        """Build a state where a task has status=RUNNING but hosts={} —
        simulates v2_playbook_on_task_start without any runner events yet."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="webservers",
                resolved_hosts=["web1"],
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
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-1", "name": "deploy"},
            }
        )
        # task_start creates the task with RUNNING status but under free
        # strategy, no hosts are populated yet (no v2_runner_on_start).
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "play-1"},
            }
        )
        return state

    def test_running_task_with_empty_hosts_shows_running_icon(self):
        """A task that has started (status=RUNNING) but has no host events
        yet must appear with RUNNING status in the tree, not PENDING."""
        state = self._running_task_no_hosts_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        task_lines = [ln for ln in lines if ln.kind == "task"]
        assert len(task_lines) >= 1, f"expected at least one task line, got {lines}"
        task = task_lines[0]
        assert task.status == Status.RUNNING, (
            f"task with RUNNING status and empty hosts should show as RUNNING, got {task.status}"
        )

    def test_running_task_with_empty_hosts_appears_in_tree(self):
        """Even without host entries, the task name should be visible."""
        state = self._running_task_no_hosts_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        task_names = [ln.label.split("  ")[0] for ln in lines if ln.kind == "task"]
        assert "Install nginx" in task_names, (
            f"running task with empty hosts should appear in tree, got {task_names}"
        )


class TestRuntimeRoleLabelTaskCountFromDefinitions:
    """Regression guard: role labels in the runtime play must show the
    total task count from definitions (not just the count of running+pending
    tasks). Previously _emit_runtime_play counted only visible items, so
    as tasks completed, the role label count would shrink — misleading the
    user about the role's total work.
    """

    def _multi_task_role_with_completed_task(self) -> RunState:
        """Build a state where one role task is completed and another is
        running. The role label must show the total task count (2), not
        just the running count (1)."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="webservers",
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
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-1", "name": "deploy"},
            }
        )
        # Task 1 completes
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "play-1"},
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
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        # Task 2 starts running
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:06Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "play": {"id": "play-1"},
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
        return state

    def test_role_label_shows_total_task_count_not_running_count(self):
        """When a role has 2 tasks and 1 is completed, the runtime role
        label should still show '(2 tasks)', not '(1 task)'."""
        state = self._multi_task_role_with_completed_task()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        role_lines = [ln for ln in lines if ln.kind == "role"]
        assert len(role_lines) >= 1, f"expected a role line, got {lines}"
        role_label = role_lines[0].label
        assert "(2 tasks)" in role_label, (
            f"role label should show total task count from definitions, got: {role_label}"
        )

    def test_role_label_count_with_all_tasks_completed(self):
        """When all role tasks are completed (none running, none pending),
        the runtime tree drops completed tasks. If the role line still
        appears (e.g. mixed with pending tasks from another role), the
        count must still reflect the definition total."""
        state = self._multi_task_role_with_completed_task()
        # Complete the second task too
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:09Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        role_lines = [ln for ln in lines if ln.kind == "role"]
        # Either there are no role lines (all tasks completed, tree
        # degrades) or the role label shows the full count.
        if role_lines:
            assert "(2 tasks)" in role_lines[0].label, (
                f"if role line appears, it must show total task count, got: {role_lines[0].label}"
            )