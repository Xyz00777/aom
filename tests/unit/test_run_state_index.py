"""TC-PERF-010..012 — name indexes on RunState for O(1) lookups.

``_graft_or_match_task`` currently does an O(T_def) linear scan via
``_iter_leaf_task_defs`` on every task-start event. With thousands of
tasks this is the dominant cost on the task-start path. ``_resolve_play_hosts``
has the same shape — O(P_def) name scan per task-start.

Both should be served from precomputed dicts built once when
``definitions`` is set.
"""

from __future__ import annotations

from ansible_aom.core import models
from ansible_aom.core.models import (
    PlayDefinition,
    RunState,
    TaskDefinition,
)


def _make_task(name: str, play_id: str = "p1", order: int = 0) -> TaskDefinition:
    return TaskDefinition(
        name=name,
        role=None,
        tags=[],
        play_id=play_id,
        play_order=0,
        task_order=order,
    )


def _make_play(
    play_id: str,
    name: str,
    tasks: list[TaskDefinition],
    hosts: list[str] | None = None,
) -> PlayDefinition:
    return PlayDefinition(
        id=play_id,
        name=name,
        hosts="all",
        resolved_hosts=hosts or ["host1"],
        tasks=tasks,
    )


class TestTaskDefIndex:
    def test_perf_010_index_built_on_definitions_assignment(self) -> None:
        """After definitions = [...], _task_def_index contains every leaf by name."""
        state = RunState(playbook="x.yml")
        tasks = [_make_task(f"t{i}", order=i) for i in range(5)]
        state.definitions = [_make_play("p1", "Play 1", tasks)]

        assert state._task_def_index is not None
        for task in tasks:
            assert state._task_def_index[task.name] is task

    def test_perf_011_graft_uses_index_not_linear_scan(self, monkeypatch) -> None:
        """_graft_or_match_task must NOT call _iter_leaf_task_defs.

        Mock _iter_leaf_task_defs to raise — _graft_or_match_task should
        still resolve a known name via the index without touching it.
        """
        state = RunState(playbook="x.yml")
        tasks = [_make_task(f"t{i}", order=i) for i in range(1000)]
        state.definitions = [_make_play("p1", "Play 1", tasks)]

        def _boom(plays):
            raise AssertionError("_iter_leaf_task_defs should not be called on the lookup path")

        monkeypatch.setattr(models, "_iter_leaf_task_defs", _boom)

        # Known name — should resolve via index, no scan triggered.
        state._graft_or_match_task("uuid-known", "t500")
        assert state._last_matched_task_def is not None
        assert state._last_matched_task_def.name == "t500"


class TestPlayDefIndex:
    def test_perf_012_resolve_play_hosts_o1(self) -> None:
        """_resolve_play_hosts uses _play_def_by_name dict lookup."""
        plays = []
        for i in range(50):
            plays.append(_make_play(f"p{i}", f"Play {i}", [], hosts=[f"h{i}"]))
        state = RunState(playbook="x.yml")
        state.definitions = plays

        assert state._play_def_by_name is not None
        assert "Play 17" in state._play_def_by_name

        from ansible_aom.core.models import PlayRunState, Status

        play_runtime = PlayRunState(play_id="opaque", name="Play 17", status=Status.RUNNING)
        hosts = state._resolve_play_hosts(play_runtime)
        assert hosts == ["h17"]

    def test_play_index_handles_unknown_play_name(self) -> None:
        """Unknown play name → empty list, just like the linear scan returned."""
        state = RunState(playbook="x.yml")
        state.definitions = [_make_play("p1", "Known Play", [])]

        from ansible_aom.core.models import PlayRunState, Status

        unknown = PlayRunState(play_id="opaque", name="Ghost Play", status=Status.RUNNING)
        assert state._resolve_play_hosts(unknown) == []


class TestIndexReassignment:
    def test_reassigning_definitions_rebuilds_index(self) -> None:
        state = RunState(playbook="x.yml")
        first = [_make_task("alpha", order=0)]
        state.definitions = [_make_play("p1", "P1", first)]
        assert "alpha" in state._task_def_index

        second = [_make_task("beta", order=0)]
        state.definitions = [_make_play("p2", "P2", second)]
        assert "beta" in state._task_def_index
        assert "alpha" not in state._task_def_index
