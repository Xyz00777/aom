# Playbook Event Parsing

> 13 nodes · cohesion 0.26

## Key Concepts

- **test_render_preflight_scaling.py** (11 connections) — `tests/compact/test_render_preflight_scaling.py`
- **_build_state()** (10 connections) — `tests/compact/test_render_preflight_scaling.py`
- **_count_marginal_yields()** (6 connections) — `tests/compact/test_render_preflight_scaling.py`
- **_renderer_for()** (5 connections) — `tests/compact/test_render_preflight_scaling.py`
- **test_pending_task_count_does_not_inflate_per_render_walk()** (5 connections) — `tests/compact/test_render_preflight_scaling.py`
- **test_per_render_marginal_preflight_walk_is_negligible()** (5 connections) — `tests/compact/test_render_preflight_scaling.py`
- **_force_render()** (3 connections) — `tests/compact/test_render_preflight_scaling.py`
- **_task_def()** (3 connections) — `tests/compact/test_render_preflight_scaling.py`
- **Per-render preflight-walk cost must not scale with renders × definitions.  The c** (1 connections) — `tests/compact/test_render_preflight_scaling.py`
- **Warm one render, then count ``iter_preflight_task_defs`` yields over     ``n_ren** (1 connections) — `tests/compact/test_render_preflight_scaling.py`
- **Doubling+ the pending-play task count must not increase the number of     prefli** (1 connections) — `tests/compact/test_render_preflight_scaling.py`
- **After warmup, a steady-state re-render must not re-walk the preflight     tree.** (1 connections) — `tests/compact/test_render_preflight_scaling.py`
- **One active play (``completed`` done + 1 running + rest pending) plus     two ful** (1 connections) — `tests/compact/test_render_preflight_scaling.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (4 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (3 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (3 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (1 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [Hide State Gating Tests](Hide_State_Gating_Tests.md) (1 shared connections)

## Source Files

- `tests/compact/test_render_preflight_scaling.py`

## Audit Trail

- EXTRACTED: 53 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*