# JSONL Environment Variable

> 31 nodes · cohesion 0.09

## Key Concepts

- **TestHideStateCompactPlumbing** (17 connections) — `tests/unit/test_cli.py`
- **TestWarningVisibilityCompactPlumbing** (13 connections) — `tests/unit/test_cli.py`
- **Path** (10 connections)
- **._write_live_config()** (7 connections) — `tests/unit/test_cli.py`
- **MonkeyPatch** (5 connections)
- **.test_cli_no_failed_hint_overrides_enabled_config()** (5 connections) — `tests/unit/test_cli.py`
- **.test_config_disables_failed_hint()** (5 connections) — `tests/unit/test_cli.py`
- **.test_cli_hide_deprecations_overrides_enabled_config()** (4 connections) — `tests/unit/test_cli.py`
- **.test_cli_hide_warnings_overrides_enabled_config()** (4 connections) — `tests/unit/test_cli.py`
- **.test_config_disables_warning_visibility()** (4 connections) — `tests/unit/test_cli.py`
- **.test_core_module_file_exists()** (3 connections) — `tests/unit/test_cli.py`
- **.test_cli_entry_point_is_aom()** (3 connections) — `tests/unit/test_cli.py`
- **.test_package_name_is_ansible_aom()** (3 connections) — `tests/unit/test_cli.py`
- **.test_capture_verbose_propagates_to_renderer()** (2 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_default_propagates_empty_list()** (2 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_propagates_multiple_values()** (2 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_propagates_to_renderer()** (2 connections) — `tests/unit/test_cli.py`
- **.test_no_failed_hint_propagates_to_renderer()** (2 connections) — `tests/unit/test_cli.py`
- **._write_live_config()** (2 connections) — `tests/unit/test_cli.py`
- **--hide-state propagates from CLI to create_renderer/run_playbook.** (1 connections) — `tests/unit/test_cli.py`
- **aom --hide-state ok playbook.yml → create_renderer gets hide_states=["ok"].** (1 connections) — `tests/unit/test_cli.py`
- **--hide-state ok --hide-state skipped → hide_states=["ok", "skipped"].** (1 connections) — `tests/unit/test_cli.py`
- **No --hide-state flag → create_renderer gets hide_states=[].** (1 connections) — `tests/unit/test_cli.py`
- **--capture-verbose should reach compact renderer creation.** (1 connections) — `tests/unit/test_cli.py`
- **--no-failed-hint should disable failed hints in compact mode only.** (1 connections) — `tests/unit/test_cli.py`
- *... and 6 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (10 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (2 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (2 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (2 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (2 shared connections)
- [PTY Encoding Robustness](PTY_Encoding_Robustness.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 93 (87%)
- INFERRED: 14 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*