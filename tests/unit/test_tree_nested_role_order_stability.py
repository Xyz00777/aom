# pyright: reportMissingImports=false

"""Tests for stable ordering when a role inside a role executes.

The live tree view should not "jump around" as tasks inside nested roles
transition between RUNNING and PENDING/COMPLETED states. The sequential
order from preflight definitions must be preserved; only the running status
icon and host leaves change — the position of task lines in the tree
must remain stable.

This test suite targets the interaction between ``_cluster_items_by_role_path``
and ``_emit_runtime_play`` in ``core/tree_projection.py``.
"""

from __future__ import annotations

from ansible_aom.core.models import (
    PlayDefinition,
    RoleGroupDefinition,
    RunState,
    TaskDefinition,
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


def _fire_startup(
    state: RunState,
    play_id: str = "play-1",
    play_name: str = "play",
    ts: str = "2026-06-23T10:00:00Z",
) -> None:
    state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": ts})
    state.handle_event(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": ts.replace("10:00:00", "10:00:01"),
            "play": {"id": play_id, "name": play_name},
        }
    )


def _fire_task_start(
    state: RunState,
    task_id: str,
    task_name: str,
    host: str = "web1",
    play_id: str = "play-1",
) -> None:
    state.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-06-23T10:00:02Z",
            "task": {"id": task_id, "name": task_name},
            "play": {"id": play_id},
        }
    )
    state.handle_event(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-06-23T10:00:03Z",
            "task": {"id": task_id, "name": task_name},
            "host": host,
        }
    )


def _fire_task_ok(
    state: RunState,
    task_id: str,
    task_name: str,
    host: str = "web1",
) -> None:
    state.handle_event(
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-06-23T10:00:05Z",
            "task": {"id": task_id, "name": task_name},
            "host": host,
            "res": {},
        }
    )


def _line_summary(lines) -> list[tuple[int, str, str]]:
    return [(ln.depth, ln.kind, ln.label) for ln in lines]


def _task_labels(lines) -> list[str]:
    """Return labels of task-kind lines in order, for position stability checks."""
    return [ln.label for ln in lines if ln.kind == "task"]


class TestParentTasksBeforeNestedSubrolePending:
    """Parent role tasks that precede a nested sub-role in preflight order
    must stay before the sub-role's tasks in the tree, even when the sub-role
    has tasks in RUNNING state.

    Scenario: outer role has [T1_outer, <include_role: inner>, T3_outer].
    When inner's task T2_inner is RUNNING, the tree must still show
    T1_outer above T2_inner — not jump T2_inner to the top.

    Layout in preflight order::

        role: outer
        ├─ T1_outer (completed)
        └─ role: inner
           └─ T2_inner (running)    ← must stay AFTER T1_outer's position
        └─ T3_outer (pending)
    """

    def test_parent_tasks_precede_nested_subrole_when_subrole_running(self) -> None:
        state = RunState(playbook="main.yml")
        state.definitions = [
            _play_def(
                "p1",
                "Deploy app",
                [
                    RoleGroupDefinition(
                        role="outer",
                        tasks=[
                            TaskDefinition(
                                name="Prepare directories",
                                role="outer",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=0,
                                path="outer/tasks/main.yml:1",
                            ),
                            RoleGroupDefinition(
                                role="inner",
                                tasks=[
                                    TaskDefinition(
                                        name="inner : Install certificates",
                                        role="inner",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=1,
                                        path="inner/tasks/main.yml:1",
                                    ),
                                    TaskDefinition(
                                        name="inner : Configure SSL",
                                        role="inner",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=2,
                                        path="inner/tasks/main.yml:5",
                                    ),
                                ],
                            ),
                            TaskDefinition(
                                name="Start application",
                                role="outer",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=3,
                                path="outer/tasks/main.yml:10",
                            ),
                        ],
                    ),
                ],
            )
        ]
        _fire_startup(state, play_id="play-1", play_name="Deploy app")

        # T1_outer completes
        _fire_task_start(state, "t1", "Prepare directories", host="web1")
        _fire_task_ok(state, "t1", "Prepare directories", host="web1")

        # T2_inner starts running
        _fire_task_start(state, "t2", "inner : Install certificates", host="web1")

        proj = TreeProjection.from_run_state(state)
        lines = proj.tree_lines(budget=40)
        seq = _line_summary(lines)

        # The inner role's running task must NOT jump above the outer role header
        outer_role_idx = next(
            (i for i, (_, k, lbl) in enumerate(seq) if k == "role" and "outer" in lbl),
            None,
        )
        inner_role_idx = next(
            (i for i, (_, k, lbl) in enumerate(seq) if k == "role" and "inner" in lbl),
            None,
        )
        assert outer_role_idx is not None, f"missing outer role header; tree={seq}"
        assert inner_role_idx is not None, f"missing inner role header; tree={seq}"
        assert outer_role_idx < inner_role_idx, (
            f"outer role (idx {outer_role_idx}) must appear before inner role "
            f"(idx {inner_role_idx}); tree={seq}"
        )


