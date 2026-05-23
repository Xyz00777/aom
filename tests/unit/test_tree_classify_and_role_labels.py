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


class TestCrossPlayLookupIsolation:
    """TC-CROSS: Cross-play runtime_by_name lookup must not pollute the
    ``any_running`` check in ``_tree_lines_unbounded``.

    Bug 1: Completed plays borrow a RUNNING task with the same name from
    a later play, appearing as ◐ instead of being skipped.

    Bug 2: Completed handler tasks in a different play UUID are not found
    in the current play's ``runtime_by_name``, showing □ pending. The fix
    skips the completed play entirely when ``any_running`` is True.

    The ``include_cross_play=False`` parameter scopes ``any_running``
    checks to the current play's own tasks only, while rendering
    (``_emit_runtime_play``) keeps the default ``include_cross_play=True``
    for cross-play handler context.
    """

    def _multi_play_shared_task_state(self) -> RunState:
        """Build a state with two plays sharing task name "Cleanup tasks".

        Play 1 ("Deploy webservers"): "Cleanup tasks" completed.
        Play 2 ("Deploy database"): "Cleanup tasks" is actively RUNNING
        with host "db1" in RUNNING status.
        """
        from datetime import datetime, timezone

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Deploy webservers",
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
                    ),
                    TaskDefinition(
                        name="Cleanup tasks",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=1,
                    ),
                ],
            ),
            PlayDefinition(
                id="p2",
                name="Deploy database",
                hosts="dbservers",
                resolved_hosts=["db1"],
                tasks=[
                    TaskDefinition(
                        name="Install postgres",
                        role=None,
                        tags=[],
                        play_id="p2",
                        play_order=1,
                        task_order=0,
                    ),
                    TaskDefinition(
                        name="Cleanup tasks",
                        role=None,
                        tags=[],
                        play_id="p2",
                        play_order=1,
                        task_order=1,
                    ),
                ],
            ),
        ]
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-23T10:00:00Z"}
        )
        # --- Play 1 events (all completed) ---
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "Deploy webservers"},
            }
        )
        # Task 1: Install nginx → OK
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        # Task 2: Cleanup tasks → OK
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:06Z",
                "task": {"id": "t2", "name": "Cleanup tasks"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:07Z",
                "task": {"id": "t2", "name": "Cleanup tasks"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:09Z",
                "task": {"id": "t2", "name": "Cleanup tasks"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        # --- Play 2 events (Cleanup tasks is RUNNING) ---
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:10Z",
                "play": {"id": "play-2", "name": "Deploy database"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:11Z",
                "task": {"id": "t3", "name": "Install postgres"},
                "play": {"id": "play-2"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:12Z",
                "task": {"id": "t3", "name": "Install postgres"},
                "host": "db1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:14Z",
                "task": {"id": "t3", "name": "Install postgres"},
                "hosts": {"db1": {"ok": True, "changed": False}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:15Z",
                "task": {"id": "t4", "name": "Cleanup tasks"},
                "play": {"id": "play-2"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:16Z",
                "task": {"id": "t4", "name": "Cleanup tasks"},
                "host": "db1",
            }
        )
        return state

    def test_completed_play_skipped_when_other_play_running(self) -> None:
        """TC-CROSS-2: When play 2 has a RUNNING task, a previously completed
        play 1 sharing the same task name must NOT appear in the tree
        (no borrowed ◐ icon from play 2's running task)."""
        state = self._multi_play_shared_task_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=60)

        # Play 2 is running; play 1 (completed) should be skipped.
        play_lines = {ln.label: ln for ln in lines if ln.kind == "play"}
        assert "play: Deploy database" in play_lines, (
            "Running play 2 must appear in tree"
        )
        assert "play: Deploy webservers" not in play_lines, (
            "Completed play 1 must be skipped when another play has running items"
        )

        # Ensure no task lines were emitted for the completed play 1.
        play1_task_lines = [
            ln for ln in lines if ln.kind == "task" and ln.label.startswith("Install nginx")
        ]
        assert len(play1_task_lines) == 0, (
            "Completed play's tasks must not appear in tree"
        )

    def test_completed_play_no_stale_pending_handler_tasks(self) -> None:
        """TC-CROSS-1: A completed play whose handler tasks ran under a
        different play UUID must not show stale □ pending — the entire
        play is skipped when ``any_running`` detects running items
        from another play."""
        from datetime import datetime, timezone

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Deploy webservers",
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
                    ),
                    TaskDefinition(
                        name="Restart nginx",
                        role=None,
                        tags=["handlers"],
                        play_id="p1",
                        play_order=0,
                        task_order=1,
                    ),
                ],
            ),
            PlayDefinition(
                id="p2",
                name="Deploy database",
                hosts="dbservers",
                resolved_hosts=["db1"],
                tasks=[
                    TaskDefinition(
                        name="Install postgres",
                        role=None,
                        tags=[],
                        play_id="p2",
                        play_order=1,
                        task_order=0,
                    ),
                ],
            ),
        ]
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-23T10:00:00Z"}
        )
        # Play 1: "Install nginx" completes, then "Restart nginx" runs as
        # a handler under a different play UUID.
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "Deploy webservers"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": True}},
            }
        )

        # Handler task "Restart nginx" runs under play-handler UUID (different
        # from play-1). It's completed too.
        state.handle_event(
            {
                "_event": "v2_playbook_on_handler_task_start",
                "_timestamp": "2026-05-23T10:00:06Z",
                "task": {"id": "t-handler", "name": "Restart nginx"},
                "play": {"id": "play-handler", "name": "Deploy webservers"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:07Z",
                "task": {"id": "t-handler", "name": "Restart nginx"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:09Z",
                "task": {"id": "t-handler", "name": "Restart nginx"},
                "hosts": {"web1": {"ok": True, "changed": True}},
            }
        )

        # Play 2: has a RUNNING task.
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:10Z",
                "play": {"id": "play-2", "name": "Deploy database"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:11Z",
                "task": {"id": "t3", "name": "Install postgres"},
                "play": {"id": "play-2"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:12Z",
                "task": {"id": "t3", "name": "Install postgres"},
                "host": "db1",
            }
        )
        # Leave "Install postgres" RUNNING (no terminal event).

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=60)

        # Only the running play 2 should appear.
        play_lines = [ln.label for ln in lines if ln.kind == "play"]
        assert "play: Deploy database" in play_lines, (
            f"Running play must appear, got: {play_lines}"
        )
        assert "play: Deploy webservers" not in play_lines, (
            f"Completed play must be skipped, got: {play_lines}"
        )

        # No □ pending for "Restart nginx" — play 1 is skipped entirely.
        task_lines = [ln for ln in lines if ln.kind == "task"]
        task_labels = [ln.label for ln in task_lines]
        assert "Restart nginx" not in task_labels, (
            f"Completed handler task must not show as □ pending, got tasks: {task_labels}"
        )

    def test_own_running_task_still_renders_with_cross_play(self) -> None:
        """TC-CROSS-3: A play with its own RUNNING task renders correctly
        using cross-play lookup (default ``include_cross_play=True``)."""
        from datetime import datetime, timezone

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Deploy webservers",
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
                    ),
                ],
            ),
        ]
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-23T10:00:00Z"}
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "Deploy webservers"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        task_lines = [ln for ln in lines if ln.kind == "task"]
        assert len(task_lines) == 1, f"Expected one task line, got: {lines}"
        assert task_lines[0].status == Status.RUNNING, (
            f"Own running task should show RUNNING status, got {task_lines[0].status}"
        )
        assert "Install nginx" in task_lines[0].label, (
            f"Own task name should appear, got {task_lines[0].label}"
        )

    def test_include_cross_play_false_returns_no_cross_play_items(self) -> None:
        """TC-CROSS-4: ``_play_running_and_pending(play, include_cross_play=False)``
        returns no items borrowed from other plays — only the current play's
        own tasks are considered."""
        state = self._multi_play_shared_task_state()
        p = TreeProjection.from_run_state(state)

        play1 = state.plays.get("play-1")
        assert play1 is not None

        # With cross-play: "Cleanup tasks" running in play 2 would be
        # borrowed into play 1's runtime_by_name.
        items_with = p._play_running_and_pending(play1, include_cross_play=True)
        # With include_cross_play=False: only play 1's own tasks.
        items_without = p._play_running_and_pending(play1, include_cross_play=False)

        # Play 1's own tasks are all completed → no running/pending items.
        running_without = [name for kind, name, *_ in items_without if kind == "running"]
        assert len(running_without) == 0, (
            f"No running items expected without cross-play, got: {running_without}"
        )

        # Play 1 has no own running tasks so items_without should be empty
        # (all own tasks are completed → filtered).
        # With cross-play, play 2's "Cleanup tasks" is RUNNING with a host
        # → it may appear in items_with.
        # (Whether it appears depends on whether play 2's task has hosts
        # with RUNNING status; it does in the fixture.)
        has_running_with = any(kind == "running" for kind, *_ in items_with)

        # Verify isolation: items_without is strictly a subset.
        names_without = {name for _, name, *_ in items_without}
        names_with = {name for _, name, *_ in items_with}
        assert names_without <= names_with, (
            f"Items without cross-play should be subset of items with, "
            f"without={names_without}, with={names_with}"
        )


