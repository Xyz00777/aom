# App Config Model Tests

> 42 nodes · cohesion 0.09

## Key Concepts

- **test_error_message_extraction.py** (23 connections) — `tests/compact/test_error_message_extraction.py`
- **_logged()** (21 connections) — `tests/compact/test_error_message_extraction.py`
- **_renderer()** (21 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_all_error_fields_empty()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_censored_fallback_when_no_other_fields()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_loop_item_no_log_shows_censored_marker()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_module_stderr_fallback()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_module_stderr_truncated()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_module_stdout_fallback()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_msg_field_shown()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_msg_multiline_uses_first_line_only()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_msg_takes_precedence_over_module_stderr()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_no_log_msg_still_wins()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_no_log_shows_censored_marker()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_no_msg_key()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_stderr_fallback()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_failed_stdout_fallback()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_unreachable_all_error_fields_empty()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_unreachable_module_stderr_fallback()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_unreachable_msg_field_shown()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_unreachable_msg_multiline_uses_first_line_only()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **test_unreachable_no_log_shows_censored_marker()** (4 connections) — `tests/compact/test_error_message_extraction.py`
- **Tests for error message extraction from multiple result fields.  When a task fai** (1 connections) — `tests/compact/test_error_message_extraction.py`
- **Fall back to ``stdout`` when all higher-priority fields are empty.** (1 connections) — `tests/compact/test_error_message_extraction.py`
- **When both ``msg`` and ``module_stderr`` are present, ``msg`` wins.** (1 connections) — `tests/compact/test_error_message_extraction.py`
- *... and 17 more nodes in this community*

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (2 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (1 shared connections)

## Source Files

- `tests/compact/test_error_message_extraction.py`

## Audit Trail

- EXTRACTED: 161 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*