# Secret Redaction Configuration

> 55 nodes · cohesion 0.04

## Key Concepts

- **RedactionConfig** (123 connections) — `src/ansible_aom/core/config.py`
- **redact_event()** (70 connections) — `src/ansible_aom/core/redaction.py`
- **test_redaction.py** (26 connections) — `tests/unit/test_redaction.py`
- **TestSanitizationAppliedFields** (8 connections) — `tests/unit/test_redaction.py`
- **TestLayer1AnsibleNoLog** (7 connections) — `tests/unit/test_redaction.py`
- **TestRedactionHelperFunctions** (7 connections) — `tests/unit/test_redaction.py`
- **TestRedactionIntegration** (7 connections) — `tests/unit/test_redaction.py`
- **TestInvocationModuleArgs** (6 connections) — `tests/unit/test_redaction.py`
- **.test_inspect_shows_redacted()** (6 connections) — `tests/unit/test_redaction.py`
- **.test_all_panels_show_redacted()** (6 connections) — `tests/unit/test_redaction.py`
- **.test_deeply_nested_args()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_module_args_list_values()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_module_args_recursive_redaction()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_censors_result_field()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_loop_items_individually_censored()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_mixed_loop_items()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_replaces_entire_result()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_redact_event_function()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_password_shows_asterisks_in_log()** (5 connections) — `tests/unit/test_redaction.py`
- **TestRedactionInInspectOutput** (5 connections) — `tests/unit/test_redaction.py`
- **.test_json_output_redacted()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_artifact_file_redacted()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_empty_event_handling()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_full_event_redaction()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_layer1_takes_precedence()** (5 connections) — `tests/unit/test_redaction.py`
- *... and 30 more nodes in this community*

## Relationships

- [[Four-Layer Redaction System]] (25 shared connections)
- [[Credential String Sanitization]] (17 shared connections)
- [[Redaction Config Model]] (14 shared connections)
- [[App Config Model Tests]] (9 shared connections)
- [[App Configuration Settings]] (5 shared connections)
- [[Property Based Tests]] (5 shared connections)
- [[Pydantic Model Basics]] (2 shared connections)
- [[Ansible Password Redaction]] (2 shared connections)
- [[Generic Secret Redaction]] (2 shared connections)
- [[Password Field Regex]] (2 shared connections)
- [[Redaction Always Active]] (2 shared connections)
- [[Compact Display Module Layout]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/config.py`
- `src/ansible_aom/core/redaction.py`
- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 270 (62%)
- INFERRED: 167 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*