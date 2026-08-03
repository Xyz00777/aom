# Credential Redaction Patterns

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestLayer1AnsibleNoLog** (7 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_censors_result_field()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_loop_items_individually_censored()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_mixed_loop_items()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_no_log_replaces_entire_result()** (4 connections) — `tests/unit/test_redaction.py`
- **TC-154 edge case: Mixed loop items with per-item no_log.** (1 connections) — `tests/unit/test_redaction.py`
- **Tests for TC-153 and TC-154: _ansible_no_log flag handling.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-153: When _ansible_no_log==True, entire result censored.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-153: Result field is redacted when _ansible_no_log=True.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-154: Loop items with _ansible_no_log individually censored.** (1 connections) — `tests/unit/test_redaction.py`

## Relationships

- [TUI Tree View Tests](TUI_Tree_View_Tests.md) (4 shared connections)
- [Warnings Display Config](Warnings_Display_Config.md) (4 shared connections)
- [Timestamp Timezone Formatting](Timestamp_Timezone_Formatting.md) (2 shared connections)

## Source Files

- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 23 (82%)
- INFERRED: 5 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*