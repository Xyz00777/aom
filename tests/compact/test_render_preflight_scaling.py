"""Per-render preflight-walk cost must not scale with renders × definitions.

The compact status panel re-renders up to ~20×/s during event bursts on a
single-threaded loop, so per-render cost directly gates display latency.
Anything derived *only* from the immutable preflight definitions — pending
plays' tree lines, role totals, the ``count_total_tasks`` denominator — must
be computed once and reused, not re-walked on every render.

This suite pins that guarantee by counting how many preflight task
definitions get iterated (``iter_preflight_task_defs`` yields) across a batch
of renders on a *fixed* run state. The count is asserted, not wall-clock time
(CI timing is unreliable). The key invariant: growing the number of pending
(not-yet-running) preflight tasks must NOT increase the per-render walk.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import ansible_aom.core.tree_projection as tree_projection
from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RunState,
    Status,
    TaskDefinition,
    TaskRunState,
)

N_HOSTS = 19


def _task_def(name: str, order: int, play_id: str) -> TaskDefinition:
    return TaskDefinition(
        name=name, role=None, tags=[], play_id=play_id, play_order=0, task_order=order
    )


def _build_state(active_total: int, completed: int, pending_play_size: int) -> RunState:
    """One active play (``completed`` done + 1 running + rest pending) plus
    two fully-pending plays of ``pending_play_size`` tasks each."""
    hosts = [f"host{i:02d}" for i in range(N_HOSTS)]
    defs: list[PlayDefinition] = [
        PlayDefinition(
            id="play-0",
            name="active",
            hosts="all",
            resolved_hosts=list(hosts),
            tasks=[_task_def(f"a-{i:04d}", i, "play-0") for i in range(active_total)],
        )
    ]
    for p in (1, 2):
        defs.append(
            PlayDefinition(
                id=f"play-{p}",
                name=f"pending-{p}",
                hosts="all",
                resolved_hosts=list(hosts),
                tasks=[
                    _task_def(f"p{p}-{i:04d}", i, f"play-{p}") for i in range(pending_play_size)
                ],
            )
        )

    state = RunState(playbook="site.yml")
    state.definitions = defs

    play = PlayRunState(play_id="play-0", name="active", status=Status.RUNNING)
    for i in range(completed + 1):
        running = i == completed
        task = TaskRunState(task_id=f"t-{i:04d}", name=f"a-{i:04d}", status=Status.RUNNING)
        for h in hosts:
            task.hosts[h] = HostRunState(
                hostname=h, status=Status.RUNNING if running else Status.OK
            )
        play.tasks[task.task_id] = task
    state.plays["play-0"] = play
    return state


def _renderer_for(state: RunState) -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("site.yml", [])
    r._display = MagicMock()
    r._display.is_tty = False
    r._display.is_running = False
    r._colorize = False
    r._state = state
    r._definitions = list(state.definitions)
    return r


def _force_render(r: CompactRenderer) -> None:
    # Bypass the panel-compute throttle so every call does the full work.
    r._last_panel_compute_time = 0.0
    r._panel_dirty = True
    r._render_status_panel()


def _count_marginal_yields(r: CompactRenderer, monkeypatch, n_renders: int) -> int:
    """Warm one render, then count ``iter_preflight_task_defs`` yields over
    ``n_renders`` subsequent renders."""
    _force_render(r)  # warm caches

    real = tree_projection.iter_preflight_task_defs
    count = 0

    def counting(*args, **kwargs):
        nonlocal count
        for item in real(*args, **kwargs):
            count += 1
            yield item

    monkeypatch.setattr(tree_projection, "iter_preflight_task_defs", counting)
    for _ in range(n_renders):
        _force_render(r)
    return count


def test_pending_task_count_does_not_inflate_per_render_walk(monkeypatch) -> None:
    """Doubling+ the pending-play task count must not increase the number of
    preflight definitions walked per render. Pending plays are pure functions
    of the immutable definitions, so their projection is cached."""
    n_renders = 20

    small = _renderer_for(_build_state(active_total=200, completed=100, pending_play_size=50))
    small_yields = _count_marginal_yields(small, monkeypatch, n_renders)

    large = _renderer_for(_build_state(active_total=200, completed=100, pending_play_size=800))
    large_yields = _count_marginal_yields(large, monkeypatch, n_renders)

    # The pending plays grew 16× (50 → 800 tasks each). If they were
    # re-walked per render the large batch would iterate ~16× more preflight
    # defs. Caching makes the marginal walk independent of pending size.
    assert large_yields == small_yields, (
        f"per-render preflight walk scaled with pending size: "
        f"small={small_yields}, large={large_yields}"
    )


def test_per_render_marginal_preflight_walk_is_negligible(monkeypatch) -> None:
    """After warmup, a steady-state re-render must not re-walk the preflight
    tree. The marginal yields per render must be a small constant, not
    proportional to the ~1600 preflight tasks in the run."""
    n_renders = 20
    r = _renderer_for(_build_state(active_total=200, completed=100, pending_play_size=800))
    total = _count_marginal_yields(r, monkeypatch, n_renders)
    per_render = total / n_renders

    # A single naive render iterated >6000 preflight defs (pending plays +
    # role-total passes). Cached, the steady-state marginal is ~0; allow a
    # small constant slack that is independent of definition size.
    assert per_render < 50, f"per-render preflight walk not cached: {per_render:.0f} yields/render"
