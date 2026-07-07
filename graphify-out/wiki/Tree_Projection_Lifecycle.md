# Tree Projection Lifecycle

> 13 nodes · cohesion 0.23

## Key Concepts

- **TestProjectionLifecycle** (11 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **_seed_sticky_gap_state()** (9 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **.test_perf_020_event_keeps_projection_alive_and_refreshes_cache()** (6 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **test_tree_projection_lifecycle.py** (5 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **_renderer()** (5 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **.test_perf_022_update_state_keeps_sticky_active_play_on_gap_frame()** (5 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **.test_perf_021_consecutive_ticks_reuse_projection()** (3 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **_runner_ok()** (2 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **_task_start()** (2 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **A state-shape change must refresh, not replace, the cached projection.** (1 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **Two ticks with no intervening state mutation reuse the same instance.** (1 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **A non-structural update must keep the active play visible only         while it** (1 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **Build a tiny two-play state that exposes sticky row selection.      ``active`` i** (1 connections) — `tests/compact/test_tree_projection_lifecycle.py`

## Relationships

- [[Run State Completion Recap]] (6 shared connections)
- [[Compact Renderer Implementation]] (3 shared connections)
- [[Task Definition Live Refresh]] (3 shared connections)
- [[Play Definition Tree Population]] (3 shared connections)
- [[Role Group Task Models]] (1 shared connections)

## Source Files

- `tests/compact/test_tree_projection_lifecycle.py`

## Audit Trail

- EXTRACTED: 38 (73%)
- INFERRED: 14 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*