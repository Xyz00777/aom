# Crash Recovery Auto-Save

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestRedactionIntegration** (7 connections) — `tests/unit/test_redaction.py`
- **.test_empty_event_handling()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_full_event_redaction()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_layer1_takes_precedence()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_non_dict_value_handling()** (4 connections) — `tests/unit/test_redaction.py`
- **Integration tests combining multiple redaction layers.** (1 connections) — `tests/unit/test_redaction.py`
- **All four layers work together on a complete event.** (1 connections) — `tests/unit/test_redaction.py`
- **Layer 1 (_ansible_no_log) takes precedence over other layers.** (1 connections) — `tests/unit/test_redaction.py`
- **Edge case: Empty event dict handled gracefully.** (1 connections) — `tests/unit/test_redaction.py`
- **Edge case: Non-dict values handled correctly.** (1 connections) — `tests/unit/test_redaction.py`

## Relationships

- [Warnings Display Config](Warnings_Display_Config.md) (4 shared connections)
- [TUI Tree View Tests](TUI_Tree_View_Tests.md) (3 shared connections)
- [Timestamp Timezone Formatting](Timestamp_Timezone_Formatting.md) (2 shared connections)
- [Rerun Round Trip Tests](Rerun_Round_Trip_Tests.md) (1 shared connections)

## Source Files

- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 23 (82%)
- INFERRED: 5 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*