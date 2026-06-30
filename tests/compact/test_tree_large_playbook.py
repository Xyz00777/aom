"""Tree projection with large playbooks: budget saturation and
completed-task removal at scale.

A playbook with 100+ tasks on multi-host inventory saturates the
tree budget (~40 lines on an 80-row terminal). This suite verifies
that completed tasks are correctly removed from the unbounded tree
at every stage of the playbook, and that the truncation logic
does not mask the removals.
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
    total: int,
    *,
    completed: int = 0,
    running: int | None = None,
    host_count: int = 5,
) -> RunState:
    """Build a RunState with one play of ``total`` preflight tasks.

    First ``completed`` tasks have all hosts in terminal (Status.OK)
    state. The ``running`` task (defaults to ``completed`` if not given)
    has all hosts RUNNING. Remaining tasks (after running) are pending
    (no runtime entry at all).

    Args:
        total: Number of preflight tasks.
        completed: Number of completed tasks at the front.
        running: Index of the running task (defaults to ``completed``).
        host_count: Number of hosts (default 5).
    """
    if running is None:
        running = completed

    state = RunState(playbook="site.yml")
    state.definitions = [
        PlayDefinition(
            id="1",
            name="deploy",
            hosts="all",
            resolved_hosts=[f"host{i}" for i in range(host_count)],
            tasks=[_task_def(f"task-{i:04d}", i) for i in range(total)],
        )
    ]
    play = PlayRunState(play_id="play-1", name="deploy", status=Status.RUNNING)
    state.start_time = None  # leave RUNNING but not ended

    # Create runtime entries for completed + running tasks
    for i in range(total):
        if i < completed:
            # Completed: all hosts terminal
            task = TaskRunState(
                task_id=f"t-{i:04d}",
                name=f"task-{i:04d}",
                status=Status.RUNNING,  # tasks stay RUNNING under free; classify uses host check
            )
            for h in range(host_count):
                task.hosts[f"host{h}"] = HostRunState(hostname=f"host{h}", status=Status.OK)
            play.tasks[task.task_id] = task
        elif i == running:
            # Running: all hosts RUNNING
            task = TaskRunState(
                task_id=f"t-{i:04d}",
                name=f"task-{i:04d}",
                status=Status.RUNNING,
            )
            for h in range(host_count):
                task.hosts[f"host{h}"] = HostRunState(hostname=f"host{h}", status=Status.RUNNING)
            play.tasks[task.task_id] = task
        # Tasks > running have no runtime entry → pending by classify

    state.plays["play-1"] = play
    return state


# --- End-to-end: completed tasks are removed regardless of budget ------------


def test_completed_tasks_removed_100_tasks_5_hosts_over_budget() -> None:
    """With 65/100 tasks completed (still over budget), completed tasks
    must NOT appear in the rendered tree."""
    state = _state_with_play(100, completed=65)
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False)
    joined = "\n".join(block)

    # Completed tasks must be absent
    for i in range(65):
        assert f"task-{i:04d}" not in joined, f"completed task-{i:04d} visible in tree:\n{joined}"
    # Running task must be present
    assert "task-0065" in joined, f"running task missing:\n{joined}"
    # Some pending tasks should be present (budget allows ~30 pending)
    assert "task-0066" in joined, f"first pending task missing:\n{joined}"


def test_completed_tasks_removed_under_budget() -> None:
    """With 90/100 tasks completed (well under budget), completed tasks
    must NOT appear and all remaining pending tasks must be visible."""
    state = _state_with_play(100, completed=90)
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False)
    joined = "\n".join(block)

    for i in range(90):
        assert f"task-{i:04d}" not in joined, f"completed task-{i:04d} visible in tree:\n{joined}"
    assert "task-0090" in joined, f"running task missing:\n{joined}"
    # All remaining pending tasks should be visible (under budget)
    assert "task-0091" in joined, f"pending task missing:\n{joined}"
    assert "task-0099" in joined, f"last pending task missing:\n{joined}"


def test_tree_content_changes_as_tasks_complete() -> None:
    """Simulate progression from task-0000 running to task-0065 running.
    At each step, only the running + pending tasks appear, never completed ones.

    This is the key regression test for "stops removing finished tasks":
    at no point should a completed task leak into the visible tree.
    """
    for completed in (0, 10, 30, 50, 65, 80, 95):
        state = _state_with_play(100, completed=completed)
        p = TreeProjection.from_run_state(state)
        block = format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False)
        joined = "\n".join(block)

        # Verify ALL completed tasks are absent
        for i in range(completed):
            assert f"task-{i:04d}" not in joined, (
                f"[completed={completed}] completed task-{i:04d} visible:\n{joined}"
            )
        # Running task must be present
        assert f"task-{completed:04d}" in joined, (
            f"[completed={completed}] running task missing:\n{joined}"
        )


def test_tree_shrinks_when_unbounded_fits_budget() -> None:
    """When enough tasks complete that the unbounded tree fits under
    budget, the rendered tree visibly shrinks (fewer lines)."""
    # Budget = 40; with 5 hosts, unbounded tree hits 40 at ~68 completed
    state_over = _state_with_play(100, completed=60)
    state_fits = _state_with_play(100, completed=75)

    p_over = TreeProjection.from_run_state(state_over)
    p_fits = TreeProjection.from_run_state(state_fits)

    block_over = format_tree_block(p_over, budget=40, width=120, ascii_mode=False, colorize=False)
    block_fits = format_tree_block(p_fits, budget=40, width=120, ascii_mode=False, colorize=False)

    # Both trees must be valid
    assert len(block_over) > 0
    assert len(block_fits) > 0

    # The "fits" tree must have fewer lines (not truncated to budget ceiling)
    # At 60 completed + 5 hosts + running: unbounded ~ 46 lines → still truncated to 40
    # At 75 completed + 5 hosts + running: unbounded ~ 31 lines → fits under 40
    assert len(block_fits) < len(block_over), (
        f"expected fits({len(block_fits)}) < over({len(block_over)})"
    )


# --- Budget-saturation edge: single host, very tight budget ------------------


def test_single_host_tight_budget() -> None:
    """With 1 host and budget=8 (minimum), completed tasks still removed."""
    state = _state_with_play(100, completed=50, host_count=1)
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=8, width=120, ascii_mode=False, colorize=False)
    joined = "\n".join(block)

    for i in range(50):
        assert f"task-{i:04d}" not in joined, (
            f"completed task-{i:04d} visible at tight budget:\n{joined}"
        )
    assert "task-0050" in joined, f"running task missing at tight budget:\n{joined}"


def test_100_percent_completed_shows_empty_tree() -> None:
    """All tasks completed, no running task → tree may show just
    the playbook header (no items) or be empty."""
    # All 100 tasks completed, no running task
    state = _state_with_play(100, completed=100, running=100)  # running at 100 = no running
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False)
    joined = "\n".join(block)

    # No task should appear
    for i in range(100):
        assert f"task-{i:04d}" not in joined, (
            f"completed task appearing in all-done tree:\n{joined}"
        )