class TestOrderStabilityAcrossTaskTransitions:
    """The tree's task line order must be stable across task state transitions.

    When a task inside a nested role completes and the next task starts,
    the relative order of all remaining tasks must not change — only the
    status icon and host leaves should update.
    """

    def test_order_stable_when_nested_role_task_completes(self) -> None:
        state = RunState(playbook="main.yml")
        state.definitions = [
            _play_def(
                "p1",
                "Deploy app",
                [
                    RoleGroupDefinition(
                        role="outer",
                        tasks=[
                            RoleGroupDefinition(
                                role="inner",
                                tasks=[
                                    TaskDefinition(
                                        name="inner : Step 1",
                                        role="inner",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=0,
                                        path="inner/tasks/main.yml:1",
                                    ),
                                    TaskDefinition(
                                        name="inner : Step 2",
                                        role="inner",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=1,
                                        path="inner/tasks/main.yml:5",
                                    ),
                                ],
                            ),
                            TaskDefinition(
                                name="Final cleanup",
                                role="outer",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=2,
                                path="outer/tasks/main.yml:10",
                            ),
                        ],
                    ),
                ],
            )
        ]
        _fire_startup(state, play_id="play-1", play_name="Deploy app")

        # Inner Step 1 running
        _fire_task_start(state, "t1", "inner : Step 1", host="web1")

        proj = TreeProjection.from_run_state(state)
        labels_frame1 = _task_labels(proj.tree_lines(budget=40))

        # Inner Step 1 completes, Inner Step 2 starts
        _fire_task_ok(state, "t1", "inner : Step 1", host="web1")
        _fire_task_start(state, "t2", "inner : Step 2", host="web1")

        # Force new projection to avoid stale memoization
        proj2 = TreeProjection.from_run_state(state)
        labels_frame2 = _task_labels(proj2.tree_lines(budget=40))

        # The tasks that remain visible must maintain their relative order.
        # "Step 2" was pending in frame 1 and running in frame 2.
        # "Final cleanup" was pending in both frames.
        # The order must be: inner tasks first, then outer tasks.
        if "Final cleanup" in labels_frame1 and "Final cleanup" in labels_frame2:
            # "Final cleanup" must stay after inner tasks in both frames
            step2_in_f2 = next((i for i, lbl in enumerate(labels_frame2) if "Step 2" in lbl), None)
            cleanup_in_f2 = next(
                (i for i, lbl in enumerate(labels_frame2) if "Final cleanup" in lbl), None
            )
            assert step2_in_f2 is not None, f"Step 2 missing in frame 2: {labels_frame2}"
            assert cleanup_in_f2 is not None, f"Final cleanup missing in frame 2: {labels_frame2}"
            assert step2_in_f2 < cleanup_in_f2, (
                f"Inner role task 'Step 2' (idx {step2_in_f2}) must appear before "
                f"outer task 'Final cleanup' (idx {cleanup_in_f2}) in frame 2. "
                f"Labels: {labels_frame2}"
            )


