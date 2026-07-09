# TUI Tree View Tests

> 86 nodes · cohesion 0.04

## Key Concepts

- **redact_event()** (69 connections) — `src/ansible_aom/core/redaction.py`
- **RedactionConfig** (28 connections)
- **_ansible_event_with_res()** (26 connections) — `tests/integration/test_redaction.py`
- **test_redaction.py** (14 connections) — `tests/integration/test_redaction.py`
- **TestLayer3StringSanitizationOnEvents** (9 connections) — `tests/integration/test_redaction.py`
- **TestLayer2PasswordFieldsOnEvents** (8 connections) — `tests/integration/test_redaction.py`
- **TestCustomConfigOnRealisticEvents** (6 connections) — `tests/integration/test_redaction.py`
- **TestLayer1NoLogOnFullEvent** (6 connections) — `tests/integration/test_redaction.py`
- **TestLayer4InvocationModuleArgs** (6 connections) — `tests/integration/test_redaction.py`
- **.test_custom_fields_redacted_on_event()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_custom_patterns_sanitize_strings_on_event()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_custom_whitelist_extends_default()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_entire_res_replaced_with_censored_marker()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_envelope_preserved_after_no_log_censorship()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_no_log_false_passes_through_to_other_layers()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_per_item_no_log_censors_only_marked_items()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_generic_secret_fields_redacted()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_known_ansible_password_fields_redacted()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_nested_passwords_in_realistic_dict_redacted()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_password_match_regex_field_redacted()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_whitelisted_pass_fields_not_redacted()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_all_sanitized_fields_together()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_cmd_field_url_credentials_stripped()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_cmd_list_each_entry_sanitized()** (5 connections) — `tests/integration/test_redaction.py`
- **.test_msg_field_cli_credentials_stripped()** (5 connections) — `tests/integration/test_redaction.py`
- *... and 61 more nodes in this community*

## Relationships

- [Warnings Display Config](Warnings_Display_Config.md) (15 shared connections)
- [Inspect TUI Widget Data](Inspect_TUI_Widget_Data.md) (12 shared connections)
- [Run State Summary Panel](Run_State_Summary_Panel.md) (10 shared connections)
- [Summary Panel Widget](Summary_Panel_Widget.md) (5 shared connections)
- [Timestamp Timezone Formatting](Timestamp_Timezone_Formatting.md) (5 shared connections)
- [Rerun Round Trip Tests](Rerun_Round_Trip_Tests.md) (3 shared connections)
- [View Mode Selection](View_Mode_Selection.md) (2 shared connections)
- [Status Bar Elements](Status_Bar_Elements.md) (1 shared connections)
- [Community 463](Community_463.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/redaction.py`
- `tests/integration/test_redaction.py`
- `tests/unit/test_redaction_layer4.py`

## Audit Trail

- EXTRACTED: 273 (73%)
- INFERRED: 101 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*