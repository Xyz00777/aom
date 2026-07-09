# Rerun Round Trip Tests

> 35 nodes · cohesion 0.06

## Key Concepts

- **redact_dict()** (17 connections) — `src/ansible_aom/core/redaction.py`
- **TestRecursiveRedaction** (7 connections) — `tests/unit/test_redaction.py`
- **RedactionConfig** (5 connections)
- **TestRedactionPerformance** (5 connections) — `tests/unit/test_redaction.py`
- **TestWhitelistFalsePositives** (5 connections) — `tests/unit/test_redaction.py`
- **_redact_list()** (4 connections) — `src/ansible_aom/core/redaction.py`
- **TestConfigCustomFields** (4 connections) — `tests/unit/test_redaction.py`
- **.test_custom_fields_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **TestConfigCustomWhitelist** (4 connections) — `tests/unit/test_redaction.py`
- **.test_custom_whitelist_not_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_empty_dict_list_handling()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_max_depth_truncation()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_nested_dict_redaction()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_nested_list_with_dicts()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_large_event_performance()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_max_depth_limits_recursion()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_default_whitelist_fields_not_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_custom_whitelist_from_config()** (3 connections) — `tests/unit/test_redaction.py`
- **Recursively redact by KEY (Layers 1+2). Returns a new dict.      The recursion i** (1 connections) — `src/ansible_aom/core/redaction.py`
- **Redact items within a list, recursing on dict items and sanitizing strings.** (1 connections) — `src/ansible_aom/core/redaction.py`
- **Tests for TC-158: Recursive dict/list redaction.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-158: Exact-match secret keys at any depth are redacted.          QC-002 note:** (1 connections) — `tests/unit/test_redaction.py`
- **TC-158: Password fields in list items are redacted.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-158 edge case: Max depth (10) truncation.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-158 edge: Empty dicts and lists handled correctly.** (1 connections) — `tests/unit/test_redaction.py`
- *... and 10 more nodes in this community*

## Relationships

- [Warnings Display Config](Warnings_Display_Config.md) (11 shared connections)
- [Inspect TUI Widget Data](Inspect_TUI_Widget_Data.md) (5 shared connections)
- [Run State Summary Panel](Run_State_Summary_Panel.md) (5 shared connections)
- [Timestamp Timezone Formatting](Timestamp_Timezone_Formatting.md) (5 shared connections)
- [TUI Tree View Tests](TUI_Tree_View_Tests.md) (3 shared connections)
- [Status Bar Elements](Status_Bar_Elements.md) (1 shared connections)
- [Community 463](Community_463.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/redaction.py`
- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 82 (77%)
- INFERRED: 25 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*