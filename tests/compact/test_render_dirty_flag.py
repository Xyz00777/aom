# pyright: reportMissingImports=false

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

from unittest.mock import MagicMock, patch

from ansible_aom.compact.display import Display
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

    def test_perf_042_log_storm_triggers_periodic_panel_refresh(self) -> None:
        """Sustained log output still lets the compact panel repaint.

        The log path used to reset the shared display throttle, which let
        heavy output bursts starve status/tree refreshes. The renderer now
        keeps log timing separate and repaints periodically even when no
        new JSONL event arrives.
        """
        r = _renderer()
        r._display = MagicMock(spec=Display)
        r._display.is_tty = True
        r._display.is_running = True
        r._display.print_log = MagicMock()
        r._display.update = MagicMock()
        r._last_panel_compute_time = 0.0
        r._panel_dirty = False

        with patch("ansible_aom.compact.renderer.time") as mock_time:
            mock_time.time.return_value = 100.0
            mock_time.monotonic.side_effect = [1.0, 1.0, 1.1, 1.3, 1.3]

            r.print_log("log line 1")
            r.print_log("log line 2")
            r.print_log("log line 3")

        assert r._display.print_log.call_count == 3
        assert r._display.update.call_count == 2
        assert r._render_calls == 2

    def test_perf_043_dirty_panel_renders_after_burst_settles(self) -> None:
        """HS-1/HS-8: a sustained burst of state changes must not starve the
        panel.

        Regression for the bug where the dirty-path throttle compared only
        against ``_last_panel_compute_time`` — if state changes arrived
        faster than the 0.25 s throttle, every render call skipped and
        the panel froze on stale output.

        With the fix, the dirty path compares ``last_compute`` against
        ``_last_state_change_monotonic``: when the last compute is stale
        (a state change has happened since), the gate opens immediately
        after the short coalesce window and the panel repaints.
        """
        r = _renderer()
        r._last_panel_compute_time = 0.0
        r._panel_dirty = False
        r._render_calls = 0

        # Drive one update_state so the renderer has a known compute
        # timestamp and the dirty flag is clear.
        r.update_state(_task_start("u1"))
        assert r._render_calls == 1

        # Simulate "compute happened 200 ms ago, then state changed".
        # The old gate would skip because 0.2 s < 0.25 s; the new gate
        # must render because the last compute predates the state change.
        import time as _time

        last_compute = r._last_panel_compute_time
        r._last_panel_compute_time = _time.monotonic() - 0.2
        r._last_state_change_monotonic = last_compute + 0.05  # 50 ms after compute
        r._panel_dirty = True
        baseline = r._render_calls

        r._render_status_panel()

        assert r._render_calls == baseline + 1
        assert r._panel_dirty is False

    def test_perf_044_dirty_with_fresh_compute_waits_for_tick_refresh(self) -> None:
        """HS-1/HS-8: dirty but already-rendered state waits for the 1 s
        clock-advance refresh rather than the 0.25 s compute throttle.

        The split is what lets the dirty path distinguish "stale compute"
        (render now) from "already saw this state" (wait up to 1 s).
        """
        r = _renderer()
        r._last_panel_compute_time = 0.0
        r._panel_dirty = False
        r._render_calls = 0

        r.update_state(_task_start("u1"))
        assert r._render_calls == 1

        # Set up: compute happened AFTER the most recent state change
        # (compute 50 ms ago, state change 200 ms ago). The dirty-path
        # "last compute already saw this state" branch is taken, so the
        # gate waits up to 1 s for the tick refresh rather than
        # rendering again.
        import time as _time

        now = _time.monotonic()
        r._last_state_change_monotonic = now - 0.2
        r._last_panel_compute_time = now - 0.05
        r._panel_dirty = True
        baseline = r._render_calls

        r._render_status_panel()

        # No render — gate waits up to 1 s for the tick refresh.
        assert r._render_calls == baseline
        assert r._panel_dirty is True
