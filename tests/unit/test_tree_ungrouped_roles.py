"""Regression tests for ungrouped role tasks in the tree view.

Ungrouped role tasks are TaskDefinition entries with a non-None ``role``
attribute that are NOT wrapped in a RoleGroupDefinition (because there
are fewer than 5 consecutive same-role tasks). The tree must still:

1. Show them under a ``role: X (N tasks)`` header at depth=3
2. Include their task count in the role label
3. Prioritize running tasks above pending tasks so truncation cuts
   pending content first
4. Index them in ``_task_role`` so runtime-only tasks can find their role
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


def _play_def(play_id: str, name: str, tasks: list, hosts: list[str] | None = None) -> PlayDefinition:
    return PlayDefinition(
        id=play_id,
        name=name,
        hosts="all",
        resolved_hosts=hosts or ["web1"],
        tasks=tasks,
    )


class TestUngroupedRoleTasksInTree:
    """Ungrouped role tasks (TaskDefinition with non-None role, not in
    RoleGroupDefinition) must appear under a role header at depth=3,
    not at play level (depth=2)."""

    def _state_with_ungrouped_role_running(self) -> RunState:
        """Play with a running podman task (1 task, below grouping threshold)."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def("p1", "deploy", [
                TaskDefinition(name="Install nginx", role=None, tags=[], play_id="p1",
                                play_order=0, task_order=0),
                TaskDefinition(name="Deploy podman container", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=1),
            ]),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-22T10:00:01Z",
            "play": {"id": "play-1", "name": "deploy"},
        })
        state.handle_event({
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-22T10:00:02Z",
            "task": {"id": "t1", "name": "Deploy podman container"},
            "play": {"id": "play-1"},
        })
        state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-05-22T10:00:03Z",
            "task": {"id": "t1", "name": "Deploy podman container"},
            "host": "web1",
        })
        return state

    def test_ungrouped_role_appears_under_role_header(self):
        """A bare TaskDefinition with role='podman' must appear under
        a 'role: podman' header, not at play level."""
        state = self._state_with_ungrouped_role_running()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        role_lines = [ln for ln in lines if ln.kind == "role"]
        assert len(role_lines) >= 1, f"expected role line for podman, got {[ln.label for ln in lines]}"
        assert "podman" in role_lines[0].label

        # The podman task must have depth=3 (under role), not depth=2 (play level).
        podman_task_lines = [ln for ln in lines if ln.kind == "task" and "podman" in ln.label.lower()]
        # It might not contain "podman" in the label, check by role grouping instead
        podman_role_idx = next(i for i, ln in enumerate(lines) if ln.kind == "role" and "podman" in ln.label)
        # Task after role must have depth > role depth
        for ln in lines[podman_role_idx + 1:]:
            if ln.kind == "task":
                assert ln.depth > lines[podman_role_idx].depth, (
                    f"task under podman role must have depth > role depth, "
                    f"got task depth={ln.depth}, role depth={lines[podman_role_idx].depth}"
                )
                break

    def test_ungrouped_role_label_shows_task_count(self):
        """Role label for ungrouped role must show the total task count
        from definitions, e.g. '(2 tasks)' when there are 2 podman tasks."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def("p1", "deploy", [
                TaskDefinition(name="Deploy container", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=0),
                TaskDefinition(name="Configure network", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=1),
            ]),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-22T10:00:01Z",
            "play": {"id": "play-1", "name": "deploy"},
        })
        state.handle_event({
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-22T10:00:02Z",
            "task": {"id": "t1", "name": "Deploy container"},
            "play": {"id": "play-1"},
        })
        state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-05-22T10:00:03Z",
            "task": {"id": "t1", "name": "Deploy container"},
            "host": "web1",
        })
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        role_lines = [ln for ln in lines if ln.kind == "role"]
        assert len(role_lines) >= 1
        assert "(2 tasks)" in role_lines[0].label, (
            f"ungrouped role with 2 tasks must show '(2 tasks)', got: {role_lines[0].label}"
        )

    def test_task_role_indexes_ungrouped_tasks(self):
        """_task_role must return the role for ungrouped TaskDefinition entries,
        not just for RoleGroupDefinition entries."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def("p1", "deploy", [
                TaskDefinition(name="Deploy container", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=0),
            ]),
        ]
        p = TreeProjection.from_run_state(state)
        result = p._task_role("Deploy container")
        assert result == "podman", (
            f"_task_role must find role for ungrouped TaskDefinition, got: {result!r}"
        )

    def test_running_task_prioritized_over_pending(self):
        """When a running task is at the end of the definition list,
        the stable partition must place it before pending tasks so
        truncation does not cut it."""
        state = self._state_with_ungrouped_role_running()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        # Find the running task
        running_tasks = [ln for ln in lines if ln.kind == "task" and ln.status == Status.RUNNING]
        pending_tasks = [ln for ln in lines if ln.kind == "task" and ln.status == Status.PENDING]

        if running_tasks and pending_tasks:
            running_idx = lines.index(running_tasks[0])
            pending_idx = lines.index(pending_tasks[0])
            assert running_idx < pending_idx, (
                f"running task must appear before pending tasks in tree, "
                f"but running at {running_idx}, pending at {pending_idx}"
            )

    def test_host_leaf_visible_under_ungrouped_role(self):
        """Host leaf must appear under the running task within an
        ungrouped role, even when budget is tight."""
        state = self._state_with_ungrouped_role_running()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        host_lines = [ln for ln in lines if ln.kind == "host"]
        assert len(host_lines) >= 1, (
            f"expected host leaf under running task, got: {[ln.label for ln in lines]}"
        )


