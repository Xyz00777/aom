"""TC-PERF-020..021 — persistent TreeProjection on CompactRenderer.

``TreeProjection.from_run_state`` was called per render, which threw
away the per-instance ``_role_index`` memo on every cycle. Caching the
projection on the renderer and invalidating it only when state-shape
mutating events arrive keeps the memo alive across renders.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    Status,
    TaskDefinition,
    TaskRunState,
)
from ansible_aom.core.tree import TreeProjection


def _task_start(uuid: str = "u1", ts: str = "2026-05-11T10:00:00Z") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": uuid, "name": "T"},
        "play": {"id": "p1"},
    }


def _runner_ok(uuid: str = "u1", ts: str = "2026-05-11T10:00:01Z") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": ts,
        "task": {"id": uuid, "name": "T"},
        "play": {"id": "p1"},
        "host": "web1",
        "hosts": {"web1": {"changed": False}},
    }


def _seed_sticky_gap_state(r: CompactRenderer) -> None:
    """Build a tiny two-play state that exposes sticky row selection.

    ``active`` is currently running, while ``later`` is already completed but
    still has runtime tasks. If the projection survives the next frame, the
    tree stays anchored on ``active``. If the renderer discards the projection,
    the next frame loses ``_last_running_play_id`` and the tree can jump to
    ``later`` instead.
    """
    r._definitions = [
        PlayDefinition(
            id="1",
            name="active",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name="T",
                    role=None,
                    tags=[],
                    play_id="1",
                    play_order=0,
                    task_order=0,
                )
            ],
        ),
        PlayDefinition(
            id="2",
            name="later",
            hosts="all",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name="U",
                    role=None,
                    tags=[],
                    play_id="2",
                    play_order=1,
                    task_order=0,
                )
            ],
        ),
    ]
    assert r._state is not None
    r._state.definitions = list(r._definitions)

    active = PlayRunState(play_id="p1", name="active", status=Status.RUNNING)
    active_task = TaskRunState(task_id="u1", name="T", status=Status.RUNNING)
    active_task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    active.tasks["u1"] = active_task

    later = PlayRunState(play_id="p2", name="later", status=Status.COMPLETED)
    later.tasks["u2"] = TaskRunState(task_id="u2", name="U", status=Status.COMPLETED)

    r._state.plays = {"p1": active, "p2": later}


def _renderer() -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._colorize = False
    r._display = MagicMock()
    return r


class TestProjectionLifecycle:
    def test_perf_020_event_invalidates_projection(self) -> None:
        """A state-shape change invalidates the cached projection.

        The cache is forced to None on every ``update_state``; the next
        eligible render rebuilds it. The HS-1/HS-8 compute-throttle can
        skip that render if it lands inside the throttle window — what
        matters for HS-3 is that the stale instance is gone.
        """
        r = _renderer()
        # Force a render so the projection cache populates.
        r._render_status_panel()
        first = r._projection
        assert isinstance(first, TreeProjection)

        r.update_state(_task_start("u1"))

        # The projection cache must have been invalidated by the event
        # (cleared to None or rebuilt to a fresh instance) — never
        # silently kept as the pre-event object.
        post_event = r._projection
        assert post_event is not first

    def test_perf_021_consecutive_ticks_reuse_projection(self) -> None:
        """Two ticks with no intervening state mutation reuse the same instance."""
        r = _renderer()
        r.tick()
        first = r._projection
        assert isinstance(first, TreeProjection)

        # The HS-1/HS-8 throttle would skip a second compute within
        # 1 s, so reset the timestamp to force a real render — that's
        # what makes the cache-reuse question observable.
        r._last_panel_compute_time = 0.0
        r.tick()
        second = r._projection

        # No state mutation between the ticks → the cached projection
        # is reused (object identity), keeping ``_role_index`` warm.
        assert second is first

    def test_perf_022_update_state_keeps_sticky_active_play_on_gap_frame(self) -> None:
        """A non-structural update must not drop the sticky active-play anchor.

        The regression is that ``update_state()`` clears ``_projection`` on every
        event. That throws away ``TreeProjection._last_running_play_id`` and lets
        the next frame reselect the wrong play (``later``) even though no row
        reassignment is semantically justified.
        """
        r = _renderer()
        _seed_sticky_gap_state(r)

        # Prime the projection with an active frame so the sticky play id is
        # stored on the cached ``TreeProjection`` instance.
        r._last_panel_compute_time = 0.0
        r._render_status_panel()
        assert isinstance(r._projection, TreeProjection)

        # The active task now completes, leaving a gap frame. The renderer must
        # keep the same projection instance alive so the sticky fallback keeps
        # the tree anchored on ``active`` instead of bouncing to ``later``.
        r._last_panel_compute_time = 0.0
        r.update_state(_runner_ok())

        play_rows = [
            ln.label
            for ln in r._projection.tree_lines(20)
            if ln.kind == "play" and ln.depth == 1
        ]
        assert play_rows == ["play: active"]
