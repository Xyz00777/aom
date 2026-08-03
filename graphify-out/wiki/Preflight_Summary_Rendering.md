# Preflight Summary Rendering

> 56 nodes · cohesion 0.04

## Key Concepts

- **create_renderer()** (27 connections) — `src/ansible_aom/renderer/factory.py`
- **test_json_renderer.py** (26 connections) — `tests/unit/test_json_renderer.py`
- **_state_two_hosts_one_failure()** (12 connections) — `tests/unit/test_json_renderer.py`
- **.test_factory_creates_compact_renderer_by_default()** (4 connections) — `tests/integration/test_compact_renderer.py`
- **.test_factory_creates_compact_renderer_when_tui_false()** (4 connections) — `tests/integration/test_compact_renderer.py`
- **.test_factory_forwards_failed_hint_flag_to_compact_renderer()** (4 connections) — `tests/unit/test_cli.py`
- **.test_factory_forwards_is_tty_to_compact_renderer()** (4 connections) — `tests/unit/test_cli.py`
- **.test_factory_forwards_recording_flags_to_compact_renderer()** (4 connections) — `tests/unit/test_cli.py`
- **.test_factory_forwards_warning_flags_to_compact_renderer()** (4 connections) — `tests/unit/test_cli.py`
- **test_handle_completion_aggregates_per_host_counts()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_emits_one_json_object()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_lists_failed_tasks()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_uses_state_timestamps()** (4 connections) — `tests/unit/test_json_renderer.py`
- **.test_factory_creates_tui_renderer_when_tui_true()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_factory_default_tui_mode_false()** (3 connections) — `tests/unit/test_cli.py`
- **.test_factory_function_exists()** (3 connections) — `tests/unit/test_cli.py`
- **.test_factory_returns_renderer_for_compact_mode()** (3 connections) — `tests/unit/test_cli.py`
- **.test_factory_returns_renderer_for_tui_mode()** (3 connections) — `tests/unit/test_cli.py`
- **test_factory_compact_format_explicit_returns_compact_renderer()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_factory_default_format_is_compact()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_factory_returns_json_renderer_for_json_format()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_factory_tui_mode_still_wins_over_format()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_records_playbook_and_exit_code()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_schema_version_is_one()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_interactive_prompt_refuses_to_stderr()** (3 connections) — `tests/unit/test_json_renderer.py`
- *... and 31 more nodes in this community*

## Relationships

- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (20 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (14 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (9 shared connections)
- [First Ctrl-C Cancellation](First_Ctrl-C_Cancellation.md) (2 shared connections)
- [Rerun Subcommand Module](Rerun_Subcommand_Module.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (2 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (1 shared connections)
- [State Machine Happy Path](State_Machine_Happy_Path.md) (1 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/renderer/factory.py`
- `tests/integration/test_compact_renderer.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 122 (67%)
- INFERRED: 59 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*