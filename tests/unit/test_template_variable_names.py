"""Regression tests for Jinja2 template variable names in preflight tasks.

ansible's --list-tasks output contains unresolved Jinja2 template
variables (e.g. "Get the user ID for {{ username }}"), but at runtime
the JSONL callback sends the resolved value (e.g. "Get the user ID for
angie-sidecar"). The tree must match these correctly so resolved runtime
tasks land under the right preflight definition and host leaves appear.
"""

from __future__ import annotations

from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
    TaskRunState,
)
from ansible_aom.core.tree import TreeProjection


def _play_def(
    play_id: str, name: str, tasks: list, hosts: list[str] | None = None
) -> PlayDefinition:
    return PlayDefinition(
        id=play_id,
        name=name,
        hosts="all",
        resolved_hosts=hosts or ["web1"],
        tasks=tasks,
    )


def _td(name, role=None, pid="1", order=0):
    return TaskDefinition(
        name=name, role=role, tags=[], play_id=pid, play_order=0, task_order=order
    )


class TestTemplateVariableNameMismatch:
    """Preflight tasks with {{ variable }} must match resolved runtime names."""

    def test_template_variable_resolved(self):
        """A preflight task 'Get ID for {{ user }}' must match the runtime
        task 'Get ID for angie-sidecar' so it does not appear as pending."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "deploy",
                [
                    _td("Get the user ID for {{ username }}", pid="1", order=0),
                    _td("Install nginx", pid="1", order=1),
                ],
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "deploy"},
            }
        )
        # Runtime sends RESOLVED name
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t1", "name": "Get the user ID for angie-sidecar"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t1", "name": "Get the user ID for angie-sidecar"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        # The task must NOT appear as pending (□)
        template_task_pending = [
            ln
            for ln in lines
            if ln.kind == "task" and "{{ username }}" in ln.label and ln.status == Status.PENDING
        ]
        assert len(template_task_pending) == 0, (
            f"template variable task should not appear as pending, got: "
            f"{[(ln.label, ln.status) for ln in template_task_pending]}"
        )

        # The task must appear as RUNNING (◐) with the resolved name
        running_tasks = [
            ln
            for ln in lines
            if ln.kind == "task" and "angie-sidecar" in ln.label and ln.status == Status.RUNNING
        ]
        assert len(running_tasks) >= 1, (
            f"resolved runtime task must appear as running, got: "
            f"{[(ln.label, ln.status) for ln in lines if ln.kind == 'task']}"
        )

    def test_host_leaf_under_resolved_template_task(self):
        """Host leaves must appear under a running task whose preflight
        name has {{ variable }} but runtime name is resolved."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "deploy",
                [
                    _td("Check if user {{ username }} already exists", pid="1", order=0),
                ],
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t1", "name": "Check if user podman already exists"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t1", "name": "Check if user podman already exists"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        host_lines = [ln for ln in lines if ln.kind == "host"]
        assert len(host_lines) >= 1, (
            f"expected host leaf under running template-variable task, "
            f"got: {[ln.label for ln in lines]}"
        )
        assert host_lines[0].label == "web1"

    def test_no_duplicate_for_template_and_resolved_name(self):
        """A task with {{ variable }} in preflight must not appear twice
        in the tree (once as pending from preflight path, once as
        running from runtime-only path)."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "deploy",
                [
                    _td("Ensure user {{ username }} exists", pid="1", order=0),
                ],
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t1", "name": "Ensure user podman exists"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t1", "name": "Ensure user podman exists"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        task_lines = [ln for ln in lines if ln.kind == "task"]
        assert len(task_lines) == 1, (
            f"expected exactly 1 task line (no duplicates), got {len(task_lines)}: "
            f"{[(ln.label, ln.status) for ln in task_lines]}"
        )

    def test_template_variable_in_role_task(self):
        """A role task with {{ variable }} must match the resolved runtime
        name and appear under the correct role header."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "deploy",
                [
                    _td(
                        "Check if user {{ username }} already exists",
                        role="podman",
                        pid="1",
                        order=0,
                    ),
                    _td("Ensure user {{ username }} exists", role="podman", pid="1", order=1),
                ],
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t1", "name": "podman : Check if user podman already exists"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t1", "name": "podman : Check if user podman already exists"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        # Must have a role: podman header
        role_lines = [ln for ln in lines if ln.kind == "role" and "podman" in ln.label]
        assert len(role_lines) >= 1, (
            f"expected podman role header, got: {[ln.label for ln in lines if ln.kind == 'role']}"
        )

        # The running task must appear under the role (depth > role depth)
        podman_idx = next(
            i for i, ln in enumerate(lines) if ln.kind == "role" and "podman" in ln.label
        )
        running_under_role = [
            ln
            for ln in lines[podman_idx + 1 :]
            if ln.kind == "task" and ln.status == Status.RUNNING
        ]
        assert len(running_under_role) >= 1, (
            f"expected running task under podman role, got: "
            f"{[(ln.label, ln.depth, ln.status) for ln in lines[podman_idx:] if ln.kind == 'task']}"
        )
        assert running_under_role[0].depth > lines[podman_idx].depth

    def test_completed_template_task_dropped_from_tree(self):
        """A preflight task with {{ variable }} that has completed at
        runtime must be dropped from the tree, not shown as pending."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "deploy",
                [
                    _td("Get user ID for {{ user }}", pid="1", order=0),
                    _td("Install nginx", pid="1", order=1),
                ],
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "deploy"},
            }
        )
        # First task completed
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t1", "name": "Get user ID for angie-sidecar"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t1", "name": "Get user ID for angie-sidecar"},
                "play": {"id": "play-1"},
                "hosts": {"web1": {"changed": False}},
            }
        )
        # Second task running
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:04Z",
                "task": {"id": "t2", "name": "Install nginx"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-22T10:00:05Z",
                "task": {"id": "t2", "name": "Install nginx"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        # The completed template-variable task should NOT appear
        template_tasks = [
            ln
            for ln in lines
            if ln.kind == "task"
            and ("{{ user }}" in ln.label or "angie-sidecar" in ln.label)
            and ln.status != Status.RUNNING
        ]
        assert len(template_tasks) == 0, (
            f"completed template task should not appear in tree, got: "
            f"{[(ln.label, ln.status) for ln in template_tasks]}"
        )
