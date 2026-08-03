# Limit Args Merging

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestPlaybookOnStats** (13 connections) — `tests/unit/test_event_processing.py`
- **.test_stats_empty_plays()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_stats_no_failures_status_completed()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_stats_sets_end_time()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_stats_with_failures_status_failed()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_stats_with_unreachable_status_failed()** (3 connections) — `tests/unit/test_event_processing.py`
- **Tests for v2_playbook_on_stats handling (TC-214).** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-214: v2_playbook_on_stats sets RunState.end_time.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-214: Stats with no failures sets status to COMPLETED.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-214: Stats with failures sets status to FAILED.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-214: Stats with unreachable sets status to FAILED.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-214 edge case: Stats with empty plays dict still works.** (1 connections) — `tests/unit/test_event_processing.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (7 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (3 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)

## Source Files

- `tests/unit/test_event_processing.py`

## Audit Trail

- EXTRACTED: 28 (82%)
- INFERRED: 6 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*