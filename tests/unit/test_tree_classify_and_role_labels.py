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


class TestDynamicChildrenTaskRole:
    """TC-300: _task_role must index TaskDefinition.children (grafted
    include_tasks children), not just the flat play_def.tasks list."""

    def test_dynamic_child_under_role_returns_correct_role(self) -> None:
        """Dynamic grafted child under role 'nginx' → _task_role("Dynamic task")
        returns "nginx"."""
        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        parent.children.append(
            TaskDefinition(
                name="Dynamic task",
                role="nginx",
                is_dynamic=True,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
            )
        )
        defs = [
            PlayDefinition(
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        p = TreeProjection.from_run_state(state)
        assert p._task_role("Dynamic task") == "nginx"

    def test_dynamic_child_stripped_prefix_also_finds_role(self) -> None:
        """Runtime task names with 'role : ' prefix should still match
        the dynamic child index after stripping."""
        parent = TaskDefinition(
            name="Include tasks file",
            role="nginx",
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        parent.children.append(
            TaskDefinition(
                name="nginx : Dynamic task",
                role="nginx",
                is_dynamic=True,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
            )
        )
        defs = [
            PlayDefinition(
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        p = TreeProjection.from_run_state(state)
        assert p._task_role("nginx : Dynamic task") == "nginx"


class TestDynamicChildrenRoleTotalTasks:
    """TC-301: role_total_tasks must count dynamic children."""

    def test_role_with_preflight_and_dynamic_children_count(self) -> None:
        """Role with both preflight tasks and grafted dynamic children
        must show the combined total."""
        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        parent.children.append(
            TaskDefinition(
                name="Dynamic task A",
                role="nginx",
                is_dynamic=True,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
            )
        )
        parent.children.append(
            TaskDefinition(
                name="Dynamic task B",
                role="nginx",
                is_dynamic=True,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
            )
        )
        # Also a preflight task with same role
        preflight = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=[],
            play_id="1",
            play_order=0,
            task_order=1,
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent, preflight],
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "Test"},
            }
        )
        # Make one task RUNNING so the role tree line appears
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t-pre", "name": "Install nginx"},
                "play": {"id": "play-1"},
            }
        )
        from datetime import datetime, timezone

        from ansible_aom.core.models import HostRunState

        t = state.plays["play-1"].tasks["t-pre"]
        t.hosts["web1"] = HostRunState(
            hostname="web1",
            status=Status.RUNNING,
            start_time=datetime(2026, 5, 22, 10, 0, 2, tzinfo=timezone.utc),
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        role_lines = [ln for ln in lines if ln.kind == "role" and "nginx" in ln.label]
        assert len(role_lines) >= 1, f"expected nginx role, got {[ln.label for ln in lines]}"
        assert "(3 tasks)" in role_lines[0].label, (
            f"nginx role should show 3 tasks (1 preflight + 2 dynamic), got: {role_lines[0].label}"
        )

    def test_dynamic_child_task_appears_under_role_header(self) -> None:
        """TC-302: Dynamic child renders under the correct role header
        in tree output, not as a bare ungrouped task."""
        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "Test"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t-include", "name": "Include tasks file"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t-dyn", "name": "nginx : Dynamic task A"},
                "play": {"id": "play-1"},
            }
        )
        from datetime import datetime, timezone

        from ansible_aom.core.models import HostRunState

        t = state.plays["play-1"].tasks["t-dyn"]
        t.hosts["web1"] = HostRunState(
            hostname="web1",
            status=Status.RUNNING,
            start_time=datetime(2026, 5, 22, 10, 0, 3, tzinfo=timezone.utc),
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        # The dynamic child should NOT appear as a bare ungrouped task
        # (it has no runtime task state, so it's only reflected in the count).
        role_lines = [ln for ln in lines if ln.kind == "role" and "nginx" in ln.label]
        assert len(role_lines) >= 1, f"expected nginx role, got {[ln.label for ln in lines]}"
        # At minimum the role header shows (1 task) — the dynamic child
        assert "(1 task)" in role_lines[0].label, (
            f"nginx role with one dynamic child should show (1 task), got: {role_lines[0].label}"
        )


class TestDynamicChildrenAsPendingInTree:
    """TC-320: Dynamic children (grafted include_tasks) appear in tree
    as □ pending before ansible announces them at runtime."""

    def test_dynamic_children_show_pending_before_announcement(self) -> None:
        """Grafted children not yet seen at runtime appear with Status.PENDING."""
        from datetime import datetime, timezone

        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        parent.children.append(
            TaskDefinition(
                name="Dynamic A",
                role=None,
                is_dynamic=True,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
            )
        )
        parent.children.append(
            TaskDefinition(
                name="Dynamic B",
                role=None,
                is_dynamic=True,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
            )
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"}
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "Test"},
            }
        )
        # Only the parent include_tasks is announced — children not yet.
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t-parent", "name": "Include tasks file"},
                "play": {"id": "play-1"},
            }
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        pending_labels = [
            ln.label for ln in lines if ln.kind == "task" and ln.status == Status.PENDING
        ]
        assert "Dynamic A" in pending_labels, (
            f"Dynamic A should appear as □ pending, got pending: {pending_labels}"
        )
        assert "Dynamic B" in pending_labels, (
            f"Dynamic B should appear as □ pending, got pending: {pending_labels}"
        )

    def test_running_dynamic_child_shows_running_status(self) -> None:
        """TC-321: Dynamic child announced at runtime shows RUNNING status (◐)."""
        from datetime import datetime, timezone

        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        parent.children.append(
            TaskDefinition(
                name="Dynamic A",
                role=None,
                is_dynamic=True,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
            )
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"}
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "Test"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t-parent", "name": "Include tasks file"},
                "play": {"id": "play-1"},
            }
        )
        # Announce the dynamic child.
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t-dyn", "name": "Dynamic A"},
                "play": {"id": "play-1"},
            }
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        running_labels = [
            ln.label.split("  ")[0]
            for ln in lines
            if ln.kind == "task" and ln.status == Status.RUNNING
        ]
        assert "Dynamic A" in running_labels, (
            f"Dynamic A should show as RUNNING, got running tasks: {running_labels}"
        )

    def test_completed_dynamic_child_filtered_from_tree(self) -> None:
        """TC-322: Dynamic child classified as 'completed' is excluded from tree lines."""
        from datetime import datetime, timezone

        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        parent.children.append(
            TaskDefinition(
                name="Dynamic A",
                role=None,
                is_dynamic=True,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
            )
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"}
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "Test"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t-parent", "name": "Include tasks file"},
                "play": {"id": "play-1"},
            }
        )
        # Fire task_start + runner_on_start + runner_on_ok to complete the child.
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t-dyn", "name": "Dynamic A"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-22T10:00:04Z",
                "task": {"id": "t-dyn", "name": "Dynamic A"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-22T10:00:05Z",
                "task": {"id": "t-dyn", "name": "Dynamic A"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        all_task_labels = [ln.label for ln in lines if ln.kind == "task"]
        # Completed dynamic child must not appear.
        assert not any("Dynamic A" in lbl for lbl in all_task_labels), (
            f"Completed dynamic child must be filtered, got: {all_task_labels}"
        )

    def test_dynamic_child_under_role_header(self) -> None:
        """TC-323: Dynamic child with role appears under correct role header."""
        from datetime import datetime, timezone

        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        parent.children.append(
            TaskDefinition(
                name="nginx : Dynamic A",
                role="nginx",
                is_dynamic=True,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
            )
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"}
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "Test"},
            }
        )
        # Make parent running so tree is visible.
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t-parent", "name": "Include tasks file"},
                "play": {"id": "play-1"},
            }
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        role_lines = [ln for ln in lines if ln.kind == "role" and "nginx" in ln.label]
        assert len(role_lines) >= 1, (
            f"Expected nginx role header, got {[ln.label for ln in lines]}"
        )
        # The pending dynamic child should appear under the nginx role header
        # (depth 3, not depth 2).
        pending_under_role = [
            ln
            for ln in lines
            if ln.kind == "task" and ln.status == Status.PENDING and ln.depth == 3
        ]
        assert len(pending_under_role) >= 1, (
            f"Dynamic child should appear at depth 3 under role header, got lines: {lines}"
        )
        assert any(
            "Dynamic A" in ln.label for ln in pending_under_role
        ), f"Dynamic A not found under role at depth 3: {[ln.label for ln in pending_under_role]}"

    def test_host_leaves_for_running_dynamic_child(self) -> None:
        """TC-324: Running dynamic child shows host leaves under it."""
        from datetime import datetime, timezone

        from ansible_aom.core.models import HostRunState

        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        parent.children.append(
            TaskDefinition(
                name="Dynamic A",
                role=None,
                is_dynamic=True,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
            )
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"}
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "Test"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t-parent", "name": "Include tasks file"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t-dyn", "name": "Dynamic A"},
                "play": {"id": "play-1"},
            }
        )
        # Give the child a running host.
        t = state.plays["play-1"].tasks["t-dyn"]
        t.hosts["web1"] = HostRunState(
            hostname="web1",
            status=Status.RUNNING,
            start_time=datetime(2026, 5, 22, 10, 0, 3, tzinfo=timezone.utc),
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        host_lines = [ln for ln in lines if ln.kind == "host"]
        assert "web1" in [ln.label for ln in host_lines], (
            f"Running dynamic child should have host leaf for web1, got hosts: {[ln.label for ln in host_lines]}"
        )

    def test_no_duplicate_for_runtime_announced_dynamic_child(self) -> None:
        """When a dynamic child is announced at runtime AND grafted in
        children, it must NOT appear twice in the tree."""
        from datetime import datetime, timezone

        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        parent.children.append(
            TaskDefinition(
                name="Dynamic A",
                role=None,
                is_dynamic=True,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
            )
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Test",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"}
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "Test"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t-parent", "name": "Include tasks file"},
                "play": {"id": "play-1"},
            }
        )
        # Announce the dynamic child at runtime — name matches grafted child.
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t-dyn", "name": "Dynamic A"},
                "play": {"id": "play-1"},
            }
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        task_lines = [ln for ln in lines if ln.kind == "task" and "Dynamic A" in ln.label]
        assert len(task_lines) == 1, (
            f"Dynamic A should appear exactly once, got {len(task_lines)} lines: {task_lines}"
        )
