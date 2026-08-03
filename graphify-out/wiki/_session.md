# _session

> 24 nodes · cohesion 0.16

## Key Concepts

- **_session()** (17 connections) — `tests/unit/test_session_collectors.py`
- **collect_changed_hosts()** (10 connections) — `src/ansible_aom/session/summary.py`
- **collect_unreachable_hosts()** (10 connections) — `src/ansible_aom/session/summary.py`
- **summary.py** (8 connections) — `src/ansible_aom/session/summary.py`
- **test_session_collectors.py** (6 connections) — `tests/unit/test_session_collectors.py`
- **TestCollectChangedHosts** (6 connections) — `tests/unit/test_session_collectors.py`
- **TestCollectUnreachableHosts** (6 connections) — `tests/unit/test_session_collectors.py`
- **create_session_summary()** (4 connections) — `src/ansible_aom/session/summary.py`
- **Any** (4 connections)
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
- **Pure post-mortem projections of a loaded session.  These functions take a sessio** (1 connections) — `src/ansible_aom/session/summary.py`
- **Return the set of hostnames that had at least one changed task.      Pure: scans** (1 connections) — `src/ansible_aom/session/summary.py`
- **Create a human-readable summary of a session.      Args:         session: Sessio** (1 connections) — `src/ansible_aom/session/summary.py`
- **Return the set of hostnames that hit ``v2_runner_on_unreachable``.      Pure: sa** (1 connections) — `src/ansible_aom/session/summary.py`
- **Pure-helper tests for collect_failed_hosts / collect_unreachable_hosts.  Operate** (1 connections) — `tests/unit/test_session_collectors.py`

## Relationships

- [collect_failed_hosts](collect_failed_hosts.md) (10 shared connections)
- [load_session](load_session.md) (3 shared connections)
- [Path](Path.md) (2 shared connections)
- [KeyAction TypedDict](KeyAction_TypedDict.md) (2 shared connections)

## Source Files

- `src/ansible_aom/session/summary.py`
- `tests/unit/test_session_collectors.py`

## Audit Trail

- EXTRACTED: 105 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*