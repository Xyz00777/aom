# .test_perf_022_update_state_keeps_sticky_active_play_on_gap_frame

> 6 nodes · cohesion 0.33

## Key Concepts

- **.test_perf_022_update_state_keeps_sticky_active_play_on_gap_frame()** (6 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **_renderer()** (5 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **.test_perf_021_consecutive_ticks_reuse_projection()** (4 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **_runner_ok()** (2 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **Two ticks with no intervening state mutation reuse the same instance.** (1 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **A non-structural update must keep the active play visible only         while it** (1 connections) — `tests/compact/test_tree_projection_lifecycle.py`

## Relationships

- [HostRunState](HostRunState.md) (6 shared connections)
- [TreeProjection](TreeProjection.md) (2 shared connections)
- [CompactRenderer](CompactRenderer.md) (1 shared connections)

## Source Files

- `tests/compact/test_tree_projection_lifecycle.py`

## Audit Trail

- EXTRACTED: 17 (89%)
- INFERRED: 2 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*