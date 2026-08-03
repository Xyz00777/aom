# RedactionConfig

> 51 nodes · cohesion 0.05

## Key Concepts

- **RedactionConfig** (47 connections)
- **TestSanitizationAppliedFields** (8 connections) — `tests/unit/test_redaction.py`
- **TestLayer1AnsibleNoLog** (7 connections) — `tests/unit/test_redaction.py`
- **TestRedactionIntegration** (7 connections) — `tests/unit/test_redaction.py`
- **TestInvocationModuleArgs** (6 connections) — `tests/unit/test_redaction.py`
- **TestRedactionConfigModel** (6 connections) — `tests/unit/test_redaction.py`
- **.test_deeply_nested_args()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_module_args_list_values()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_module_args_recursive_redaction()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_censors_result_field()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_loop_items_individually_censored()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_mixed_loop_items()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_replaces_entire_result()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_empty_event_handling()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_full_event_redaction()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_layer1_takes_precedence()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_non_dict_value_handling()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_all_fields_together()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_cmd_field_sanitized()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_msg_field_sanitized()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_stderr_field_sanitized()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_stdout_field_sanitized()** (4 connections) — `tests/unit/test_redaction.py`
- **custom_config()** (3 connections) — `tests/unit/test_redaction.py`
- **.test_config_with_values()** (3 connections) — `tests/unit/test_redaction.py`
- **.test_default_config_has_empty_lists()** (3 connections) — `tests/unit/test_redaction.py`
- *... and 26 more nodes in this community*

## Relationships

- [redact_event](redact_event.md) (15 shared connections)
- [unit/test_redaction.py](unit-test_redaction.py.md) (12 shared connections)
- [redact_dict](redact_dict.md) (11 shared connections)
- [sanitize_string](sanitize_string.md) (7 shared connections)
- [AppConfig](AppConfig.md) (5 shared connections)
- [TestRedactionHelperFunctions](TestRedactionHelperFunctions.md) (4 shared connections)

## Source Files

- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 177 (97%)
- INFERRED: 5 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*