class TestPendingPlayUngroupedRoles:
    """Pending plays must also show ungrouped role tasks under role headers."""

    def test_pending_play_shows_ungrouped_role_header(self):
        """A pending play with bare TaskDefinition entries that have role
        set must render them under a 'role: X (N tasks)' header, not at
        play level."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def("p1", "deploy", [
                TaskDefinition(name="Install nginx", role=None, tags=[], play_id="p1",
                                play_order=0, task_order=0),
                TaskDefinition(name="Deploy container", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=1),
                TaskDefinition(name="Configure network", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=2),
            ]),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-22T10:00:01Z",
            "play": {"id": "play-1", "name": "deploy"},
        })
        state.handle_event({
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-22T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "play-1"},
        })
        state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-05-22T10:00:03Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "host": "web1",
        })
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        role_lines = [ln for ln in lines if ln.kind == "role"]
        assert len(role_lines) >= 1, f"expected podman role line, got {[ln.label for ln in lines]}"
        assert "podman" in role_lines[0].label
        assert "(2 tasks)" in role_lines[0].label, (
            f"ungrouped role with 2 tasks must show '(2 tasks)', got: {role_lines[0].label}"
        )

        # Podman tasks must have depth > role depth (not at play level)
        podman_idx = next(i for i, ln in enumerate(lines) if ln.kind == "role" and "podman" in ln.label)
        for ln in lines[podman_idx + 1:]:
            if ln.kind == "task":
                assert ln.depth > lines[podman_idx].depth, (
                    f"task under podman role at depth={ln.depth}, role at depth={lines[podman_idx].depth}"
                )
                break

    def test_runtime_play_counts_ungrouped_role_tasks_in_label(self):
        """Runtime play role labels must count ungrouped role tasks from
        definitions, not just from visible running+pending items."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def("p1", "deploy", [
                TaskDefinition(name="Deploy container", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=0),
                TaskDefinition(name="Configure network", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=1),
            ]),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-22T10:00:01Z",
            "play": {"id": "play-1", "name": "deploy"},
        })
        # First task is running, second is pending
        state.handle_event({
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-22T10:00:02Z",
            "task": {"id": "t1", "name": "Deploy container"},
            "play": {"id": "play-1"},
        })
        state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-05-22T10:00:03Z",
            "task": {"id": "t1", "name": "Deploy container"},
            "host": "web1",
        })
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        role_lines = [ln for ln in lines if ln.kind == "role"]
        assert len(role_lines) >= 1
        assert "(2 tasks)" in role_lines[0].label, (
            f"runtime role label for 2 ungrouped podman tasks must show '(2 tasks)', "
            f"got: {role_lines[0].label}"
        )


