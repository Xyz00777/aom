# Inspect Data Model Builders

> 62 nodes · cohesion 0.04

## Key Concepts

- **JsonRenderer** (76 connections) — `src/ansible_aom/formats/json.py`
- **test_json_renderer.py** (26 connections) — `tests/unit/test_json_renderer.py`
- **_state_two_hosts_one_failure()** (12 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_aggregates_per_host_counts()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_emits_one_json_object()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_lists_failed_tasks()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_uses_state_timestamps()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_satisfies_renderer_protocol()** (4 connections) — `tests/unit/test_json_renderer.py`
- **.handle_interactive_prompt()** (3 connections) — `src/ansible_aom/formats/json.py`
- **.handle_password_prompt()** (3 connections) — `src/ansible_aom/formats/json.py`
- **.start()** (3 connections) — `src/ansible_aom/formats/json.py`
- **.update_state()** (3 connections) — `src/ansible_aom/formats/json.py`
- **test_factory_returns_json_renderer_for_json_format()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_empty_state_emits_zero_exit()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_records_playbook_and_exit_code()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_schema_version_is_one()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_interactive_prompt_refuses_to_stderr()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_noop_methods_emit_nothing()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_set_definitions_stores_them()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_start_records_playbook_and_args()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_through_full_lifecycle()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_password_prompt_refuses_to_stderr()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_prompt_refusal_does_not_corrupt_completion_json()** (3 connections) — `tests/unit/test_json_renderer.py`
- **.add_warning()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.note_pty_bytes()** (2 connections) — `src/ansible_aom/formats/json.py`
- *... and 37 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (24 shared connections)
- [Preflight Summary Rendering](Preflight_Summary_Rendering.md) (5 shared connections)
- [Terminal Display Manager](Terminal_Display_Manager.md) (5 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (4 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (3 shared connections)
- [PTY Stream Parser](PTY_Stream_Parser.md) (3 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (2 shared connections)
- [Community 602](Community_602.md) (2 shared connections)
- [Invalid Key Handling](Invalid_Key_Handling.md) (2 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)
- [Status Bar Rerender](Status_Bar_Rerender.md) (1 shared connections)
- [Community 570](Community_570.md) (1 shared connections)

## Source Files

- `src/ansible_aom/formats/json.py`
- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 144 (63%)
- INFERRED: 83 (37%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*