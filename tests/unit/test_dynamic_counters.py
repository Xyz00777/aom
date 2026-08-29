"""Unit tests for dynamic counter accuracy (TC-310–TC-317).

Tests that ``_count_tasks``, ``count_total_tasks``, ``count_total_tasks_seen``,
and ``count_completed_tasks`` correctly handle dynamic ``include_tasks`` children
grafted onto ``TaskDefinition.children`` at runtime.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.compact.format import (
    count_completed_tasks,
    count_total_tasks,
    count_total_tasks_seen,
)
from ansible_aom.core.models import (
    HostRunState,
    IncludeCacheEntry,
    PlayDefinition,
    PlayRunState,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
    TaskRunState,
)


# ---------------------------------------------------------------------------
# TC-310: count_total_tasks counts dynamic children from .children
# ---------------------------------------------------------------------------
def test_total_tasks_counts_dynamic_children() -> None:
    """3 static + 5 dynamic children under one parent → total = 8."""
    parent = TaskDefinition(
        name="Include tasks file",
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=0,
    )
    for i in range(5):
        parent.children.append(
            TaskDefinition(
                name=f"Dynamic {i}",
                role=None,
                tags=[],
                play_id="1",
                play_order=0,
                task_order=-1,
                is_dynamic=True,
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
    assert count_total_tasks(defs) == 5  # parent stub skipped, only 5 dynamic children count


# ---------------------------------------------------------------------------
# TC-311: no dynamic children → returns static count only
# ---------------------------------------------------------------------------
def test_total_tasks_no_dynamic_children() -> None:
    """Three static tasks with no dynamic children → total = 3."""
    defs = [
        PlayDefinition(
            id="1",
            name="Test",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name="Task A", role=None, tags=[], play_id="1", play_order=0, task_order=0
                ),
                TaskDefinition(
                    name="Task B", role=None, tags=[], play_id="1", play_order=0, task_order=1
                ),
                TaskDefinition(
                    name="Task C", role=None, tags=[], play_id="1", play_order=0, task_order=2
                ),
            ],
        )
    ]
    assert count_total_tasks(defs) == 3


# ---------------------------------------------------------------------------
# TC-312: count_total_tasks_seen includes include cache count
# ---------------------------------------------------------------------------
def test_total_tasks_seen_includes_include_cache() -> None:
    """When include cache has entries, they contribute to the denominator."""
    defs: list[PlayDefinition] = [
        PlayDefinition(
            id="1",
            name="Test",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name="Static task", role=None, tags=[], play_id="1", play_order=0, task_order=0
                ),
            ],
        )
    ]
    state = RunState(playbook="test.yml", definitions=defs)
    state._include_cache["includes/tasks.yml"] = IncludeCacheEntry(
        path="includes/tasks.yml",
        task_names=["Dynamic A", "Dynamic B", "Dynamic C"],
        role=None,
        parsed_at=datetime.now(timezone.utc),
    )
    state._include_cache["includes/more.yml"] = IncludeCacheEntry(
        path="includes/more.yml",
        task_names=["Dynamic D", "Dynamic E"],
        role=None,
        parsed_at=datetime.now(timezone.utc),
    )

    # preflight = 1, runtime = 0 (no plays populated), cached = 5
    result = count_total_tasks_seen(defs, state)
    assert result == 5


# ---------------------------------------------------------------------------
# TC-313: count_total_tasks_seen without cache falls back to preflight+runtime max
# ---------------------------------------------------------------------------
def test_total_tasks_seen_no_cache_falls_back_to_preflight_runtime_max() -> None:
    """Without include cache, denominator = max(preflight, runtime)."""
    defs: list[PlayDefinition] = [
        PlayDefinition(
            id="1",
            name="Test",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name="Task 1", role=None, tags=[], play_id="1", play_order=0, task_order=0
                ),
                TaskDefinition(
                    name="Task 2", role=None, tags=[], play_id="1", play_order=0, task_order=1
                ),
            ],
        )
    ]
    state = RunState(playbook="test.yml", definitions=defs)

    # No runtime plays populated → max(preflight=2, runtime=0, cached=0) = 2
    result = count_total_tasks_seen(defs, state)
    assert result == 2

    # Populate runtime with more tasks than preflight
    play_state = PlayRunState(play_id="1", name="Test")
    for i in range(5):
        play_state.tasks[f"uuid-{i}"] = TaskRunState(task_id=f"uuid-{i}", name=f"Task {i}")
    state.plays["1"] = play_state

    # max(preflight=2, runtime=5, cached=0) = 5
    result = count_total_tasks_seen(defs, state)
    assert result == 5


# ---------------------------------------------------------------------------
# TC-314: count_completed_tasks counts dynamic children whose hosts are terminal
# ---------------------------------------------------------------------------
def test_completed_tasks_counts_dynamic_children() -> None:
    """Dynamic task children with terminal hosts contribute to completed count."""
    defs = [
        PlayDefinition(
            id="1",
            name="Test",
            hosts="all",
            resolved_hosts=["web1", "web2"],
            tasks=[
                TaskDefinition(
                    name="Include tasks",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=0,
                ),
            ],
        )
    ]
    state = RunState(playbook="test.yml", definitions=defs)

    play_state = PlayRunState(play_id="1", name="Test")
    # Static task: both hosts terminal → completed
    static_task = TaskRunState(task_id="uuid-0", name="Include tasks")
    static_task.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    static_task.hosts["web2"] = HostRunState(hostname="web2", status=Status.OK)
    play_state.tasks["uuid-0"] = static_task

    # Dynamic child 1: both hosts terminal → completed
    dyn1 = TaskRunState(task_id="uuid-dyn-1", name="Dynamic task A")
    dyn1.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    dyn1.hosts["web2"] = HostRunState(hostname="web2", status=Status.OK)
    play_state.tasks["uuid-dyn-1"] = dyn1

    # Dynamic child 2: one host still RUNNING → not completed
    dyn2 = TaskRunState(task_id="uuid-dyn-2", name="Dynamic task B")
    dyn2.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    dyn2.hosts["web2"] = HostRunState(hostname="web2", status=Status.RUNNING)
    play_state.tasks["uuid-dyn-2"] = dyn2

    state.plays["1"] = play_state

    # 1 static + 1 dynamic completed = 2 total completed
    assert count_completed_tasks(state) == 2


# ---------------------------------------------------------------------------
# TC-315: import_tasks (static) are already counted
# ---------------------------------------------------------------------------
def test_total_tasks_counts_import_tasks_as_static() -> None:
    """import_tasks are expanded by --list-tasks — they appear as regular
    static TaskDefinitions without children.  Verify they are counted
    normally."""
    defs = [
        PlayDefinition(
            id="1",
            name="Test",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name="Imported task 1",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=0,
                ),
                TaskDefinition(
                    name="Imported task 2",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=1,
                ),
                TaskDefinition(
                    name="Imported task 3",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=2,
                ),
            ],
        )
    ]
    assert count_total_tasks(defs) == 3


# ---------------------------------------------------------------------------
# TC-316: RoleGroupDefinition + dynamic children
# ---------------------------------------------------------------------------
def test_total_tasks_with_role_group_and_dynamic_children() -> None:
    """A play with RoleGroupDefinition entries and a TaskDefinition that
    has dynamic children.  Both expansion paths must work."""
    role_tasks = [
        TaskDefinition(
            name="Role task 1",
            role="myrole",
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
        ),
        TaskDefinition(
            name="Role task 2",
            role="myrole",
            tags=[],
            play_id="1",
            play_order=0,
            task_order=1,
        ),
        TaskDefinition(
            name="Role task 3",
            role="myrole",
            tags=[],
            play_id="1",
            play_order=0,
            task_order=2,
        ),
    ]
    role_group = RoleGroupDefinition(role="myrole", tasks=role_tasks)

    parent = TaskDefinition(
        name="Include tasks file",
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=3,
    )
    parent.children.append(
        TaskDefinition(
            name="Dynamic A",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=-1,
            is_dynamic=True,
        )
    )
    parent.children.append(
        TaskDefinition(
            name="Dynamic B",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=-1,
            is_dynamic=True,
        )
    )

    defs = [
        PlayDefinition(
            id="1",
            name="Test",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[role_group, parent],
        )
    ]

    # Role group: 3 leaf tasks.  Parent stub skipped, 2 dynamic children.  Total = 5.
    assert count_total_tasks(defs) == 5


# ---------------------------------------------------------------------------
# TC-317: Empty definitions → returns 0
# ---------------------------------------------------------------------------
def test_total_tasks_empty_definitions() -> None:
    """Empty definition list → 0 (renderer uses this to suppress the segment)."""
    assert count_total_tasks([]) == 0


# ---------------------------------------------------------------------------
# Multi-play test: dynamic children across multiple plays
# ---------------------------------------------------------------------------
def test_total_tasks_multi_play_with_dynamic_children() -> None:
    """Dynamic children in multiple plays are all counted."""
    parent1 = TaskDefinition(
        name="Include A",
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=0,
    )
    parent1.children.append(
        TaskDefinition(
            name="Dyn A1",
            role=None,
            tags=[],
            play_id="1",
            play_order=0,
            task_order=-1,
            is_dynamic=True,
        )
    )

    parent2 = TaskDefinition(
        name="Include B",
        role=None,
        tags=[],
        play_id="2",
        play_order=1,
        task_order=0,
    )
    parent2.children.append(
        TaskDefinition(
            name="Dyn B1",
            role=None,
            tags=[],
            play_id="2",
            play_order=1,
            task_order=-1,
            is_dynamic=True,
        )
    )
    parent2.children.append(
        TaskDefinition(
            name="Dyn B2",
            role=None,
            tags=[],
            play_id="2",
            play_order=1,
            task_order=-1,
            is_dynamic=True,
        )
    )

    defs = [
        PlayDefinition(
            id="1",
            name="Play 1",
            hosts="web",
            resolved_hosts=["web1"],
            tasks=[parent1],
        ),
        PlayDefinition(
            id="2",
            name="Play 2",
            hosts="db",
            resolved_hosts=["db1"],
            tasks=[parent2],
        ),
    ]

    # Play 1: parent stub skipped, 1 dynamic child = 1.  Play 2: parent stub skipped, 2 children = 2.  Total = 3.
    assert count_total_tasks(defs) == 3


# ---------------------------------------------------------------------------
# Nested include stub: a stub whose children are themselves stubs must
# recurse into grandchildren (Fix A). The status-bar denominator and
# count_leaf_tasks must count the grandchildren leaves, not len(direct).
# ---------------------------------------------------------------------------
def test_total_tasks_counts_nested_include_stub_grandchildren() -> None:
    """A stub → child stub → grandchildren chain: count_total_tasks counts
    the grandchildren leaves, not len(direct children)."""
    grandchild1 = TaskDefinition(
        name="Grandchild 1",
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=-1,
        is_dynamic=True,
    )
    grandchild2 = TaskDefinition(
        name="Grandchild 2",
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=-1,
        is_dynamic=True,
    )
    child_stub = TaskDefinition(
        name="Include podman role for user setup",
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=-1,
        is_dynamic=True,
        children=[grandchild1, grandchild2],
    )
    parent_stub = TaskDefinition(
        name="Include setup tasks",
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=0,
        children=[child_stub],
    )
    defs = [
        PlayDefinition(
            id="1",
            name="Test",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[parent_stub],
        )
    ]
    # Both stubs are skipped; the two grandchildren leaves count.
    assert count_total_tasks(defs) == 2


def test_count_leaf_tasks_counts_nested_include_stub_grandchildren() -> None:
    """count_leaf_tasks counts the grandchildren leaves of a nested include
    stub chain, matching count_total_tasks and the tree's per-play sum."""
    from ansible_aom.core.run_state import count_leaf_tasks

    grandchild1 = TaskDefinition(
        name="Grandchild 1",
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=-1,
        is_dynamic=True,
    )
    grandchild2 = TaskDefinition(
        name="Grandchild 2",
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=-1,
        is_dynamic=True,
    )
    child_stub = TaskDefinition(
        name="Include podman role for user setup",
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=-1,
        is_dynamic=True,
        children=[grandchild1, grandchild2],
    )
    parent_stub = TaskDefinition(
        name="Include setup tasks",
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=0,
        children=[child_stub],
    )
    defs = [
        PlayDefinition(
            id="1",
            name="Test",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[parent_stub],
        )
    ]
    assert count_leaf_tasks(defs) == 2


def test_count_leaf_tasks_excludes_meta_tasks() -> None:
    """count_leaf_tasks excludes meta tasks (they never emit task-start
    events), matching the tree's per-play sum."""
    from ansible_aom.core.run_state import count_leaf_tasks

    defs = [
        PlayDefinition(
            id="1",
            name="Test",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name="Install nginx",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=0,
                ),
                TaskDefinition(
                    name="meta: flush_handlers",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=1,
                ),
            ],
        )
    ]
    assert count_leaf_tasks(defs) == 1
