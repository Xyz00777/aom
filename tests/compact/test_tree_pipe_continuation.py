"""Tree-block lines under a non-last play must show the vertical
continuation pipe (``│``) so the user can see at a glance which parent
they belong to. Previously the pruner emitted plain spaces, breaking
the spine between siblings.
"""

from __future__ import annotations

from ansible_aom.compact.format import format_tree_block
from ansible_aom.core.models import RunState
from ansible_aom.core.tree import TreeProjection


def _state(*events: dict) -> RunState:
    state = RunState(playbook="site.yml")
    for ev in events:
        state.handle_event(ev)
    return state


def _two_plays_with_running_tasks() -> RunState:
    """State with two plays, each with a running task on one host."""
    return _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "first play"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "task one"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "t1", "name": "task one"},
            "host": "web1",
        },
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:04Z",
            "play": {"id": "p2", "name": "second play"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "t2", "name": "task two"},
            "play": {"id": "p2"},
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:06Z",
            "task": {"id": "t2", "name": "task two"},
            "host": "web1",
        },
    )


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
