"""Unit tests for include_tasks dynamic expansion.

TC-094 / TC-095 from TEST_SPECIFICATION.md Section 5.2.

When ansible-playbook emits a v2_playbook_on_task_start for a task that
does not appear in the pre-parsed --list-tasks output, AOM grafts a new
TaskDefinition under the most recently matched preflight task (which is
the parent include_tasks node — the only static task that fans out into
unknown children at runtime).

Each grafted definition carries:
- is_dynamic=True
- task_order=-1 (sentinel placing it after static siblings)
- A parent.children link to the include_tasks node
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ansible_aom.core.models import (
    PlayDefinition,
    RunState,
    TaskDefinition,
)


def _task_start(task_id: str, task_name: str, play_id: str = "play-uuid-1") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": "2026-04-20T10:00:00Z",
        "task": {"id": task_id, "name": task_name},
        "play": {"id": play_id},
    }


def _runner_start(task_id: str, task_name: str, host: str = "web1") -> dict:
    return {
        "_event": "v2_runner_on_start",
        "_timestamp": "2026-04-20T10:00:00Z",
        "task": {"id": task_id, "name": task_name},
        "host": host,
    }


def _play_start(play_id: str = "play-uuid-1", name: str = "Test play") -> dict:
    return {
        "_event": "v2_playbook_on_play_start",
        "_timestamp": "2026-04-20T10:00:00Z",
        "play": {"id": play_id, "name": name},
    }


def _task_start_with_path(
    task_id: str,
    task_name: str,
    task_path: str,
    play_id: str = "play-uuid-1",
) -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": "2026-04-20T10:00:00Z",
        "task": {"id": task_id, "name": task_name, "path": task_path},
        "play": {"id": play_id},
    }


class TestDynamicExpansion:
    """TC-094 / TC-095: include_tasks dynamic expansion."""

    def test_unknown_task_grafted_as_child_of_last_matched_task(self) -> None:
        """TC-095: Unknown task becomes a child of the last matched preflight task."""
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
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())

        # Static include_tasks entry matches preflight; arrival sets parent.
        state.handle_event(_task_start("uuid-static", "Include tasks file"))

        # Unknown task fires next — must graft under the include_tasks node.
        state.handle_event(_task_start("uuid-dynamic", "Dynamic task A"))

        assert len(parent.children) == 1
        dyn = parent.children[0]
        assert dyn.name == "Dynamic task A"
        assert dyn.is_dynamic is True
        assert dyn.task_order == -1

    def test_dynamic_task_inherits_parent_play_fields(self) -> None:
        """Dynamic TaskDefinition copies play_id and play_order from the parent."""
        parent = TaskDefinition(
            name="Include tasks file",
            role=None,
            tags=[],
            play_id="1",
            play_order=7,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(_task_start("uuid-static", "Include tasks file"))
        state.handle_event(_task_start("uuid-dynamic", "Dynamic task A"))

        dyn = parent.children[0]
        assert dyn.play_id == "1"
        assert dyn.play_order == 7

    def test_multiple_unknown_tasks_accumulate_under_same_parent(self) -> None:
        """TC-094: Several dynamic tasks under the same include_tasks parent."""
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
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(_task_start("uuid-static", "Include tasks file"))
        state.handle_event(_task_start("uuid-a", "Dynamic task A"))
        state.handle_event(_task_start("uuid-b", "Dynamic task B"))

        assert [c.name for c in parent.children] == ["Dynamic task A", "Dynamic task B"]
        assert all(c.is_dynamic for c in parent.children)
        assert all(c.task_order == -1 for c in parent.children)

    def test_repeated_task_uuid_does_not_re_graft(self) -> None:
        """A second v2_runner_on_start for the same UUID must not graft twice."""
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
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(_task_start("uuid-static", "Include tasks file"))
        state.handle_event(_task_start("uuid-dynamic", "Dynamic task A"))
        # Re-arriving event for the same task (e.g. retry under a different
        # phase) must not duplicate the dynamic child.
        state.handle_event(_runner_start("uuid-dynamic", "Dynamic task A"))

        assert len(parent.children) == 1

    def test_static_task_following_dynamic_resets_parent(self) -> None:
        """A subsequent matched preflight task replaces the parent cursor."""
        include_a = TaskDefinition(
            name="Include set A",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        include_b = TaskDefinition(
            name="Include set B",
            role=None,
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
                tasks=[include_a, include_b],
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())

        state.handle_event(_task_start("uuid-include-a", "Include set A"))
        state.handle_event(_task_start("uuid-a1", "Task A1"))
        state.handle_event(_task_start("uuid-include-b", "Include set B"))
        state.handle_event(_task_start("uuid-b1", "Task B1"))

        assert [c.name for c in include_a.children] == ["Task A1"]
        assert [c.name for c in include_b.children] == ["Task B1"]

    def test_orphan_dynamic_task_when_no_parent_seen_yet(self) -> None:
        """Unknown task before any preflight match is left orphan (no graft, no crash)."""
        sibling = TaskDefinition(
            name="Some other task",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[sibling]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())

        # No matched preflight task yet → unknown task has no parent. The
        # handler must accept the event without raising and without grafting
        # anywhere (no spurious child appears on unrelated definitions).
        state.handle_event(_task_start("uuid-orphan", "Mystery task"))

        assert sibling.children == []

    def test_grafting_works_under_v2_runner_on_start(self) -> None:
        """Free-strategy plays emit v2_runner_on_start instead of task_start.

        The grafting path must apply there too — otherwise free-strategy
        include_tasks dynamic children would never reach the definition tree.
        """
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
                id="1", name="Test", hosts="all", resolved_hosts=["web1"], tasks=[parent]
            )
        ]
        state = RunState(playbook="test.yml", definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(_runner_start("uuid-static", "Include tasks file"))
        state.handle_event(_runner_start("uuid-dynamic", "Dynamic task A"))

        assert len(parent.children) == 1
        assert parent.children[0].name == "Dynamic task A"
        assert parent.children[0].is_dynamic is True
        assert parent.children[0].task_order == -1

    def test_no_grafting_without_definitions(self) -> None:
        """With no preflight definitions there's no parent to graft under."""
        state = RunState(playbook="test.yml")
        state.handle_event(_play_start())
        # No definitions: every task is "unknown" but there's nothing to
        # attach to. Must not raise.
        state.handle_event(_task_start("uuid-a", "Task A"))
        state.handle_event(_task_start("uuid-b", "Task B"))

        assert state.definitions == []


