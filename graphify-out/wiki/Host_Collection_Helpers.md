# Host Collection Helpers

> 19 nodes · cohesion 0.20

## Key Concepts

- **_session()** (17 connections) — `tests/unit/test_session_collectors.py`
- **collect_changed_hosts()** (9 connections) — `src/ansible_aom/session/summary.py`
- **collect_unreachable_hosts()** (9 connections) — `src/ansible_aom/session/summary.py`
- **TestCollectChangedHosts** (6 connections) — `tests/unit/test_session_collectors.py`
- **TestCollectUnreachableHosts** (6 connections) — `tests/unit/test_session_collectors.py`
- **test_session_collectors.py** (5 connections) — `tests/unit/test_session_collectors.py`
- **.test_changed_host_collected()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_empty_session_returns_empty_set()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_failed_events_ignored()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_multi_host_event_picks_only_changed()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_unchanged_ok_host_ignored()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_empty_session_returns_empty_set()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_failed_events_ignored_by_unreachable_collector()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_multi_host_unreachable_event()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_single_unreachable_returns_one_host()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_session_without_events_key()** (2 connections) — `tests/unit/test_session_collectors.py`
- **Return the set of hostnames that had at least one changed task.      Pure: scans** (1 connections) — `src/ansible_aom/session/summary.py`
- **Return the set of hostnames that hit ``v2_runner_on_unreachable``.      Pure: sa** (1 connections) — `src/ansible_aom/session/summary.py`
- **Pure-helper tests for collect_failed_hosts / collect_unreachable_hosts.  Operate** (1 connections) — `tests/unit/test_session_collectors.py`

## Relationships

- [[Failed Host Collection]] (8 shared connections)
- [[Playbook Event Parsing]] (2 shared connections)
- [[Rerun Host Set Composition]] (2 shared connections)
- [[Session Summary Creation]] (2 shared connections)

## Source Files

- `src/ansible_aom/session/summary.py`
- `tests/unit/test_session_collectors.py`

## Audit Trail

- EXTRACTED: 62 (74%)
- INFERRED: 22 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*