class TestStickyFallbackTreeRender:
    """TC-STICKY: Tree projection must not flicker between "current running
    play only" and "all completed plays" during transient multi-frame gaps
    under linear strategy.

    The fix: a sticky `_last_running_play_id` field persists across render
    calls, so when `any_running` is False during a gap, the fallback shows
    the most recent running play rather than all completed plays.
    """

    @staticmethod
    def _two_play_state_play2_gap() -> RunState:
        """Play 1 completed, Play 2 in gap (tasks exist, all hosts terminal).

        Simulates the moment after one linear-strategy task finishes and
        before the next task starts. Both plays have a runtime counterpart
        (play_start fired), but no hosts are RUNNING anywhere.
        """
        from datetime import datetime, timezone

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Play One",
                hosts="web",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="Task 1A",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                    ),
                ],
            ),
            PlayDefinition(
                id="p2",
                name="Play Two",
                hosts="db",
                resolved_hosts=["db1"],
                tasks=[
                    TaskDefinition(
                        name="Task 2A",
                        role=None,
                        tags=[],
                        play_id="p2",
                        play_order=1,
                        task_order=0,
                    ),
                ],
            ),
        ]
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-23T10:00:00Z"}
        )
        # Play 1: start + complete its single task
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "Play One"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "t1", "name": "Task 1A"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "t1", "name": "Task 1A"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:05Z",
                "task": {"id": "t1", "name": "Task 1A"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        # Play 2: started, task completed (gap state)
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:06Z",
                "play": {"id": "play-2", "name": "Play Two"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:07Z",
                "task": {"id": "t2", "name": "Task 2A"},
                "play": {"id": "play-2"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:08Z",
                "task": {"id": "t2", "name": "Task 2A"},
                "host": "db1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:10Z",
                "task": {"id": "t2", "name": "Task 2A"},
                "hosts": {"db1": {"ok": True, "changed": False}},
            }
        )
        return state

    def test_sticky_1_gap_between_tasks_renders_most_recent_play(self):
        """TC-STICKY-1: Gap between tasks — only the most recent
        running play renders, not completed plays.

        After Play 1 is fully done and Play 2 is in gap (tasks complete),
        the tree must show Play 2 (sticky fallback), not Play 1.

        Also verifies that the sticky ID persists across a second render
        call — the gap doesn't cause a flip back to "all plays."
        """
        state = self._two_play_state_play2_gap()
        p = TreeProjection.from_run_state(state)

        # First render: Play 2 was the last running play (via the scan),
        # so it should be the sticky winner.
        lines1 = p.tree_lines(budget=60)
        play_lines1 = {ln.label for ln in lines1 if ln.kind == "play"}
        assert "play: Play Two" in play_lines1, (
            f"Play 2 must render as sticky fallback, got: {play_lines1}"
        )
        assert "play: Play One" not in play_lines1, (
            f"Completed Play 1 must be filtered, got: {play_lines1}"
        )
        # Verify sticky state persisted
        assert p._last_running_play_id == "play-2", (
            f"Sticky fallback should point to play-2, got {p._last_running_play_id}"
        )

        # Second render (simulating next frame): the gap persists.
        lines2 = p.tree_lines(budget=60)
        play_lines2 = {ln.label for ln in lines2 if ln.kind == "play"}
        assert "play: Play Two" in play_lines2, (
            "Second frame: Play 2 must still render via sticky fallback"
        )
        assert "play: Play One" not in play_lines2, (
            "Second frame: completed Play 1 must stay filtered"
        )

    def test_sticky_2_two_plays_both_running(self):
        """TC-STICKY-2: Two plays both running — both render in the tree.

        When two plays each have a RUNNING task, both should appear.
        The sticky fallback is set to the LATEST running play (play 2),
        but play 1 still renders because it has its own running items.
        """
        from datetime import datetime, timezone

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Deploy web",
                hosts="web",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="Install nginx",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                    ),
                ],
            ),
            PlayDefinition(
                id="p2",
                name="Deploy db",
                hosts="db",
                resolved_hosts=["db1"],
                tasks=[
                    TaskDefinition(
                        name="Install postgres",
                        role=None,
                        tags=[],
                        play_id="p2",
                        play_order=1,
                        task_order=0,
                    ),
                ],
            ),
        ]
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-23T10:00:00Z"}
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "Deploy web"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:04Z",
                "play": {"id": "play-2", "name": "Deploy db"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:05Z",
                "task": {"id": "t2", "name": "Install postgres"},
                "play": {"id": "play-2"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:06Z",
                "task": {"id": "t2", "name": "Install postgres"},
                "host": "db1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=60)
        play_labels = {ln.label for ln in lines if ln.kind == "play"}
        assert "play: Deploy web" in play_labels, "Both running plays should render"
        assert "play: Deploy db" in play_labels, "Both running plays should render"
        assert p._last_running_play_id == "play-2", (
            "Sticky fallback should point to LATEST running play"
        )

    def test_sticky_3_no_plays_running_yet_renders_all_upcoming(self):
        """TC-STICKY-3: No plays running yet — all plays render (no filter).

        When no play has running items AND the sticky pointer is unset
        (pre-first task), the tree must render all plays: runtime plays
        with tasks and upcoming definition-only plays.

        The gap test fixture fires events so tree is visible but no
        host is RUNNING anywhere. Both the started play and the upcoming
        play must appear.
        """
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Setup",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="Ping hosts",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                    ),
                ],
            ),
            PlayDefinition(
                id="p2",
                name="Deploy",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="Install app",
                        role=None,
                        tags=[],
                        play_id="p2",
                        play_order=1,
                        task_order=0,
                    ),
                ],
            ),
        ]
        # Fire events: start play 1 and complete its single task (gap state).
        # Tree is visible because play 1 has tasks, but no running items.
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-23T10:00:00Z"}
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "Setup"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "t1", "name": "Ping hosts"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "t1", "name": "Ping hosts"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:05Z",
                "task": {"id": "t1", "name": "Ping hosts"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )

        # Fresh projection: no _last_running_play_id, no running items.
        # secondary fallback should kick in and set active_play_id to
        # play-1 (last with tasks). But that's a single-play sticky —
        # we still want upcoming plays.
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=60)
        play_labels = {ln.label for ln in lines if ln.kind == "play"}
        assert "play: Setup" in play_labels, "Started play should render"
        assert "play: Deploy" in play_labels, "Upcoming play should render"
        assert p._last_running_play_id == "play-1", (
            "Secondary fallback should set sticky to play-1"
        )

    def test_sticky_4_play_transitions_from_running_to_gap(self):
        """TC-STICKY-4: Play transitions from running to gap — tree
        stays showing the play's last state, does NOT toggle to
        showing completed plays.

        This simulates two frames:
        Frame 1: Play 2 has a RUNNING task → sticky set to play-2.
        Frame 2: Play 2's task completes (gap) → sticky persists,
        tree still shows Play 2, not completed Play 1.
        """
        from datetime import datetime, timezone

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="Install deps",
                hosts="web",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="Apt update",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                    ),
                ],
            ),
            PlayDefinition(
                id="p2",
                name="Start services",
                hosts="web",
                resolved_hosts=["web1"],
                tasks=[
                    TaskDefinition(
                        name="systemctl start nginx",
                        role=None,
                        tags=[],
                        play_id="p2",
                        play_order=1,
                        task_order=0,
                    ),
                ],
            ),
        ]
        state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-23T10:00:00Z"}
        )
        # Play 1: completed
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:01Z",
                "play": {"id": "play-1", "name": "Install deps"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:02Z",
                "task": {"id": "t1", "name": "Apt update"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:03Z",
                "task": {"id": "t1", "name": "Apt update"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:05Z",
                "task": {"id": "t1", "name": "Apt update"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        # Play 2: RUNNING
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-23T10:00:06Z",
                "play": {"id": "play-2", "name": "Start services"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-23T10:00:07Z",
                "task": {"id": "t2", "name": "systemctl start nginx"},
                "play": {"id": "play-2"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-23T10:00:08Z",
                "task": {"id": "t2", "name": "systemctl start nginx"},
                "host": "web1",
            }
        )

        # Frame 1: Play 2 running → sticky set to play-2
        p = TreeProjection.from_run_state(state)
        lines1 = p.tree_lines(budget=60)
        play_labels1 = {ln.label for ln in lines1 if ln.kind == "play"}
        assert "play: Start services" in play_labels1
        assert "play: Install deps" not in play_labels1
        assert p._last_running_play_id == "play-2"

        # Frame 2: Complete Play 2's task → gap state
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-23T10:00:10Z",
                "task": {"id": "t2", "name": "systemctl start nginx"},
                "hosts": {"web1": {"ok": True, "changed": True}},
            }
        )
        # Same projection object (sticky state persists)
        lines2 = p.tree_lines(budget=60)
        play_labels2 = {ln.label for ln in lines2 if ln.kind == "play"}
        assert "play: Start services" in play_labels2, (
            "Sticky fallback must keep showing Play 2 during gap"
        )
        assert "play: Install deps" not in play_labels2, (
            "Completed Play 1 must stay filtered even during gap"
        )
