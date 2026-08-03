# Summary Panel Widget

> 24 nodes · cohesion 0.09

## Key Concepts

- **test_properties_redaction.py** (15 connections) — `tests/unit/test_properties_redaction.py`
- **SearchStrategy** (4 connections)
- **_distinctive_secret()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **_innocuous_key()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **_password_shaped_key()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_cli_credentials_are_stripped()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_no_log_at_top_level_censors_everything()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_no_log_in_loop_items_censors_that_item()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_password_redaction_works_through_nested_dicts()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_password_shaped_keys_are_redacted()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_url_credentials_are_stripped()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_whitelisted_keys_pass_through()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **_whitelisted_key()** (2 connections) — `tests/unit/test_properties_redaction.py`
- **Property-based tests for the redaction layers (Batch C, family #5b).  These prop** (1 connections) — `tests/unit/test_properties_redaction.py`
- **The verbatim secret never appears in the redacted serialisation.** (1 connections) — `tests/unit/test_properties_redaction.py`
- **Nested dicts under MAX_DEPTH still redact password-shaped keys.** (1 connections) — `tests/unit/test_properties_redaction.py`
- **Keys in PASSWORD_WHITELIST keep their value unchanged.** (1 connections) — `tests/unit/test_properties_redaction.py`
- **URL of form scheme://user:SECRET@host/ has SECRET removed by sanitize_string.** (1 connections) — `tests/unit/test_properties_redaction.py`
- **CLI flag of form --password=SECRET has SECRET removed by sanitize_string.** (1 connections) — `tests/unit/test_properties_redaction.py`
- **_ansible_no_log=True at result top-level: entire res becomes censored marker.** (1 connections) — `tests/unit/test_properties_redaction.py`
- **A list ``results`` entry with _ansible_no_log=True collapses to the marker.** (1 connections) — `tests/unit/test_properties_redaction.py`
- **Generate keys that satisfy the PASSWORD_MATCH regex and are not whitelisted.** (1 connections) — `tests/unit/test_properties_redaction.py`
- **Distinctive non-empty secret values unlikely to collide with other fields.** (1 connections) — `tests/unit/test_properties_redaction.py`
- **Keys that should never be redacted.** (1 connections) — `tests/unit/test_properties_redaction.py`

## Relationships

- [TUI Tree View Tests](TUI_Tree_View_Tests.md) (5 shared connections)
- [Inspect TUI Widget Data](Inspect_TUI_Widget_Data.md) (3 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/unit/test_properties_redaction.py`

## Audit Trail

- EXTRACTED: 55 (89%)
- INFERRED: 7 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*