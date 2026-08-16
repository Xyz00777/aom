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

    def test_template_variable_with_punctuation_suffix(self):
        """Regression: preflight name `Ensure {{ user }}'s home exists` must
        match the runtime name `Ensure angie-sidecar's home exists` even
        though punctuation (`'s`) is glued onto the resolved value. Without
        the fix the punctuation becomes a separate skeleton word after
        Jinja stripping and no longer matches the runtime token."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "deploy",
                [
                    _td("Ensure {{ user }}'s home exists", pid="1", order=0),
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
                "task": {"id": "t1", "name": "Ensure angie-sidecar's home exists"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t1", "name": "Ensure angie-sidecar's home exists"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        task_lines = [ln for ln in lines if ln.kind == "task"]
        assert len(task_lines) == 1, (
            f"expected exactly 1 task line (no preflight duplicate), got {len(task_lines)}: "
            f"{[(ln.label, ln.status) for ln in task_lines]}"
        )
        assert "{{ user }}" not in task_lines[0].label, (
            f"preflight template name must be resolved away, got: {task_lines[0].label!r}"
        )
        assert "angie-sidecar's home exists" in task_lines[0].label
        assert task_lines[0].status == Status.RUNNING

    def test_template_variable_with_punctuation_prefix(self):
        """Regression: preflight name `Deploy for {{ user }}!` must match
        runtime name `Deploy for angie-sidecar!` — punctuation (`!`) glued
        onto the resolved value must not break the match."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "deploy",
                [
                    _td("Deploy for {{ user }}!", pid="1", order=0),
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
                "task": {"id": "t1", "name": "Deploy for angie-sidecar!"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t1", "name": "Deploy for angie-sidecar!"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        task_lines = [ln for ln in lines if ln.kind == "task"]
        assert len(task_lines) == 1, (
            f"expected exactly 1 task line (no preflight duplicate), got {len(task_lines)}: "
            f"{[(ln.label, ln.status) for ln in task_lines]}"
        )
        assert "{{ user }}" not in task_lines[0].label
        assert "angie-sidecar!" in task_lines[0].label
        assert task_lines[0].status == Status.RUNNING

    def test_template_variable_in_middle_with_punctuation(self):
        """Two template variables with no extra punctuation still match —
        guards against regression while fixing the punctuation edge case."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "deploy",
                [
                    _td("Copy {{ src }} to {{ dest }}", pid="1", order=0),
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
                "task": {"id": "t1", "name": "Copy /etc/a to /etc/b"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t1", "name": "Copy /etc/a to /etc/b"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        task_lines = [ln for ln in lines if ln.kind == "task"]
        assert len(task_lines) == 1, (
            f"expected exactly 1 task line (no preflight duplicate), got {len(task_lines)}: "
            f"{[(ln.label, ln.status) for ln in task_lines]}"
        )
        assert "{{" not in task_lines[0].label
        assert task_lines[0].status == Status.RUNNING

    def test_empty_skeleton_does_not_swallow_unrelated_task(self):
        """Regression: a preflight task whose name is entirely a Jinja
        template (e.g. ``{{ var }}``) must NOT greedily claim the first
        runtime task it sees. When the preflight list is
        ``["{{ var }}", "Plain task A", "Plain task B"]`` and runtime
        completes A then starts B, the tree must show Plain task B and
        must NOT show ``{{ var }}`` as a pending orphan. Plain task A
        completed so it is correctly dropped from the tree."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "deploy",
                [
                    _td("{{ var }}", pid="1", order=0),
                    _td("Plain task A", pid="1", order=1),
                    _td("Plain task B", pid="1", order=2),
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
        # Plain task A completes
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t1", "name": "Plain task A"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t1", "name": "Plain task A"},
                "play": {"id": "play-1"},
                "hosts": {"web1": {"changed": False}},
            }
        )
        # Plain task B starts running
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:04Z",
                "task": {"id": "t2", "name": "Plain task B"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-22T10:00:05Z",
                "task": {"id": "t2", "name": "Plain task B"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        task_lines = [ln for ln in lines if ln.kind == "task"]
        task_labels = [ln.label for ln in task_lines]
        # Plain task B must appear in the tree (running)
        assert any("Plain task B" in label for label in task_labels), (
            f"Plain task B must appear in the tree, got tasks: "
            f"{[(ln.label, ln.status) for ln in task_lines]}"
        )
        # {{ var }} must NOT appear as a task — it has no runtime match
        # and should be dropped (unmatched preflight with no static
        # fragments cannot claim a runtime slot)
        template_tasks = [ln for ln in task_lines if "{{ var }}" in ln.label]
        assert len(template_tasks) == 0, (
            f"{{ var }} preflight should not appear in tree, got: "
            f"{[(ln.label, ln.status) for ln in template_tasks]}"
        )

    def test_empty_skeleton_is_template_match_returns_false(self):
        """Direct unit test: ``_is_template_match("{{ var }}", "Plain task A")``
        must return False. A preflight name that is entirely a Jinja
        expression has no static fragments to anchor the match, so it must
        not wildcard-match any runtime name."""
        from ansible_aom.core.tree_projection import _is_template_match

        assert _is_template_match("{{ var }}", "Plain task A") is False, (
            "Empty-skeleton preflight must not wildcard-match an unrelated runtime name"
        )

    def test_empty_skeleton_against_itself_returns_false(self):
        """Direct unit test: ``_is_template_match("{{ var }}", "{{ var }}")``
        must return False. Even when both names are the same Jinja
        expression, there are no static fragments to anchor, so this
        function correctly declines to match. The exact-equality path in
        ``_pick_runtime`` handles the case where preflight and runtime
        names are literally identical."""
        from ansible_aom.core.tree_projection import _is_template_match

        assert _is_template_match("{{ var }}", "{{ var }}") is False, (
            "Empty-skeleton preflight must not match even an identical runtime name; "
            "exact-equality handles that case"
        )

    def test_completed_play_with_multiple_templated_tasks_dropped_from_tree(self):
        """When a completed play had multiple tasks with Jinja template names (e.g. 5 tasks
        named 'Get the user ID for {{ user }}') and a subsequent play is running, the completed
        play must be dropped from the tree and not leave lingering pending template tasks."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            _play_def(
                "p1",
                "Deploy Keepalived",
                [
                    _td("Get the user ID for {{ user }}", role="angie", pid="1", order=0),
                    _td("Get the user ID for {{ user }}", role="angie", pid="1", order=1),
                    _td("Get the user ID for {{ user }}", role="angie", pid="1", order=2),
                ],
            ),
            _play_def(
                "p2",
                "Setup Podman",
                [
                    _td("Install podman", pid="2", order=0),
                ],
            ),
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        # Play 1 starts
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy Keepalived"},
            }
        )
        # Task 1 in Play 1 runs and finishes
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t1", "name": "angie : Get the user ID for sidecar1"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-22T10:00:03Z",
                "task": {"id": "t1", "name": "angie : Get the user ID for sidecar1"},
                "play": {"id": "p1"},
                "hosts": {"web1": {"changed": False}},
            }
        )
        # Task 2 in Play 1 runs and finishes
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:04Z",
                "task": {"id": "t2", "name": "angie : Get the user ID for sidecar2"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-22T10:00:05Z",
                "task": {"id": "t2", "name": "angie : Get the user ID for sidecar2"},
                "play": {"id": "p1"},
                "hosts": {"web1": {"changed": False}},
            }
        )
        # Task 3 in Play 1 runs and finishes
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:06Z",
                "task": {"id": "t3", "name": "angie : Get the user ID for sidecar3"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-22T10:00:07Z",
                "task": {"id": "t3", "name": "angie : Get the user ID for sidecar3"},
                "play": {"id": "p1"},
                "hosts": {"web1": {"changed": False}},
            }
        )
        # Play 2 starts
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:08Z",
                "play": {"id": "p2", "name": "Setup Podman"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:09Z",
                "task": {"id": "t4", "name": "Install podman"},
                "play": {"id": "p2"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-05-22T10:00:10Z",
                "task": {"id": "t4", "name": "Install podman"},
                "host": "web1",
            }
        )

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        # Completed Play 1 must NOT appear in tree with lingering pending template tasks
        assert not any("Deploy Keepalived" in ln.label for ln in lines), (
            f"Completed play should not appear in tree, got lines: {[ln.label for ln in lines]}"
        )
        assert not any("{{ user }}" in ln.label for ln in lines), (
            f"Unresolved template tasks should not linger in tree, "
            f"got lines: {[ln.label for ln in lines]}"
        )
