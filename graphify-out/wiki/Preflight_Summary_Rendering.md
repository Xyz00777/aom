# Preflight Summary Rendering

> 34 nodes · cohesion 0.06

## Key Concepts

- **create_renderer()** (27 connections) — `src/ansible_aom/renderer/factory.py`
- **_resolve_mode()** (5 connections) — `src/ansible_aom/renderer/factory.py`
- **.test_factory_creates_compact_renderer_by_default()** (4 connections) — `tests/integration/test_compact_renderer.py`
- **.test_factory_creates_compact_renderer_when_tui_false()** (4 connections) — `tests/integration/test_compact_renderer.py`
- **.test_factory_forwards_failed_hint_flag_to_compact_renderer()** (4 connections) — `tests/unit/test_cli.py`
- **.test_factory_forwards_is_tty_to_compact_renderer()** (4 connections) — `tests/unit/test_cli.py`
- **.test_factory_forwards_recording_flags_to_compact_renderer()** (4 connections) — `tests/unit/test_cli.py`
- **.test_factory_forwards_warning_flags_to_compact_renderer()** (4 connections) — `tests/unit/test_cli.py`
- **test_factory_tui_mode_still_wins_over_format()** (4 connections) — `tests/unit/test_json_renderer.py`
- **factory.py** (3 connections) — `src/ansible_aom/renderer/factory.py`
- **.test_factory_creates_tui_renderer_when_tui_true()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_factory_default_tui_mode_false()** (3 connections) — `tests/unit/test_cli.py`
- **.test_factory_function_exists()** (3 connections) — `tests/unit/test_cli.py`
- **.test_factory_returns_renderer_for_compact_mode()** (3 connections) — `tests/unit/test_cli.py`
- **.test_factory_returns_renderer_for_tui_mode()** (3 connections) — `tests/unit/test_cli.py`
- **test_factory_compact_format_explicit_returns_compact_renderer()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_factory_default_format_is_compact()** (3 connections) — `tests/unit/test_json_renderer.py`
- **RenderFormat** (2 connections)
- **RenderMode** (2 connections)
- **Renderer factory.  One entry point — :func:`create_renderer` — that picks the co** (1 connections) — `src/ansible_aom/renderer/factory.py`
- **Pick a single ``RenderMode`` from the user-facing parameter set.      Priority:** (1 connections) — `src/ansible_aom/renderer/factory.py`
- **Create the renderer selected by ``mode``.      Args:         mode: ``"compact"``** (1 connections) — `src/ansible_aom/renderer/factory.py`
- **Default view mode is compact.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **tui_mode=False creates CompactRenderer.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **tui_mode=True creates Textual AOMApp.** (1 connections) — `tests/integration/test_compact_renderer.py`
- *... and 9 more nodes in this community*

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (9 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (8 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (5 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (3 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (2 shared connections)
- [State Transition Validation](State_Transition_Validation.md) (1 shared connections)
- [State Machine Happy Path](State_Machine_Happy_Path.md) (1 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)
- [Shell Completion Helpers](Shell_Completion_Helpers.md) (1 shared connections)

## Source Files

- `src/ansible_aom/renderer/factory.py`
- `tests/integration/test_compact_renderer.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 59 (57%)
- INFERRED: 44 (43%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*