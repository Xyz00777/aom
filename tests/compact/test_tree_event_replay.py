"""Tree correctness under incremental event replay.

Unlike synthetic-state tests that construct RunState directly,
these tests replay the exact sequence of JSONL events that a
real ansible-playbook run produces, and check the tree after
each step. This catches any divergence between the event-driven
state machine and the synthetic state used in other tests.
"""

from __future__ import annotations

from ansible_aom.compact.format import (
    format_tree_block,
)
from ansible_aom.core.models import PlayDefinition, TaskDefinition
from ansible_aom.core.run_state import RunState
from ansible_aom.core.tree import TreeProjection


def _play_event(name: str, play_id: str = "play-uuid-1") -> dict:
    return {
        "_event": "v2_playbook_on_play_start",
        "_timestamp": "2026-06-26T10:00:01Z",
        "play": {"id": play_id, "name": name},
    }


def _task_start_event(
    name: str, task_id: str, play_id: str = "play-uuid-1", path: str | None = None
) -> dict:
    ev = {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": "2026-06-26T10:00:02Z",
        "task": {"id": task_id, "name": name},
        "play": {"id": play_id},
    }
    if path:
        ev["path"] = path
    return ev


def _runner_ok_event(
    task_id: str,
    host: str,
    changed: bool = False,
    play_id: str = "play-uuid-1",
) -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-06-26T10:00:05Z",
        "task": {"id": task_id, "name": f"task-{task_id}"},
        "play": {"id": play_id},
        "hosts": {host: {"ok": True, "changed": changed}},
    }


def _list_tasks_event(play_id: str, task_names: list[str]) -> dict:
    """Simulate start-of-run event with preflight task list."""
    return {
        "_event": "v2_playbook_on_start",
        "_timestamp": "2026-06-26T10:00:00Z",
        "playbook": "site.yml",
    }


def _stats_event() -> dict:
    return {
        "_event": "v2_playbook_on_stats",
        "_timestamp": "2026-06-26T10:01:00Z",
        "stats": {},
    }


def _setup_state(
    host_count: int = 5,
    task_count: int = 100,
) -> tuple[RunState, TreeProjection]:
    """Create RunState with preflight definitions matching events we'll replay."""
    state = RunState(playbook="site.yml")
    state.definitions = [
        PlayDefinition(
            id="play-uuid-1",
            name="deploy",
            hosts="all",
            resolved_hosts=[f"host{h}" for h in range(host_count)],
            tasks=[
                TaskDefinition(
                    name=f"task-{i:04d}",
                    role=None,
                    tags=[],
                    play_id="play-uuid-1",
                    play_order=0,
                    task_order=i,
                )
                for i in range(task_count)
            ],
        )
    ]
    projection = TreeProjection.from_run_state(state)
    return state, projection


def tree_has_task(block: list[str], task_name: str) -> bool:
    """Check if a task name appears in the rendered tree block."""
    joined = "\n".join(block)
    return task_name in joined


# --- Event replay: 100 tasks, check tree after each completion ---------------


def test_tree_after_each_task_completion() -> None:
    """Replay a 100-task linear playbook event stream, checking the tree for
    completed tasks after every task_end event. Verifies the invariant:
    at no point does a completed task appear in the tree."""
    state, projection = _setup_state(host_count=3, task_count=100)

    state.handle_event(_play_event("deploy"))

    for i in range(100):
        # Task i starts
        task_id = f"task-uuid-{i:04d}"
        task_name = f"task-{i:04d}"
        state.handle_event(_task_start_event(task_name, task_id, path=f"site.yml:{i + 1}"))

        # Check tree after task_start alone (should be visible now)
        block = format_tree_block(
            projection,
            budget=40,
            width=120,
            ascii_mode=False,
            colorize=False,
        )
        running = f"task-{i:04d}"
        joined = "\n".join(block)
        assert running in joined, (
            f"[task {i}] task {running} not visible after task_start:\n{joined}"
        )

        # For each of 3 hosts, runner_on_ok
        for h in range(3):
            state.handle_event(_runner_ok_event(task_id, f"host{h}", play_id="play-uuid-1"))

        # Check tree after all hosts complete
        block = format_tree_block(
            projection,
            budget=40,
            width=120,
            ascii_mode=False,
            colorize=False,
        )
        joined = "\n".join(block)

        # Completed tasks (including current) should NEVER appear
        for completed_i in range(i + 1):
            completed_name = f"task-{completed_i:04d}"
            if completed_name in joined:
                raise AssertionError(
                    f"[task {i}] completed {completed_name} visible in tree:\n{joined}"
                )

        # The next task hasn't started yet, so task i should not appear.
        # The tree should show either nothing (after play ends) or pending
        # tasks / upcoming plays.
        # This demonstrates that completed tasks DO vanish from the tree
        # during event replay.

    # Done: all 100 tasks completed
    state.handle_event(_stats_event())
    tree = projection.tree_lines(budget=40)
    assert len(tree) == 0, "tree not empty after stats"


def test_tree_after_completion_no_race_window() -> None:
    """Specifically test the window between last runner_on_ok and next
    task_start: a task whose all hosts are terminal but whose status is
    still RUNNING must NOT appear in the tree."""
    state, projection = _setup_state(host_count=2, task_count=5)

    state.handle_event(_play_event("deploy"))
    state.handle_event(_task_start_event("task-0000", "uuid-0"))

    # All hosts finish
    state.handle_event(_runner_ok_event("uuid-0", "host0"))
    state.handle_event(_runner_ok_event("uuid-0", "host1"))

    # At this point, task-0000 has all hosts OK but status=RUNNING.
    # _classify must still return "completed" via host check.
    tree = projection.tree_lines(budget=40)
    block = format_tree_block(
        projection,
        budget=40,
        width=120,
        ascii_mode=False,
        colorize=False,
    )
    joined = "\n".join(block)
    assert "task-0000" not in joined, f"task-0000 visible before next task_start:\n{joined}"


def test_tree_shrinks_under_budget_during_replay() -> None:
    """As tasks complete during event replay, the rendered tree should
    shrink once the unbounded tree fits under budget."""
    state, projection = _setup_state(host_count=3, task_count=100)

    state.handle_event(_play_event("deploy"))

    tree_sizes: list[int] = []
    for i in range(100):
        task_id = f"uuid-{i:04d}"
        task_name = f"task-{i:04d}"
        state.handle_event(_task_start_event(task_name, task_id, path=f"site.yml:{i + 1}"))
        for h in range(3):
            state.handle_event(_runner_ok_event(task_id, f"host{h}"))

        block = format_tree_block(
            projection,
            budget=40,
            width=120,
            ascii_mode=False,
            colorize=False,
        )
        tree_sizes.append(len(block))

    # At some point the tree should shrink (unbounded tree fits under 40)
    # Not all sizes should be identical
    assert len(set(tree_sizes)) > 1, f"tree never changed size during 100-task replay: {tree_sizes}"
    # The last tree should be smaller than the first
    assert tree_sizes[-1] < tree_sizes[0], (
        f"tree did not shrink: {tree_sizes[0]} -> {tree_sizes[-1]}"
    )
