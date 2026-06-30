# Renderer Parity Invariant

> 18 nodes · cohesion 0.17

## Key Concepts

- **reduce_state_for_parity()** (8 connections) — `src/ansible_aom/core/parity.py`
- **test_renderer_parity.py** (7 connections) — `tests/integration/test_renderer_parity.py`
- **test_all_renderers_agree_on_reduced_state()** (7 connections) — `tests/integration/test_renderer_parity.py`
- **_drive_compact()** (6 connections) — `tests/integration/test_renderer_parity.py`
- **_drive_json()** (6 connections) — `tests/integration/test_renderer_parity.py`
- **_drive_tui()** (5 connections) — `tests/integration/test_renderer_parity.py`
- **_load_events()** (4 connections) — `tests/integration/test_renderer_parity.py`
- **test_reduced_state_shape_is_stable()** (4 connections) — `tests/integration/test_renderer_parity.py`
- **parity.py** (3 connections) — `src/ansible_aom/core/parity.py`
- **_empty_host_counts()** (2 connections) — `src/ansible_aom/core/parity.py`
- **Reduce a ``RunState`` into a renderer-agnostic dict.  This is the canonical "wha** (1 connections) — `src/ansible_aom/core/parity.py`
- **Project ``state`` into a renderer-agnostic dict.      Shape::          {** (1 connections) — `src/ansible_aom/core/parity.py`
- **Cross-renderer parity invariant.  Feed the same recorded JSONL stream through al** (1 connections) — `tests/integration/test_renderer_parity.py`
- **For each fixture, all three renderers must reduce to the same dict.** (1 connections) — `tests/integration/test_renderer_parity.py`
- **Sanity check the shape on a known-good fixture.      Locks in the keys other con** (1 connections) — `tests/integration/test_renderer_parity.py`
- **Drive a CompactRenderer through every event and reduce the final state.** (1 connections) — `tests/integration/test_renderer_parity.py`
- **Drive a JsonRenderer through every event and reduce its RunState.      The rende** (1 connections) — `tests/integration/test_renderer_parity.py`
- **Drive an AOMApp through every event and reduce its RunState.      AOMApp's rende** (1 connections) — `tests/integration/test_renderer_parity.py`

## Relationships

- [[Replay Determinism Tests]] (2 shared connections)
- [[Playbook Event Parsing]] (1 shared connections)
- [[Run State Summary Panel]] (1 shared connections)
- [[Compact Renderer Implementation]] (1 shared connections)
- [[JSON Renderer]] (1 shared connections)
- [[AOM TUI Application]] (1 shared connections)
- [[Run Config Key Normalization]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/parity.py`
- `tests/integration/test_renderer_parity.py`

## Audit Trail

- EXTRACTED: 51 (85%)
- INFERRED: 9 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*