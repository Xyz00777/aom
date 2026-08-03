# Host Result Hide Filter

> 37 nodes · cohesion 0.09

## Key Concepts

- **should_hide_event()** (29 connections) — `src/ansible_aom/core/log_filter.py`
- **TestShouldHideEvent** (26 connections) — `tests/unit/test_log_filter.py`
- **.test_empty_event_type_never_hidden()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_multiple_hide_states_match_any()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_multiple_hide_states_no_match()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_item_on_ok_true_when_changed_hidden()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_on_ok_false_when_not_hidden()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_on_ok_false_when_only_failed_hidden()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_on_ok_true_when_changed_hidden()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_on_ok_true_when_ok_hidden()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_on_start_never_hidden()** (3 connections) — `tests/unit/test_log_filter.py`
- **.test_unknown_event_type_never_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_playbook_on_handler_task_start_never_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_playbook_on_play_start_never_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_playbook_on_start_never_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_playbook_on_stats_never_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_playbook_on_task_start_never_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_item_on_failed_true()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_item_on_ok_true()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_item_on_skipped_true()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_on_failed_false_when_not_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_on_failed_true()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_on_skipped_false_when_not_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_on_skipped_true()** (2 connections) — `tests/unit/test_log_filter.py`
- **.test_v2_runner_on_unreachable_false_when_not_hidden()** (2 connections) — `tests/unit/test_log_filter.py`
- *... and 12 more nodes in this community*

## Relationships

- [._emit_event_log](_emit_event_log.md) (2 shared connections)
- [log_filter.py](log_filter.py.md) (2 shared connections)
- [renderer.py](renderer.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/log_filter.py`
- `tests/unit/test_log_filter.py`

## Audit Trail

- EXTRACTED: 123 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*