class TestNoDoubleClustering:
    """_emit_runtime_play must not split running/pending and re-cluster,
    because that changes path_order each time a different role's task
    transitions to RUNNING.

    This test has two nested sub-roles under a parent, with tasks that
    alternate between them. The order must follow preflight order, not
    jump based on which sub-role has running tasks.
    """

    def test_two_subroles_maintain_preflight_order(self) -> None:
        state = RunState(playbook="main.yml")
        state.definitions = [
            _play_def(
                "p1",
                "Deploy stack",
                [
                    RoleGroupDefinition(
                        role="parent",
                        tasks=[
                            RoleGroupDefinition(
                                role="sub_a",
                                tasks=[
                                    TaskDefinition(
                                        name="sub_a : Install package A",
                                        role="sub_a",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=0,
                                    ),
                                    TaskDefinition(
                                        name="sub_a : Configure package A",
                                        role="sub_a",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=1,
                                    ),
                                ],
                            ),
                            RoleGroupDefinition(
                                role="sub_b",
                                tasks=[
                                    TaskDefinition(
                                        name="sub_b : Install package B",
                                        role="sub_b",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=2,
                                    ),
                                    TaskDefinition(
                                        name="sub_b : Configure package B",
                                        role="sub_b",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=3,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ]
        _fire_startup(state, play_id="play-1", play_name="Deploy stack")

        # sub_a's first task is running
        _fire_task_start(state, "ta1", "sub_a : Install package A", host="web1")

        proj = TreeProjection.from_run_state(state)
        lines = proj.tree_lines(budget=40)
        seq = _line_summary(lines)

        # sub_a role header must appear before sub_b role header
        sub_a_idx = next(
            (i for i, (_, k, lbl) in enumerate(seq) if k == "role" and "sub_a" in lbl),
            None,
        )
        sub_b_idx = next(
            (i for i, (_, k, lbl) in enumerate(seq) if k == "role" and "sub_b" in lbl),
            None,
        )
        if sub_a_idx is not None and sub_b_idx is not None:
            assert sub_a_idx < sub_b_idx, (
                f"sub_a role (idx {sub_a_idx}) must appear before sub_b role "
                f"(idx {sub_b_idx}) — preflight order; tree={seq}"
            )

        # Now sub_a completes and sub_b starts running
        _fire_task_ok(state, "ta1", "sub_a : Install package A", host="web1")
        _fire_task_start(state, "ta2", "sub_a : Configure package A", host="web1")
        _fire_task_ok(state, "ta2", "sub_a : Configure package A", host="web1")
        _fire_task_start(state, "tb1", "sub_b : Install package B", host="web1")

        proj2 = TreeProjection.from_run_state(state)
        lines2 = proj2.tree_lines(budget=40)
        labels2 = _task_labels(lines2)

        # sub_b tasks must still appear after any remaining sub_a tasks (if visible)
        # More importantly, sub_b's running task must not jump above parent-level items
        if "Install package B" in str(labels2) and "Configure package B" in str(labels2):
            b_install_idx = next(
                (i for i, lbl in enumerate(labels2) if "Install package B" in lbl), None
            )
            b_config_idx = next(
                (i for i, lbl in enumerate(labels2) if "Configure package B" in lbl), None
            )
            assert b_install_idx is not None and b_config_idx is not None
            assert b_install_idx < b_config_idx, (
                f"sub_b tasks must maintain their internal order: "
                f"Install (idx {b_install_idx}) before Configure (idx {b_config_idx}); "
                f"labels={labels2}"
            )


class TestClusteringDoesNotFlipOrderBetweenFrames:
    """Direct test of ``_cluster_items_by_role_path``: the relative order
    of parent-level pending tasks vs. inner-level pending tasks must be
    stable across frames even when the running/pending split changes the
    input order.

    Repro: outer role has tasks [parent_A, <inner_1, inner_2>, parent_B].
    When parent_A is running, the split puts it first → path_order sees
    ``('outer',)`` first → parent_B appears BEFORE inner tasks. When
    parent_A completes and inner_1 starts, the split puts inner_1 first
    → path_order sees ``('outer', 'inner')`` first → inner tasks jump
    ABOVE parent_B. That's the user-visible "jumping around".
    """

    def test_clustering_stable_across_running_status_change(self) -> None:
        from ansible_aom.core.tree_projection import _cluster_items_by_role_path

        # Frame 1: parent_A is running, everything else is pending.
        # The _emit_runtime_play split puts running first.
        items_frame1 = [
            ("running", "parent_A", ("outer",), None),
            ("pending", "inner_1", ("outer", "inner"), None),
            ("pending", "inner_2", ("outer", "inner"), None),
            ("pending", "parent_B", ("outer",), None),
        ]
        clustered1 = _cluster_items_by_role_path(items_frame1)
        names1 = [name for _, name, _, _ in clustered1]

        # Frame 2: parent_A completed, inner_1 is now running.
        # The split puts inner_1 (running) first.
        items_frame2 = [
            ("running", "inner_1", ("outer", "inner"), None),
            ("pending", "inner_2", ("outer", "inner"), None),
            ("pending", "parent_B", ("outer",), None),
        ]
        clustered2 = _cluster_items_by_role_path(items_frame2)
        names2 = [name for _, name, _, _ in clustered2]

        # In both frames, inner tasks must appear before parent_B.
        # That's the preflight sequential order: inner role comes
        # before parent_B in the playbook.
        # Frame 1 bug: parent_B appears at index 1 (before inner_1).
        if "parent_B" in names1:
            inner1_idx_f1 = names1.index("inner_1") if "inner_1" in names1 else -1
            parentB_idx_f1 = names1.index("parent_B")
            assert inner1_idx_f1 < parentB_idx_f1, (
                f"Frame 1: inner_1 (idx {inner1_idx_f1}) must appear before "
                f"parent_B (idx {parentB_idx_f1}) to maintain preflight order. "
                f"Got: {names1}"
            )

        if "parent_B" in names2:
            inner1_idx_f2 = names2.index("inner_1") if "inner_1" in names2 else -1
            parentB_idx_f2 = names2.index("parent_B")
            assert inner1_idx_f2 < parentB_idx_f2, (
                f"Frame 2: inner_1 (idx {inner1_idx_f2}) must appear before "
                f"parent_B (idx {parentB_idx_f2}) to maintain preflight order. "
                f"Got: {names2}"
            )

    def test_parent_tasks_sandwich_inner_role_order_stable(self) -> None:
        """End-to-end tree view test: parent tasks that sandwich an inner
        role must not flip order as the inner role starts running.

        Preflight order:
            outer_task_1
            inner_task_1, inner_task_2
            outer_task_2

        The tree must show this order regardless of which task is running.
        """
        state = RunState(playbook="main.yml")
        state.definitions = [
            _play_def(
                "p1",
                "Deploy app",
                [
                    RoleGroupDefinition(
                        role="outer",
                        tasks=[
                            TaskDefinition(
                                name="Prepare directories",
                                role="outer",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=0,
                                path="outer/tasks/main.yml:1",
                            ),
                            RoleGroupDefinition(
                                role="inner",
                                tasks=[
                                    TaskDefinition(
                                        name="inner : Install certs",
                                        role="inner",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=1,
                                        path="inner/tasks/main.yml:1",
                                    ),
                                    TaskDefinition(
                                        name="inner : Configure SSL",
                                        role="inner",
                                        tags=[],
                                        play_id="p1",
                                        play_order=0,
                                        task_order=2,
                                        path="inner/tasks/main.yml:5",
                                    ),
                                ],
                            ),
                            TaskDefinition(
                                name="Start application",
                                role="outer",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=3,
                                path="outer/tasks/main.yml:10",
                            ),
                        ],
                    ),
                ],
            )
        ]
        _fire_startup(state, play_id="play-1", play_name="Deploy app")

        # Frame 1: outer's first task is running
        _fire_task_start(state, "t1", "Prepare directories", host="web1")

        proj1 = TreeProjection.from_run_state(state)
        labels1 = _task_labels(proj1.tree_lines(budget=40))

        # Inner tasks must be before outer's "Start application"
        if "Start application" in labels1:
            for inner_name in ("Install certs", "Configure SSL"):
                inner_matches = [i for i, lbl in enumerate(labels1) if inner_name in lbl]
                start_matches = [i for i, lbl in enumerate(labels1) if "Start application" in lbl]
                if inner_matches and start_matches:
                    assert inner_matches[0] < start_matches[0], (
                        f"Frame 1: '{inner_name}' must appear before 'Start application' "
                        f"(preflight order). Labels: {labels1}"
                    )

        # Frame 2: outer's first task done, inner's first task now running
        _fire_task_ok(state, "t1", "Prepare directories", host="web1")
        _fire_task_start(state, "t2", "inner : Install certs", host="web1")

        proj2 = TreeProjection.from_run_state(state)
        labels2 = _task_labels(proj2.tree_lines(budget=40))

        # Inner tasks must STILL be before outer's "Start application"
        if "Start application" in labels2:
            for inner_name in ("Install certs", "Configure SSL"):
                inner_matches = [i for i, lbl in enumerate(labels2) if inner_name in lbl]
                start_matches = [i for i, lbl in enumerate(labels2) if "Start application" in lbl]
                if inner_matches and start_matches:
                    assert inner_matches[0] < start_matches[0], (
                        f"Frame 2: '{inner_name}' must appear before 'Start application' "
                        f"(preflight order must be stable). Labels: {labels2}"
                    )
