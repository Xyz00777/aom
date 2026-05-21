"""TC-PERF-040..041 — dirty-flag gating for ``_render_status_panel``.

The status panel is computed on every event, but ``Display.update``
throttles the corresponding terminal write to ~4 Hz. Computing every
event wastes CPU on output that's immediately discarded. The renderer
now keeps a ``_panel_dirty`` flag and a "last compute" timestamp so:

- Multiple event arrivals within Display's throttle window coalesce to
  one panel computation.
- ``tick()`` with a clean state and recent compute is a fast no-op.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer


def _task_start(uuid: str = "u1") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": "2026-05-11T10:00:00Z",
        "task": {"id": uuid, "name": "T"},
        "play": {"id": "p1"},
    }


def _renderer() -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._colorize = False
    r._display = MagicMock()
    return r


class TestDirtyFlagGating:
    def test_perf_040_two_updates_in_throttle_window_one_compute(self) -> None:
        """Two update_state calls within the throttle window → 1 panel compute.

        ``_render_calls`` only increments past the throttle gate, so it
        cleanly counts the number of compute invocations that actually
        run.
        """
        r = _renderer()
        r._last_panel_compute_time = 0.0
        r._panel_dirty = False
        r._render_calls = 0

        # The first update primes the last-compute timestamp; the
        # second arrives well inside the 0.25 s throttle and must be
        # coalesced (skipped).
        r.update_state(_task_start("u1"))
        r.update_state(_task_start("u2"))

        assert r._render_calls == 1

    def test_perf_041_clean_tick_skips_projection_compute(self) -> None:
        """tick() with _panel_dirty=False and recent compute skips compute."""
        r = _renderer()
        # Drive one event so the panel is rendered and the compute
        # timestamp is set; ``_panel_dirty`` flips back to False.
        r.update_state(_task_start("u1"))
        assert r._panel_dirty is False
        baseline = r._render_calls

        # tick() right after a clean render must not touch the
        # projection. The clock-advance refresh only kicks in after
        # the long quiet-window threshold (1 s).
        r.tick()

        assert r._render_calls == baseline
