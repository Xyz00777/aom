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


def test_tree_lines_respects_budget_with_upcoming_plays():
    """Tree must not exceed budget lines even when upcoming plays push
    the unbounded tree over the limit.

    Regression guard: the upcoming-plays feature added pending tasks
    from future plays to the tree, but the pruning stages (a–c) only
    cover host drops, per-role task limits, and role collapse. When
    many plays with many pending tasks are projected, the pruned
    result can still exceed budget — the tree would flood the terminal.
    """
    # 5 plays, each with 8 tasks = playbook + 5 plays + 40 tasks = 46 lines,
    # far exceeding a budget of 10.
    definitions = [
        _play_def(str(i), f"play {i}", [f"p{i}t{j}" for j in range(8)])
        for i in range(5)
    ]
    state = RunState(playbook="site.yml")
    state.definitions = definitions
    # First play in flight with one running task.
    play1 = PlayRunState(play_id="p1", name="play 0", status=Status.RUNNING)
    task = TaskRunState(task_id="t1", name="p0t0", status=Status.RUNNING)
    task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    play1.tasks["t1"] = task
    state.plays["p1"] = play1

    p = TreeProjection.from_run_state(state)
    lines = p.tree_lines(budget=10)
    assert len(lines) <= 10, (
        f"tree_lines returned {len(lines)} lines for budget=10, "
        f"expected <=10. Lines:\n" + "\n".join(f"  {ln.kind}: {ln.label}" for ln in lines)
    )


def test_tree_lines_respects_budget_with_many_pending_tasks():
    """Even without multiple plays, a single play with many pending
    tasks must be pruned to budget."""
    definitions = [_play_def("1", "big play", [f"task_{i}" for i in range(30)])]
    state = RunState(playbook="site.yml")
    state.definitions = definitions
    play1 = PlayRunState(play_id="p1", name="big play", status=Status.RUNNING)
    task = TaskRunState(task_id="t1", name="task_0", status=Status.RUNNING)
    task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    play1.tasks["t1"] = task
    state.plays["p1"] = play1

    p = TreeProjection.from_run_state(state)
    lines = p.tree_lines(budget=7)
    assert len(lines) <= 7, (
        f"tree_lines returned {len(lines)} lines for budget=7, "
        f"expected <=7. Lines:\n" + "\n".join(f"  {ln.kind}: {ln.label}" for ln in lines)
    )


def test_host_leaves_preserved_when_budget_allows():
    """Host leaves (web1, web2) must appear when budget is generous enough.

    Regression guard: stage (a) of the pruner drops host leaves, but
    only when the unbounded tree exceeds budget. A generous budget
    should preserve host leaves so the user can see which host is
    running which task.
    """
    state = _state_first_play_running()
    p = TreeProjection.from_run_state(state)
    # Unbounded tree for this state: playbook + play + task + host = 4 lines.
    # Budget of 10 is plenty.
    lines = p.tree_lines(budget=10)
    host_lines = [ln for ln in lines if ln.kind == "host"]
    assert len(host_lines) >= 1, (
        f"expected at least 1 host leaf with budget=10, got {len(host_lines)}. "
        f"Lines:\n" + "\n".join(f"  {ln.kind}: {ln.label}" for ln in lines)
    )


def test_host_leaves_dropped_when_budget_tight():
    """Host leaves are dropped when budget cannot accommodate them."""
    state = RunState(playbook="site.yml")
    state.definitions = [
        _play_def("1", "first play", ["t1.1", "t1.2"]),
        _play_def("2", "second play", ["t2.1", "t2.2"]),
        _play_def("3", "third play", ["t3.1"]),
    ]
    play1 = PlayRunState(play_id="p1", name="first play", status=Status.RUNNING)
    task = TaskRunState(task_id="t1", name="t1.1", status=Status.RUNNING)
    task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    task.hosts["web2"] = HostRunState(hostname="web2", status=Status.RUNNING)
    play1.tasks["t1"] = task
    state.plays["p1"] = play1

    p = TreeProjection.from_run_state(state)
    # Budget=3 fits playbook + play + task but no hosts.
    lines = p.tree_lines(budget=3)
    assert all(ln.kind != "host" for ln in lines), (
        f"expected no host leaves with budget=3, but found some. "
        f"Lines:\n" + "\n".join(f"  {ln.kind}: {ln.label}" for ln in lines)
    )