class TestRuntimeIncludeDiscovery:
    """TC-094h / TC-094i: runtime include cache discovery from task.path."""

    def test_task_path_populates_include_cache(self, tmp_path: Path) -> None:
        """TC-094h: An unknown task.path triggers include cache population."""
        from ansible_aom.core.models import TaskDefinition

        include_file = tmp_path / "site.yml"
        include_file.write_text(
            "- name: Alpha\n  debug:\n    msg: a\n- name: Beta\n  debug:\n    msg: b\n"
        )
        parent = TaskDefinition(
            name="Include site",
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
        playbook_path = str(tmp_path / "play.yml")
        state = RunState(playbook=playbook_path, definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(
            _task_start_with_path(
                "uuid-include",
                "Include site",
                f"{include_file.name}:2",
            )
        )

        cache_key = str(include_file.resolve())
        assert cache_key in state._include_cache
        assert state._include_cache[cache_key].task_names == ["Alpha", "Beta"]

    def test_runtime_cache_reuses_preflight_entry(self, tmp_path: Path) -> None:
        """TC-094i: A second task hitting the same path reuses the cache."""
        from datetime import datetime, timezone

        from ansible_aom.core.models import IncludeCacheEntry, TaskDefinition

        include_file = tmp_path / "site.yml"
        include_file.write_text("- name: Beta\n  debug:\n    msg: b\n")
        cache_key = str(include_file.resolve())
        preflight_entry = IncludeCacheEntry(
            path=cache_key,
            task_names=["Beta"],
            role=None,
            parsed_at=datetime.now(timezone.utc),
        )
        parent = TaskDefinition(
            name="Include site",
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
        playbook_path = str(tmp_path / "play.yml")
        state = RunState(playbook=playbook_path, definitions=defs)
        state._include_cache[cache_key] = preflight_entry

        state.handle_event(_play_start())
        state.handle_event(
            _task_start_with_path(
                "uuid-include",
                "Include site",
                f"{include_file.name}:2",
            )
        )

        assert state._include_cache[cache_key] is preflight_entry


class TestIncludeRoleRuntimeGraft:
    """TC-096: ``include_role`` discovery at runtime.

    ``--list-tasks`` does not expand ``include_role`` directives — the
    preflight tree only sees the ``include_role:`` stub itself. When a
    role is included at runtime, its first task arrives with the
    ``"role : "`` prefix (e.g. ``"podman : Install podman"``). The
    grafting logic must use that prefix to discover the role's
    ``tasks/main.yml`` and graft every other role task as siblings
    under the same parent so the projection can show them all as
    pending instead of revealing them one at a time as each fires its
    own ``task_start`` event.
    """

    def test_first_role_task_reveals_all_role_tasks_as_pending_siblings(
        self, tmp_path: Path
    ) -> None:
        """The first runtime task from an ``include_role`` reveals the
        role's full task list as grafted siblings under the same
        parent. Without this, only the running task would be visible
        until each subsequent task fires its own ``task_start``.
        """
        role_dir = tmp_path / "roles" / "podman" / "tasks"
        role_dir.mkdir(parents=True)
        (role_dir / "main.yml").write_text(
            "- name: Install podman\n  debug: msg=1\n"
            "- name: Configure podman\n  debug: msg=2\n"
            "- name: Start podman\n  debug: msg=3\n"
        )
        parent = TaskDefinition(
            name="Apply podman role",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Setup rootless Podman",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        playbook_path = str(tmp_path / "site.yml")
        state = RunState(playbook=playbook_path, definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(_task_start("uuid-stub", "Apply podman role"))
        state.handle_event(_task_start("uuid-1", "podman : Install podman"))

        child_names = sorted(c.name for c in parent.children)
        assert child_names == [
            "podman : Configure podman",
            "podman : Install podman",
            "podman : Start podman",
        ], (
            "All three role tasks must appear as siblings under the "
            "include_role stub after the first runtime task reveals "
            "the role; got "
            f"{child_names}"
        )
        assert all(c.is_dynamic for c in parent.children), (
            "All grafted siblings must be marked dynamic so the projection "
            "treats them as runtime-discovered rather than preflight-known."
        )

    def test_grafted_sibling_carries_role_field_for_total_count(self, tmp_path: Path) -> None:
        """Grafted siblings under an include_role stub get the role
        field set so ``role_total_tasks`` counts them under the
        role header. The role-less parent branch in
        ``_graft_or_match_task`` sets ``role=<runtime role>`` instead
        of leaving it ``None`` (the pre-existing role-in-role branch
        only fires when the parent already has a role).
        """
        role_dir = tmp_path / "roles" / "podman" / "tasks"
        role_dir.mkdir(parents=True)
        (role_dir / "main.yml").write_text(
            "- name: Install podman\n  debug: msg=1\n- name: Configure podman\n  debug: msg=2\n"
        )
        parent = TaskDefinition(
            name="Apply podman role",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Setup rootless Podman",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        playbook_path = str(tmp_path / "site.yml")
        state = RunState(playbook=playbook_path, definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(_task_start("uuid-stub", "Apply podman role"))
        state.handle_event(_task_start("uuid-1", "podman : Install podman"))

        for child in parent.children:
            assert child.role == "podman", (
                f"Grafted child must carry role='podman' so the "
                f"projection's role_total_tasks counter keys on the "
                f"innermost role; got role={child.role!r} on {child.name!r}"
            )

    def test_subsequent_role_tasks_do_not_duplicate_siblings(self, tmp_path: Path) -> None:
        """When the second and third tasks of the role fire
        ``task_start`` events, the per-(parent, role) dedupe key in
        ``_grafted_role_names`` keeps the sibling list from growing
        past the role's real task count.
        """
        role_dir = tmp_path / "roles" / "podman" / "tasks"
        role_dir.mkdir(parents=True)
        (role_dir / "main.yml").write_text(
            "- name: Install podman\n  debug: msg=1\n"
            "- name: Configure podman\n  debug: msg=2\n"
            "- name: Start podman\n  debug: msg=3\n"
        )
        parent = TaskDefinition(
            name="Apply podman role",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Setup rootless Podman",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        playbook_path = str(tmp_path / "site.yml")
        state = RunState(playbook=playbook_path, definitions=defs)
        state.handle_event(_play_start())
        state.handle_event(_task_start("uuid-stub", "Apply podman role"))
        state.handle_event(_task_start("uuid-1", "podman : Install podman"))
        state.handle_event(_task_start("uuid-2", "podman : Configure podman"))
        state.handle_event(_task_start("uuid-3", "podman : Start podman"))

        assert len(parent.children) == 3, (
            "Sibling graft must run exactly once per (parent, role); "
            f"later task_starts must not duplicate siblings. Got "
            f"{[c.name for c in parent.children]}"
        )

    def test_tree_projection_shows_pending_role_tasks(self, tmp_path: Path) -> None:
        """End-to-end: the tree projection emits all role tasks as
        pending rows under the role header, with the role total
        reflecting the full task count.
        """
        from ansible_aom.core.tree_projection import TreeProjection

        role_dir = tmp_path / "roles" / "podman" / "tasks"
        role_dir.mkdir(parents=True)
        (role_dir / "main.yml").write_text(
            "- name: Install podman\n  debug: msg=1\n"
            "- name: Configure podman\n  debug: msg=2\n"
            "- name: Start podman\n  debug: msg=3\n"
            "- name: Verify podman\n  debug: msg=4\n"
        )
        parent = TaskDefinition(
            name="Apply podman role",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Setup rootless Podman",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        playbook_path = str(tmp_path / "site.yml")
        state = RunState(playbook=playbook_path, definitions=defs)
        state.handle_event(_play_start(play_id="1", name="Setup rootless Podman"))
        state.handle_event(_task_start("uuid-stub", "Apply podman role", play_id="1"))
        state.handle_event(_task_start("uuid-1", "podman : Install podman", play_id="1"))
        state.handle_event(_runner_start("uuid-1", "podman : Install podman"))

        projection = TreeProjection.from_run_state(state)
        lines = projection.tree_lines(budget=40)

        role_lines = [ln for ln in lines if ln.kind == "role"]
        assert role_lines, "role header must be emitted"
        assert role_lines[0].label == "role: podman (4 tasks)", (
            f"role total must reflect all 4 role tasks, not just the "
            f"currently running one; got {role_lines[0].label!r}"
        )

        task_lines = [ln for ln in lines if ln.kind == "task"]
        # The include_role stub itself ("Apply podman role") also renders
        # as a task row; we only care about the four role tasks here.
        task_labels = sorted(
            ln.label.split("  ")[0] for ln in task_lines if ln.label != "Apply podman role"
        )
        assert task_labels == sorted(
            ["Install podman", "Configure podman", "Start podman", "Verify podman"]
        ), f"All 4 role tasks must appear in the tree; got {task_labels}"


class TestIncludeRoleStubInsideOuterRole:
    """An ``include_role:`` stub that lives inside another role (e.g.
    ``angie_ssl_terminator : include_role: podman``) must graft the
    inner role's tasks as children of the stub itself, with ``role``
    set to the inner role name.

    Without the override in ``_graft_or_match_task`` the runtime
    prefix ``"angie_ssl_terminator : podman : Install podman"`` makes
    ``runtime_role_from_task_name`` return ``"angie_ssl_terminator"``
    (the outermost prefix), which equals ``parent.role``. The
    grafting branch then takes the ``else`` path, sets
    ``graft_role = parent.role = "angie_ssl_terminator"``, and
    passes ``"angie_ssl_terminator"`` to
    ``_graft_role_pending_siblings``. That call tries to discover
    the ``angie_ssl_terminator`` role instead of ``podman`` — and
    since the role prefix differs from the parent role, no
    siblings are grafted at all.

    The fix detects the include_role stub on the parent and uses
    the stub's target role name (``"podman"``) as
    ``runtime_role`` instead of the outermost runtime prefix.
    """

    def test_nested_include_role_grafts_inner_role_as_children(self, tmp_path: Path) -> None:
        role_dir = tmp_path / "roles" / "podman" / "tasks"
        role_dir.mkdir(parents=True)
        (role_dir / "main.yml").write_text(
            "- name: Install podman\n  debug: msg=1\n"
            "- name: Configure podman\n  debug: msg=2\n"
            "- name: Start podman\n  debug: msg=3\n"
        )
        # Preflight parent: an ``include_role: podman`` stub nested
        # inside the ``angie_ssl_terminator`` role. The runtime prefix
        # on incoming tasks carries ``"angie_ssl_terminator : "`` first,
        # so without the override the grafting would attach children
        # to the wrong role.
        parent = TaskDefinition(
            name="angie_ssl_terminator : include_role: podman",
            role="angie_ssl_terminator",
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Setup rootless Podman",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        playbook_path = str(tmp_path / "site.yml")
        state = RunState(playbook=playbook_path, definitions=defs)
        state.handle_event(_play_start())
        # First, the include_role stub itself fires — matches preflight
        # and sets the cursor to ``parent``.
        state.handle_event(_task_start("uuid-stub", "angie_ssl_terminator : include_role: podman"))
        # Then the first runtime task of the inner role fires.
        state.handle_event(_task_start("uuid-1", "angie_ssl_terminator : podman : Install podman"))
        state.handle_event(
            _runner_start("uuid-1", "angie_ssl_terminator : podman : Install podman")
        )

        # The buggy code (without the override) calls
        # ``_graft_role_pending_siblings(role_name="angie_ssl_terminator", ...)``
        # which then tries to discover an ``angie_ssl_terminator`` role
        # directory. That call may either fail to find it (returning
        # ``None``, leaving the children list empty) or graft
        # angie_ssl_terminator's tasks (the wrong role entirely). The
        # fixed code passes ``role_name="podman"`` and discovers the
        # podman role's tasks. Either way, the children list must
        # contain the three podman tasks in some form — never zero
        # children, and never angie_ssl_terminator's tasks.
        child_names = sorted(c.name for c in parent.children)
        assert len(parent.children) == 3, (
            "All three podman role tasks must be grafted as children "
            "of the include_role stub; the buggy code discovers the "
            f"wrong role and either skips the graft or grafts "
            f"angie_ssl_terminator's tasks. Got {len(parent.children)} "
            f"children: {child_names}"
        )

        # Every grafted child must carry role="podman" (the include_role
        # target), NOT role="angie_ssl_terminator" (which is what the
        # buggy code sets). The parent_role must be the outer role
        # so the projection renders podman as a sub-branch under
        # angie_ssl_terminator.
        for child in parent.children:
            assert child.role == "podman", (
                f"Grafted child must carry role='podman' (the "
                f"include_role target), got role={child.role!r} on "
                f"{child.name!r}"
            )
            assert child.parent_role == "angie_ssl_terminator", (
                f"Grafted child must carry parent_role='angie_ssl_terminator' "
                f"so the projection nests the inner role under the outer "
                f"role; got parent_role={child.parent_role!r} on {child.name!r}"
            )

    def test_role_task_with_template_variable_not_duplicated_as_pending_sibling(
        self, tmp_path: Path
    ) -> None:
        """When an included role has a task whose name contains Jinja templates
        (e.g. 'Get the user ID for {{ user }}') and runtime starts with the resolved name,
        the sibling grafter and tree projection must match them and not duplicate
        the pending template task."""
        from ansible_aom.core.tree import TreeProjection

        roles_dir = tmp_path / "roles"
        angie_dir = roles_dir / "angie"
        (angie_dir / "tasks").mkdir(parents=True)
        (angie_dir / "tasks" / "main.yml").write_text(
            "- name: Get the user ID for {{ sidecar_user }}\n"
            "  command: id -u\n"
            "- name: Configure sidecar\n"
            "  command: setup\n"
        )
        parent = TaskDefinition(
            name="include_role: angie",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1",
                name="Deploy VIP",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[parent],
            )
        ]
        playbook_path = str(tmp_path / "site.yml")
        state = RunState(playbook=playbook_path, definitions=defs)
        state.handle_event(_play_start(play_id="1", name="Deploy VIP"))
        state.handle_event(_task_start("uuid-stub", "include_role: angie", play_id="1"))
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-22T10:00:01Z",
                "task": {"id": "uuid-stub", "name": "include_role: angie"},
                "play": {"id": "1"},
                "hosts": {"web1": {"changed": False}},
            }
        )
        # First task of role arrives with RESOLVED name
        state.handle_event(
            _task_start("uuid-1", "angie : Get the user ID for sidecar_bob", play_id="1")
        )
        state.handle_event(_runner_start("uuid-1", "angie : Get the user ID for sidecar_bob"))

        # Check grafted children under parent
        child_names = [c.name for c in parent.children]
        # Should have exactly 2 tasks (the running task and the 1 pending sibling), NOT 3!
        assert len(parent.children) == 2, f"Expected 2 children under parent, got: {child_names}"
        assert not any("{{ sidecar_user }}" in name for name in child_names), (
            f"Pending sibling should not duplicate the running template task, got: {child_names}"
        )

        # Check TreeProjection
        proj = TreeProjection.from_run_state(state)
        lines = proj.tree_lines(budget=25)
        # Must have running task and pending sibling, and no unresolved template line
        labels = [ln.label for ln in lines]
        assert any("sidecar_bob" in lbl for lbl in labels)
        assert any("Configure sidecar" in lbl for lbl in labels)
        assert not any("{{ sidecar_user }}" in lbl for lbl in labels)

    def test_task_matching_scoped_to_current_play_not_cross_play(self) -> None:
        """When two plays share identical task names (e.g. 'Ensure firewalld is started'),
        tasks in Play 2 must match Play 2's TaskDefinition and never graft onto Play 1."""
        p1_t1 = TaskDefinition(
            name="Ensure firewalld is started",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        )
        p2_t1 = TaskDefinition(
            name="Ensure firewalld is started",
            role=None,
            tags=[],
            play_id="2",
            play_order=1,
            task_order=0,
        )
        defs = [
            PlayDefinition(
                id="1", name="Play 1", hosts="all", resolved_hosts=["web1"], tasks=[p1_t1]
            ),
            PlayDefinition(
                id="2", name="Play 2", hosts="all", resolved_hosts=["web1"], tasks=[p2_t1]
            ),
        ]
        state = RunState(playbook="site.yml", definitions=defs)
        # Play 1 runs
        state.handle_event(_play_start(play_id="1", name="Play 1"))
        state.handle_event(_task_start("p1-task", "Ensure firewalld is started", play_id="1"))
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-22T10:00:01Z",
                "task": {"id": "p1-task", "name": "Ensure firewalld is started"},
                "play": {"id": "1"},
                "hosts": {"web1": {"changed": False}},
            }
        )

        # Play 2 starts and runs its own task with the same name
        state.handle_event(_play_start(play_id="2", name="Play 2"))
        state.handle_event(_task_start("p2-task", "Ensure firewalld is started", play_id="2"))
        # Dynamic task arrives in Play 2
        state.handle_event(_task_start("p2-dynamic", "Reload systemd daemon for user", play_id="2"))

        # Must graft onto Play 2, NOT Play 1!
        assert len(p1_t1.children) == 0, (
            f"Play 1 task must have no grafted children, got {p1_t1.children}"
        )
        assert len(p2_t1.children) == 1, (
            f"Play 2 task must have 1 grafted child, got {p2_t1.children}"
        )
        assert p2_t1.children[0].name == "Reload systemd daemon for user"
