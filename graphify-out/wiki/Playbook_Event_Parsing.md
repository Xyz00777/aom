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

- [HostRunState](HostRunState.md) (4 shared connections)
- [CompactRenderer](CompactRenderer.md) (3 shared connections)
- [RunState](RunState.md) (2 shared connections)
- [renderer.py](renderer.py.md) (1 shared connections)
- [tree.py](tree.py.md) (1 shared connections)
- [PlayDefinition](PlayDefinition.md) (1 shared connections)
- [TaskDefinition](TaskDefinition.md) (1 shared connections)

## Source Files

- `tests/compact/test_render_preflight_scaling.py`

## Audit Trail

- EXTRACTED: 53 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*