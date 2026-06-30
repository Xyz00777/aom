"""Regression tests for role_total_tasks counting runtime-only tasks.

When a role is loaded via include_role (dynamic), --list-tasks doesn't
expand its tasks. They appear at runtime with a "role : " prefix.
role_total_tasks must count these runtime-only tasks, otherwise the
role header shows no task count and the overall task total is wrong.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.core.models import (
    PlayDefinition,
    RunState,
    Status,
    TaskDefinition,
)
from ansible_aom.core.tree import TreeProjection


def _td(name: str, role: str | None = None, order: int = 0) -> TaskDefinition:
    return TaskDefinition(
        name=name, role=role, tags=[], play_id="p1", play_order=0, task_order=order
    )


class TestRuntimeRoleTaskCount:
    """role_total_tasks must include tasks from runtime that aren't in
    the preflight definitions (include_role / dynamic tasks)."""

    def _state_with_dynamic_role(self) -> RunState:
        """Preflight has no podman tasks. At runtime, podman tasks appear
        via include_role with 'podman : ' prefix."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="webservers",
                resolved_hosts=["web1"],
                tasks=[
                    _td("Install keepalived", order=0),
                    _td("Detect interface", order=1),
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "deploy"},
            }
        )
        # Non-role tasks complete
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t1", "name": "Install keepalived"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-22T10:00:04Z",
                "task": {"id": "t1", "name": "Install keepalived"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:05Z",
                "task": {"id": "t2", "name": "Detect interface"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-22T10:00:07Z",
                "task": {"id": "t2", "name": "Detect interface"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        # Dynamic podman role tasks appear at runtime
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:08Z",
                "task": {"id": "t3", "name": "podman : Install Podman"},
                "play": {"id": "play-1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:09Z",
                "task": {"id": "t4", "name": "podman : Configure rootless"},
                "play": {"id": "play-1"},
            }
        )
        # Task t3 has a RUNNING host
        t3 = state.plays["play-1"].tasks["t3"]
        t3.hosts["web1"] = __import__(
            "ansible_aom.core.models", fromlist=["HostRunState"]
        ).HostRunState(
            hostname="web1",
            status=Status.RUNNING,
            start_time=datetime(2026, 5, 22, 10, 0, 8, tzinfo=timezone.utc),
        )
        return state

    def test_dynamic_role_shows_task_count_in_label(self):
        """A role loaded via include_role must show its runtime task count
        in the role header label, not 0 or no count.

        The role label always carries the role's full task count
        ``(N tasks)`` — never a ``(M remaining)`` suffix (which would
        have grown as completed tasks dropped out of the visible
        tree). The ``… and N more tasks`` inner/outer footers surface
        the truncated work. See
        ``.sisyphus/plans/two-level-truncation.md`` T3."""
        state = self._state_with_dynamic_role()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        role_lines = [ln for ln in lines if ln.kind == "role"]
        assert len(role_lines) >= 1, (
            f"expected a podman role line, got {[ln.label for ln in lines]}"
        )
        podman_role = [ln for ln in role_lines if "podman" in ln.label]
        assert len(podman_role) >= 1, f"expected podman role, got {[ln.label for ln in role_lines]}"
        assert "(2 tasks)" in podman_role[0].label, (
            f"podman role should show total count (2 tasks); got: {podman_role[0].label}"
        )
        assert "remaining" not in podman_role[0].label, (
            f"podman role must NOT carry 'remaining' suffix; got: {podman_role[0].label}"
        )

    def test_dynamic_role_task_appears_under_role_header(self):
        """Runtime podman tasks should appear as children of the podman
        role header, not as bare ungrouped tasks."""
        state = self._state_with_dynamic_role()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        # Find the podman role header and the next task lines
        role_idx = None
        for i, ln in enumerate(lines):
            if ln.kind == "role" and "podman" in ln.label:
                role_idx = i
                break
        assert role_idx is not None, f"no podman role header found in {[ln.label for ln in lines]}"
        # Next line(s) should be task(s) under podman
        next_line = lines[role_idx + 1]
        assert next_line.kind == "task", f"expected task after podman role, got {next_line.kind}"
        assert next_line.depth > lines[role_idx].depth, (
            f"task should be deeper than role header, depths: {next_line.depth} vs {lines[role_idx].depth}"
        )

    def test_no_double_counting_preflight_and_runtime(self):
        """When a role has tasks in BOTH preflight and runtime (same task
        resolved from template), they must not be double-counted."""
        from ansible_aom.core.models import RoleGroupDefinition

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="webservers",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="podman",
                        tasks=[
                            _td("Install Podman", role="podman", order=0),
                            _td("Configure rootless", role="podman", order=1),
                        ],
                    ),
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "deploy"},
            }
        )
        # Runtime task with "podman : " prefix (preflight had "Install Podman")
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-05-22T10:00:02Z",
                "task": {"id": "t1", "name": "podman : Install Podman"},
                "play": {"id": "play-1"},
            }
        )
        t1 = state.plays["play-1"].tasks["t1"]
        t1.hosts["web1"] = __import__(
            "ansible_aom.core.models", fromlist=["HostRunState"]
        ).HostRunState(
            hostname="web1",
            status=Status.RUNNING,
            start_time=datetime(2026, 5, 22, 10, 0, 2, tzinfo=timezone.utc),
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        role_lines = [ln for ln in lines if ln.kind == "role" and "podman" in ln.label]
        assert len(role_lines) >= 1, "expected podman role line"
        # Should be 2 tasks (from preflight), NOT 3 (2 preflight + 1 runtime double-counted)
        assert "(2 tasks)" in role_lines[0].label, (
            f"podman preflight tasks should not be double-counted with runtime, got: {role_lines[0].label}"
        )

    def test_task_name_with_colon_not_misidentified_as_role(self):
        """A task name containing ' : ' that is NOT a role prefix must not
        be assigned a role. E.g. 'Install foo : bar' is not role='Install
        foo'."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="webservers",
                resolved_hosts=["web1"],
                tasks=[
                    _td("Install foo : bar", role=None, order=0),
                ],
            )
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
                "task": {"id": "t1", "name": "Install foo : bar"},
                "play": {"id": "play-1"},
            }
        )
        t1 = state.plays["play-1"].tasks["t1"]
        t1.hosts["web1"] = __import__(
            "ansible_aom.core.models", fromlist=["HostRunState"]
        ).HostRunState(
            hostname="web1",
            status=Status.RUNNING,
            start_time=datetime(2026, 5, 22, 10, 0, 2, tzinfo=timezone.utc),
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        role_lines = [ln for ln in lines if ln.kind == "role"]
        assert len(role_lines) == 0, (
            f"'Install foo : bar' should not create a role header, got {[ln.label for ln in role_lines]}"
        )

    def test_dynamic_role_with_no_preflight_shows_runtime_count(self):
        """Pure runtime role (no preflight tasks at all) must still show
        the correct task count from only runtime tasks.

        The role label always carries the role's full task count
        ``(N tasks)`` — never a ``(M remaining)`` suffix. With linear
        strategy and 3 runtime tasks, only 1 is visible in the kept
        lines (the other 2 auto-complete when the next task starts),
        but the label still reads ``(3 tasks)`` because the suffix
        that would have surfaced the visible/total delta was dropped
        (it counted completed tasks and grew as the run progressed).
        See ``.sisyphus/plans/two-level-truncation.md`` T3."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="webservers",
                resolved_hosts=["web1"],
                tasks=[],  # No preflight tasks!
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-22T10:00:01Z",
                "play": {"id": "play-1", "name": "deploy"},
            }
        )
        # Three podman tasks at runtime
        for i, name in enumerate(["podman : Install", "podman : Configure", "podman : Enable"]):
            tid = f"t{i + 1}"
            state.handle_event(
                {
                    "_event": "v2_playbook_on_task_start",
                    "_timestamp": f"2026-05-22T10:00:0{2 + i}Z",
                    "task": {"id": tid, "name": name},
                    "play": {"id": "play-1"},
                }
            )
        # First task has RUNNING host
        t1 = state.plays["play-1"].tasks["t1"]
        t1.hosts["web1"] = __import__(
            "ansible_aom.core.models", fromlist=["HostRunState"]
        ).HostRunState(
            hostname="web1",
            status=Status.RUNNING,
            start_time=datetime(2026, 5, 22, 10, 0, 2, tzinfo=timezone.utc),
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        role_lines = [ln for ln in lines if ln.kind == "role" and "podman" in ln.label]
        assert len(role_lines) >= 1, f"expected podman role, got {[ln.label for ln in lines]}"
        assert "(3 tasks)" in role_lines[0].label, (
            f"pure runtime role should show total count (3 tasks); got: {role_lines[0].label}"
        )
        assert "remaining" not in role_lines[0].label, (
            f"pure runtime role must NOT carry 'remaining' suffix; got: {role_lines[0].label}"
        )
