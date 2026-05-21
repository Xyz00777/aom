"""TC-PERF-020..021 — persistent TreeProjection on CompactRenderer.

``TreeProjection.from_run_state`` was called per render, which threw
away the per-instance ``_role_index`` memo on every cycle. Caching the
projection on the renderer and invalidating it only when state-shape
mutating events arrive keeps the memo alive across renders.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.tree import TreeProjection


def _task_start(uuid: str = "u1", ts: str = "2026-05-11T10:00:00Z") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": uuid, "name": "T"},
        "play": {"id": "p1"},
    }


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
