# Dirty Flag Throttle

> 14 nodes · cohesion 0.24

## Key Concepts

- **TestDirtyFlagGating** (8 connections) — `tests/compact/test_render_dirty_flag.py`
- **_renderer()** (7 connections) — `tests/compact/test_render_dirty_flag.py`
- **_task_start()** (5 connections) — `tests/compact/test_render_dirty_flag.py`
- **.test_perf_040_two_updates_in_throttle_window_one_compute()** (4 connections) — `tests/compact/test_render_dirty_flag.py`
- **.test_perf_041_clean_tick_skips_projection_compute()** (4 connections) — `tests/compact/test_render_dirty_flag.py`
- **.test_perf_043_dirty_panel_renders_after_burst_settles()** (4 connections) — `tests/compact/test_render_dirty_flag.py`
- **.test_perf_044_dirty_with_fresh_compute_waits_for_tick_refresh()** (4 connections) — `tests/compact/test_render_dirty_flag.py`
- **test_render_dirty_flag.py** (3 connections) — `tests/compact/test_render_dirty_flag.py`
- **.test_perf_042_log_storm_triggers_periodic_panel_refresh()** (3 connections) — `tests/compact/test_render_dirty_flag.py`
- **HS-1/HS-8: a sustained burst of state changes must not starve the         panel.** (1 connections) — `tests/compact/test_render_dirty_flag.py`
- **HS-1/HS-8: dirty but already-rendered state waits for the 1 s         clock-adva** (1 connections) — `tests/compact/test_render_dirty_flag.py`
- **Two update_state calls within the throttle window → 1 panel compute.          ``** (1 connections) — `tests/compact/test_render_dirty_flag.py`
- **tick() with _panel_dirty=False and recent compute skips compute.** (1 connections) — `tests/compact/test_render_dirty_flag.py`
- **Sustained log output still lets the compact panel repaint.          The log path** (1 connections) — `tests/compact/test_render_dirty_flag.py`

## Relationships

- [[Compact Renderer Implementation]] (2 shared connections)
- [[Terminal Display Manager]] (1 shared connections)

## Source Files

- `tests/compact/test_render_dirty_flag.py`

## Audit Trail

- EXTRACTED: 45 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*