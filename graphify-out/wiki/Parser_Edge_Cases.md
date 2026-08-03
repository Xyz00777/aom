# Parser Edge Cases

> 29 nodes · cohesion 0.13

## Key Concepts

- **should_hide_host_result()** (28 connections) — `src/ansible_aom/core/log_filter.py`
- **TestShouldHideHostResult** (26 connections) — `tests/unit/test_log_filter.py`
- **.test_missing_changed_defaults_to_false()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_changed_result_hidden_when_both_ok_and_changed_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_changed_result_hidden_when_changed_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_changed_result_visible_when_only_ok_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_changed_result_visible_with_empty_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_empty_event_type_never_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_failed_hidden_when_failed_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_failed_visible_with_empty_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_item_changed_hidden_when_changed_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_item_changed_visible_when_only_ok_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_item_failed_hidden_when_failed_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_item_ok_hidden_when_ok_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_item_skipped_hidden_when_skipped_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_missing_changed_visible_when_only_changed_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_ok_result_hidden_when_both_ok_and_changed_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_ok_result_hidden_when_ok_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_ok_result_visible_when_only_changed_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_ok_result_visible_when_only_failed_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_ok_result_visible_with_empty_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_skipped_hidden_when_skipped_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_skipped_visible_with_empty_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_unknown_event_type_never_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_unreachable_hidden_when_unreachable_in_hide_states()** (2 connections) — `tests/unit/test_log_filter.py`
- *... and 4 more nodes in this community*

## Relationships

- [log_filter.py](log_filter.py.md) (2 shared connections)
- [renderer.py](renderer.py.md) (1 shared connections)
- [._emit_event_log](_emit_event_log.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/log_filter.py`
- `tests/unit/test_log_filter.py`

## Audit Trail

- EXTRACTED: 106 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*