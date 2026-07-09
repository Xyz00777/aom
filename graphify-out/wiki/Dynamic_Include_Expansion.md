# Dynamic Include Expansion

> 38 nodes · cohesion 0.10

## Key Concepts

- **_session()** (17 connections) — `tests/unit/test_session_collectors.py`
- **collect_failed_hosts()** (13 connections) — `src/ansible_aom/session/summary.py`
- **collect_changed_hosts()** (10 connections) — `src/ansible_aom/session/summary.py`
- **collect_unreachable_hosts()** (10 connections) — `src/ansible_aom/session/summary.py`
- **TestCollectFailedHosts** (9 connections) — `tests/unit/test_session_collectors.py`
- **TestCollectChangedHosts** (6 connections) — `tests/unit/test_session_collectors.py`
- **TestCollectUnreachableHosts** (6 connections) — `tests/unit/test_session_collectors.py`
- **summary.py** (5 connections) — `src/ansible_aom/session/summary.py`
- **test_session_collectors.py** (5 connections) — `tests/unit/test_session_collectors.py`
- **create_session_summary()** (4 connections) — `src/ansible_aom/session/summary.py`
- **Any** (4 connections)
- **.test_multi_host_failure_event()** (4 connections) — `tests/unit/test_session_collectors.py`
- **.test_unreachable_events_ignored_by_failed_collector()** (4 connections) — `tests/unit/test_session_collectors.py`
- **.test_changed_host_collected()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_empty_session_returns_empty_set()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_failed_events_ignored()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_multi_host_event_picks_only_changed()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_unchanged_ok_host_ignored()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_empty_session_returns_empty_set()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_multiple_failures_across_tasks_collected()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_ok_events_ignored()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_same_host_failing_twice_collapses_to_one_entry()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_session_without_events_key()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_single_failure_returns_one_host()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_empty_session_returns_empty_set()** (3 connections) — `tests/unit/test_session_collectors.py`
- *... and 13 more nodes in this community*

## Relationships

- [KeyAction TypedDict](KeyAction_TypedDict.md) (3 shared connections)
- [Crash Recovery Auto-Save](Crash_Recovery_Auto-Save.md) (3 shared connections)
- [Total Task Counting](Total_Task_Counting.md) (1 shared connections)

## Source Files

- `src/ansible_aom/session/summary.py`
- `tests/unit/test_session_collectors.py`

## Audit Trail

- EXTRACTED: 110 (72%)
- INFERRED: 43 (28%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*