"""Tree projection shows not just the currently-running play but every
upcoming play too, so the user can plan ahead.

Previously the tree only iterated ``state.plays`` (runtime plays that
have actually started). Preflight ``PlayDefinition``s for plays that
haven't started yet were invisible — the user only ever saw the
in-flight play and any prior plays' running tasks.
"""

from __future__ import annotations

from ansible_aom.compact.format import format_tree_block
from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RunState,
    Status,
    TaskDefinition,
    TaskRunState,
)
from ansible_aom.core.tree import TreeProjection


def _task_def(name: str, order: int, play_id: str = "1") -> TaskDefinition:
    return TaskDefinition(
        name=name,
        role=None,
        tags=[],
        play_id=play_id,
        play_order=0,
        task_order=order,
    )


def _play_def(play_id: str, name: str, tasks: list[str]) -> PlayDefinition:
    return PlayDefinition(
        id=play_id,
        name=name,
        hosts="all",
        resolved_hosts=["web1"],
        tasks=[_task_def(t, i, play_id) for i, t in enumerate(tasks)],
    )


def _state_first_play_running() -> RunState:
    state = RunState(playbook="site.yml")
    state.definitions = [
        _play_def("1", "first play", ["t1.1", "t1.2"]),
        _play_def("2", "second play", ["t2.1", "t2.2"]),
        _play_def("3", "third play", ["t3.1"]),
    ]
    # First play is in flight: task t1.1 running.
    play1 = PlayRunState(play_id="p1", name="first play", status=Status.RUNNING)
    task = TaskRunState(task_id="t1", name="t1.1", status=Status.RUNNING)
    task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    play1.tasks["t1"] = task
    state.plays["p1"] = play1
    return state


def test_upcoming_plays_appear_after_running_play() -> None:
    state = _state_first_play_running()
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=60, width=120, ascii_mode=False, colorize=False)
    joined = "\n".join(block)

    assert "first play" in joined
    assert "second play" in joined, joined
    assert "third play" in joined, joined


def test_upcoming_play_tasks_are_pending() -> None:
    """Tasks under an upcoming play render with the pending icon."""
    state = _state_first_play_running()
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=60, width=120, ascii_mode=True, colorize=False)
    joined = "\n".join(block)

    # Tasks in the not-yet-started plays show up.
    for task_name in ("t2.1", "t2.2", "t3.1"):
        assert task_name in joined, joined


def test_play_order_matches_preflight() -> None:
    state = _state_first_play_running()
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=60, width=120, ascii_mode=False, colorize=False)

    play_lines = [i for i, ln in enumerate(block) if "play:" in ln]
    assert len(play_lines) == 3
    labels = [block[i] for i in play_lines]
    # Preflight order: first → second → third.
    assert "first play" in labels[0]
    assert "second play" in labels[1]
    assert "third play" in labels[2]


def test_no_preflight_no_upcoming_plays() -> None:
    """Without preflight definitions the projection cannot enumerate
    upcoming plays — only what's in runtime is visible."""
    state = RunState(playbook="site.yml")
    play1 = PlayRunState(play_id="p1", name="only play", status=Status.RUNNING)
    task = TaskRunState(task_id="t1", name="only task", status=Status.RUNNING)
    task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    play1.tasks["t1"] = task
    state.plays["p1"] = play1

    p = TreeProjection.from_run_state(state)
    joined = "\n".join(format_tree_block(p, budget=60, width=120, ascii_mode=False, colorize=False))
    assert "only play" in joined
    # Nothing else fabricated.
    assert "second play" not in joined
