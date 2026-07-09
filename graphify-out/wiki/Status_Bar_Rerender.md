# Status Bar Rerender

> 21 nodes · cohesion 0.14

## Key Concepts

- **reduce_state_for_parity()** (9 connections) — `src/ansible_aom/core/parity.py`
- **test_renderer_parity.py** (8 connections) — `tests/integration/test_renderer_parity.py`
- **test_all_renderers_agree_on_reduced_state()** (7 connections) — `tests/integration/test_renderer_parity.py`
- **_drive_compact()** (6 connections) — `tests/integration/test_renderer_parity.py`
- **_drive_json()** (6 connections) — `tests/integration/test_renderer_parity.py`
- **_drive_tui()** (5 connections) — `tests/integration/test_renderer_parity.py`
- **_load_events()** (4 connections) — `tests/integration/test_renderer_parity.py`
- **test_reduced_state_shape_is_stable()** (4 connections) — `tests/integration/test_renderer_parity.py`
- **parity.py** (3 connections) — `src/ansible_aom/core/parity.py`
- **_empty_host_counts()** (2 connections) — `src/ansible_aom/core/parity.py`
- **CaptureFixture** (2 connections)
- **Any** (1 connections)
- **Reduce a ``RunState`` into a renderer-agnostic dict.  This is the canonical "wha** (1 connections) — `src/ansible_aom/core/parity.py`
- **Project ``state`` into a renderer-agnostic dict.      Shape::          {** (1 connections) — `src/ansible_aom/core/parity.py`
- **Path** (1 connections)
- **Cross-renderer parity invariant.  Feed the same recorded JSONL stream through al** (1 connections) — `tests/integration/test_renderer_parity.py`
- **For each fixture, all three renderers must reduce to the same dict.** (1 connections) — `tests/integration/test_renderer_parity.py`
- **Sanity check the shape on a known-good fixture.      Locks in the keys other con** (1 connections) — `tests/integration/test_renderer_parity.py`
- **Drive a CompactRenderer through every event and reduce the final state.** (1 connections) — `tests/integration/test_renderer_parity.py`
- **Drive a JsonRenderer through every event and reduce its RunState.      The rende** (1 connections) — `tests/integration/test_renderer_parity.py`
- **Drive an AOMApp through every event and reduce its RunState.      AOMApp's rende** (1 connections) — `tests/integration/test_renderer_parity.py`

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (1 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (1 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/parity.py`
- `tests/integration/test_renderer_parity.py`

## Audit Trail

- EXTRACTED: 56 (85%)
- INFERRED: 10 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*