class TestRolePrefixStripping:
    """Ansible sends task names with a 'role : ' prefix at runtime
    (e.g. 'podman : Install Podman'). Preflight definitions store
    the stripped form ('Install Podman'). The tree must still match
    these correctly so runtime tasks land under the right role header
    and host leaves appear under running tasks."""

    def test_task_role_with_prefixed_name(self):
        """_task_role('podman : Install Podman') must return 'podman',
        not None."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def("p1", "deploy", [
                TaskDefinition(name="Install Podman", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=0),
            ]),
        ]
        p = TreeProjection.from_run_state(state)
        assert p._task_role("podman : Install Podman") == "podman"
        assert p._task_role("Install Podman") == "podman"

    def test_runtime_prefixed_task_under_role_header(self):
        """A runtime task named 'podman : Install Podman' must be
        rendered under the 'role: podman' header, not at play level."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def("p1", "deploy", [
                TaskDefinition(name="Install Podman", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=0),
                TaskDefinition(name="Update home directory", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=1),
            ]),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-22T10:00:01Z",
            "play": {"id": "play-1", "name": "deploy"},
        })
        state.handle_event({
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-22T10:00:02Z",
            "task": {"id": "t1", "name": "podman : Install Podman"},
            "play": {"id": "play-1"},
        })
        state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-05-22T10:00:03Z",
            "task": {"id": "t1", "name": "podman : Install Podman"},
            "host": "web1",
        })

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        role_lines = [ln for ln in lines if ln.kind == "role"]
        assert len(role_lines) >= 1, f"expected podman role line, got {[ln.label for ln in lines]}"
        assert "podman" in role_lines[0].label

        # Task under podman role must have depth > role depth
        podman_idx = next(i for i, ln in enumerate(lines) if ln.kind == "role" and "podman" in ln.label)
        task_under_role = next(
            (ln for ln in lines[podman_idx + 1:] if ln.kind == "task"),
            None,
        )
        assert task_under_role is not None, "expected a task under podman role"
        assert task_under_role.depth > lines[podman_idx].depth, (
            f"task at depth={task_under_role.depth}, must be deeper than role at depth={lines[podman_idx].depth}"
        )

    def test_host_leaf_under_prefixed_runtime_task(self):
        """Host leaves must appear under a running task whose runtime name
        carries the 'role : ' prefix."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def("p1", "deploy", [
                TaskDefinition(name="Install Podman", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=0),
            ]),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-22T10:00:01Z",
            "play": {"id": "play-1", "name": "deploy"},
        })
        state.handle_event({
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-22T10:00:02Z",
            "task": {"id": "t1", "name": "podman : Install Podman"},
            "play": {"id": "play-1"},
        })
        state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-05-22T10:00:03Z",
            "task": {"id": "t1", "name": "podman : Install Podman"},
            "host": "web1",
        })

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        host_lines = [ln for ln in lines if ln.kind == "host"]
        assert len(host_lines) >= 1, (
            f"expected host leaf under prefixed running task, got: {[ln.label for ln in lines]}"
        )
        assert host_lines[0].label == "web1"

    def test_no_duplicate_tasks_with_prefixed_runtime_names(self):
        """Runtime tasks with prefixed names must not appear both at play
        level AND under a role header (the double-rendering bug)."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def("p1", "deploy", [
                TaskDefinition(name="Install nginx", role=None, tags=[], play_id="p1",
                                play_order=0, task_order=0),
                TaskDefinition(name="Deploy container", role="podman", tags=[],
                                play_id="p1", play_order=0, task_order=1),
            ]),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-22T10:00:01Z",
            "play": {"id": "play-1", "name": "deploy"},
        })
        state.handle_event({
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-22T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "play-1"},
        })
        state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-05-22T10:00:03Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "host": "web1",
        })

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        # Count task lines mentioning "Deploy container" or "podman"
        deploy_lines = [ln for ln in lines if ln.kind == "task" and "Deploy container" in ln.label]
        assert len(deploy_lines) <= 1, (
            f"Deploy container must appear at most once, got {len(deploy_lines)}: "
            f"{[ln.label for ln in deploy_lines]}"
        )