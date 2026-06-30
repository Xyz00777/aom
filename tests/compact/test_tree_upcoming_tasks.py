"""Tree projection shows the currently-running task plus every task
yet to come in the active play. Completed tasks are dropped — they
already appear in the streaming log above the panel.

Pending tasks render with PENDING status (dim square) so the user can
see what's coming next at a glance.
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


def _task_def(name: str, order: int) -> TaskDefinition:
    return TaskDefinition(
        name=name,
        role=None,
        tags=[],
        play_id="1",
        play_order=0,
        task_order=order,
    )


def _state_with_play(
    play_name: str,
    preflight_task_names: list[str],
    runtime_tasks: dict[str, Status],
    resolved_hosts: list[str] | None = None,
) -> RunState:
    """Build a RunState with one play and one host.

    ``runtime_tasks`` maps preflight task name → terminal status for the
    single host. Status.RUNNING means the host is currently running it.
    A name not in the dict means the task hasn't started yet.
    """
    state = RunState(playbook="site.yml")
    state.definitions = [
        PlayDefinition(
            id="1",
            name=play_name,
            hosts="all",
            resolved_hosts=resolved_hosts or ["web1"],
            tasks=[_task_def(n, i) for i, n in enumerate(preflight_task_names)],
        )
    ]
    play = PlayRunState(play_id="play-1", name=play_name, status=Status.RUNNING)
    state.start_time = None  # leave RUNNING but not ended
    for i, name in enumerate(preflight_task_names):
        if name not in runtime_tasks:
            continue
        task = TaskRunState(task_id=f"t-{i}", name=name, status=Status.RUNNING)
        task.hosts["web1"] = HostRunState(hostname="web1", status=runtime_tasks[name])
        play.tasks[task.task_id] = task
    state.plays["play-1"] = play
    return state


def test_completed_tasks_not_in_tree() -> None:
    state = _state_with_play(
        play_name="deploy",
        preflight_task_names=["t0", "t1", "t2", "t3"],
        runtime_tasks={"t0": Status.OK, "t1": Status.OK, "t2": Status.RUNNING},
    )
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False)
    joined = "\n".join(block)
    assert "t0" not in joined, joined
    assert "t1" not in joined, joined


def test_running_task_visible() -> None:
    state = _state_with_play(
        play_name="deploy",
        preflight_task_names=["t0", "t1", "t2"],
        runtime_tasks={"t0": Status.OK, "t1": Status.RUNNING},
    )
    p = TreeProjection.from_run_state(state)
    joined = "\n".join(format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False))
    assert "t1" in joined


def test_upcoming_tasks_visible_after_running() -> None:
    state = _state_with_play(
        play_name="deploy",
        preflight_task_names=["t0", "t1", "t2", "t3", "t4"],
        runtime_tasks={"t0": Status.OK, "t1": Status.OK, "t2": Status.RUNNING},
    )
    p = TreeProjection.from_run_state(state)
    joined = "\n".join(format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False))
    assert "t2" in joined, joined
    assert "t3" in joined, joined
    assert "t4" in joined, joined


def test_upcoming_tasks_marked_pending() -> None:
    """Pending tasks render with the PENDING status icon (□ or ASCII '.')."""
    state = _state_with_play(
        play_name="deploy",
        preflight_task_names=["t1", "t2", "t3"],
        runtime_tasks={"t1": Status.RUNNING},
    )
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=True, colorize=False)
    joined = "\n".join(block)
    # Pending tasks use the ASCII pending icon "." in ASCII mode.
    # Each of t2 and t3 should appear on a line carrying the pending glyph.
    for pending in ("t2", "t3"):
        line = next(ln for ln in block if pending in ln)
        # PENDING in ASCII mode is "."
        assert " . " in line or line.lstrip("-+ |\\").startswith("."), line


def test_no_preflight_falls_back_to_running_only() -> None:
    """Without preflight definitions the projection cannot enumerate
    upcoming tasks — emit only what we have at runtime."""
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="play-1", name="deploy", status=Status.RUNNING)
    task = TaskRunState(task_id="t1", name="only one", status=Status.RUNNING)
    task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    play.tasks["t1"] = task
    state.plays["play-1"] = play

    p = TreeProjection.from_run_state(state)
    joined = "\n".join(format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False))
    assert "only one" in joined


def test_all_completed_falls_back_to_first_pending() -> None:
    """All preflight tasks completed, more coming → show the next pending."""
    state = _state_with_play(
        play_name="deploy",
        preflight_task_names=["t0", "t1", "t2"],
        runtime_tasks={"t0": Status.OK, "t1": Status.OK},
    )
    p = TreeProjection.from_run_state(state)
    joined = "\n".join(format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False))
    # t2 is still pending — it must surface so the user sees what's
    # coming even when no task is currently running.
    assert "t2" in joined, joined
