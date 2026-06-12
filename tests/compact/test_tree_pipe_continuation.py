"""Tree-block lines under a non-last play must show the vertical
continuation pipe (``│``) so the user can see at a glance which parent
they belong to. Previously the pruner emitted plain spaces, breaking
the spine between siblings.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.compact.format import format_tree_block
from ansible_aom.core.models import (
    HostRunState,
    PlayRunState,
    RunState,
    Status,
    TaskRunState,
)
from ansible_aom.core.tree import TreeProjection


def _two_plays_with_running_tasks() -> RunState:
    """State with two plays, each with a running task on one host.

    Built directly rather than via sequential ``v2_playbook_on_play_start``
    events: a second play starting now finalises the first (ansible runs
    plays sequentially, so a prior play is definitively done), which is
    correct for real runs but collapses the first play out of the tree.
    These tests exercise the renderer's multi-play pipe-continuation glyph,
    so they need the (otherwise transient) two-rendered-plays state held
    stable — constructing it directly does exactly that.
    """
    state = RunState(playbook="site.yml")
    t0 = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
    for pid, pname, tid, tname in (
        ("p1", "first play", "t1", "task one"),
        ("p2", "second play", "t2", "task two"),
    ):
        play = PlayRunState(play_id=pid, name=pname, status=Status.RUNNING)
        task = TaskRunState(task_id=tid, name=tname, status=Status.RUNNING, start_time=t0)
        task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING, start_time=t0)
        play.tasks[tid] = task
        state.plays[pid] = play
    return state


def test_non_last_play_children_show_vertical_pipe() -> None:
    """A task under a non-last play must be indented with ``│  ``."""
    state = _two_plays_with_running_tasks()
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False)

    # The task under "first play" (not the last) must show the spine.
    first_task_line = next(ln for ln in block if "task one" in ln)
    assert first_task_line.startswith("│  "), (
        f"expected vertical pipe before task-one under non-last play; got {first_task_line!r}"
    )


def test_last_play_children_have_plain_indent() -> None:
    """A task under the last play must NOT carry a vertical pipe — the
    parent is the last child so no continuation is needed."""
    state = _two_plays_with_running_tasks()
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False)

    last_task_line = next(ln for ln in block if "task two" in ln)
    assert not last_task_line.startswith("│"), (
        f"expected plain indent before task-two under last play; got {last_task_line!r}"
    )
    assert last_task_line.startswith("   "), (
        f"expected 3-space indent before branch glyph; got {last_task_line!r}"
    )


def test_ascii_mode_uses_pipe_substitute() -> None:
    """ASCII mode renders the continuation as ``|  `` (or equivalent)
    rather than the Unicode box-drawing pipe — no Unicode in ASCII mode.
    """
    state = _two_plays_with_running_tasks()
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=True, colorize=False)
    joined = "\n".join(block)
    assert "│" not in joined, "ASCII mode should not contain Unicode pipe"

    first_task_line = next(ln for ln in block if "task one" in ln)
    assert first_task_line.startswith("|  "), (
        f"expected ASCII pipe before task-one under non-last play; got {first_task_line!r}"
    )
