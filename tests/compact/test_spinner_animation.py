"""Running spinner (◐→◓→◑→◒) animates across renders.

Previously ``format_tree_block`` and ``format_host_rows`` passed
``counter=0`` to ``get_running_frame`` so the glyph never advanced —
users couldn't tell at a glance whether a task was making progress.
"""

from __future__ import annotations

from ansible_aom.compact.format import format_tree_block
from ansible_aom.core.icons import RUNNING_FRAMES
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


def _running_state() -> RunState:
    state = RunState(playbook="site.yml")
    state.definitions = [
        PlayDefinition(
            id="1",
            name="deploy",
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
                )
            ],
        )
    ]
    play = PlayRunState(play_id="p1", name="deploy", status=Status.RUNNING)
    task = TaskRunState(task_id="t1", name="Install nginx", status=Status.RUNNING)
    task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    play.tasks["t1"] = task
    state.plays["p1"] = play
    return state


def test_spinner_glyph_changes_with_animation_frame() -> None:
    state = _running_state()
    p = TreeProjection.from_run_state(state)
    frames_seen: set[str] = set()
    for frame in range(len(RUNNING_FRAMES)):
        block = format_tree_block(
            p,
            budget=40,
            width=120,
            ascii_mode=False,
            colorize=False,
            animation_frame=frame,
        )
        joined = "\n".join(block)
        for f in RUNNING_FRAMES:
            if f in joined:
                frames_seen.add(f)
    # All four spinner frames must be reachable by sweeping the counter.
    assert frames_seen == set(RUNNING_FRAMES), frames_seen


def test_default_frame_still_works_for_backward_compat() -> None:
    """Existing callers that don't pass animation_frame still render."""
    state = _running_state()
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=40, width=120, ascii_mode=False, colorize=False)
    joined = "\n".join(block)
    # First frame is the default.
    assert RUNNING_FRAMES[0] in joined
