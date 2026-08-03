# collect_failed_hosts

> 14 nodes · cohesion 0.22

## Key Concepts

- **collect_failed_hosts()** (13 connections) — `src/ansible_aom/session/summary.py`
- **TestCollectFailedHosts** (9 connections) — `tests/unit/test_session_collectors.py`
- **.test_multi_host_failure_event()** (4 connections) — `tests/unit/test_session_collectors.py`
- **.test_unreachable_events_ignored_by_failed_collector()** (4 connections) — `tests/unit/test_session_collectors.py`
- **.test_empty_session_returns_empty_set()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_multiple_failures_across_tasks_collected()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_ok_events_ignored()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_same_host_failing_twice_collapses_to_one_entry()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_session_without_events_key()** (3 connections) — `tests/unit/test_session_collectors.py`
- **.test_single_failure_returns_one_host()** (3 connections) — `tests/unit/test_session_collectors.py`
- **Return the set of hostnames that hit ``v2_runner_on_failed`` in this session.** (1 connections) — `src/ansible_aom/session/summary.py`
- **collect_failed_hosts only looks at v2_runner_on_failed.** (1 connections) — `tests/unit/test_session_collectors.py`
- **A single failed event can carry multiple hosts.** (1 connections) — `tests/unit/test_session_collectors.py`
- **A meta-only session (no events.jsonl) returns an empty set.** (1 connections) — `tests/unit/test_session_collectors.py`

## Relationships

- [_session](_session.md) (10 shared connections)
- [load_session](load_session.md) (1 shared connections)
- [KeyAction TypedDict](KeyAction_TypedDict.md) (1 shared connections)

## Source Files

- `src/ansible_aom/session/summary.py`
- `tests/unit/test_session_collectors.py`

## Audit Trail

- EXTRACTED: 52 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*