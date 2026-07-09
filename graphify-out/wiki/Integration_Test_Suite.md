# Integration Test Suite

> 11 nodes · cohesion 0.27

## Key Concepts

- **TestProjectionLifecycle** (11 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **.test_perf_020_event_keeps_projection_alive_and_refreshes_cache()** (7 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **.test_perf_022_update_state_keeps_sticky_active_play_on_gap_frame()** (6 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **test_tree_projection_lifecycle.py** (5 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **_renderer()** (5 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **.test_perf_021_consecutive_ticks_reuse_projection()** (4 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **_runner_ok()** (2 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **_task_start()** (2 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **A state-shape change must refresh, not replace, the cached projection.** (1 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **Two ticks with no intervening state mutation reuse the same instance.** (1 connections) — `tests/compact/test_tree_projection_lifecycle.py`
- **A non-structural update must keep the active play visible only         while it** (1 connections) — `tests/compact/test_tree_projection_lifecycle.py`

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (5 shared connections)
- [Hide State Gating Tests](Hide_State_Gating_Tests.md) (3 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (2 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (2 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)

## Source Files

- `tests/compact/test_tree_projection_lifecycle.py`

## Audit Trail

- EXTRACTED: 33 (73%)
- INFERRED: 12 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*