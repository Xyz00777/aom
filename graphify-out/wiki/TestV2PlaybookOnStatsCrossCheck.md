# TestV2PlaybookOnStatsCrossCheck

> 24 nodes · cohesion 0.08

## Key Concepts

- **TestV2PlaybookOnStatsCrossCheck** (11 connections) — `tests/unit/test_host_resolution.py`
- **TestHostFallbackAfterListHostsFailure** (10 connections) — `tests/unit/test_host_resolution.py`
- **TestListHostsResolvesHostnames** (10 connections) — `tests/unit/test_host_resolution.py`
- **test_host_resolution.py** (9 connections) — `tests/unit/test_host_resolution.py`
- **.test_stats_finalizes_stale_running_hosts()** (5 connections) — `tests/unit/test_host_resolution.py`
- **.test_runner_event_host_not_in_resolved_hosts_still_added()** (4 connections) — `tests/unit/test_host_resolution.py`
- **.test_runner_events_populate_hosts_incrementally()** (3 connections) — `tests/unit/test_host_resolution.py`
- **.test_runstate_with_empty_definitions_resolves_to_empty()** (3 connections) — `tests/unit/test_host_resolution.py`
- **.test_stats_event_with_failures_marks_run_failed()** (3 connections) — `tests/unit/test_host_resolution.py`
- **.test_stats_event_with_no_failures_marks_run_completed()** (3 connections) — `tests/unit/test_host_resolution.py`
- **.test_stats_event_with_unreachable_marks_run_failed()** (3 connections) — `tests/unit/test_host_resolution.py`
- **.test_stats_event_with_unseen_hosts_does_not_error()** (3 connections) — `tests/unit/test_host_resolution.py`
- **Tests for host name resolution (TC-149 to TC-152).  Covers TEST_SPECIFICATION.md** (1 connections) — `tests/unit/test_host_resolution.py`
- **TC-151: If --list-hosts fails, resolved_hosts starts empty; populated by runner** (1 connections) — `tests/unit/test_host_resolution.py`
- **TC-151: RunState.definitions=[] → _resolve_play_hosts returns [].** (1 connections) — `tests/unit/test_host_resolution.py`
- **TC-151: v2_runner_on_* events add hosts to task.hosts even without preflight.** (1 connections) — `tests/unit/test_host_resolution.py`
- **TC-151 edge: host arriving from a runner event but absent from preflight** (1 connections) — `tests/unit/test_host_resolution.py`
- **TC-152: Final stats event cross-checks collected hosts.      Production code: ``** (1 connections) — `tests/unit/test_host_resolution.py`
- **TC-152: v2_playbook_on_stats with no failures transitions state to COMPLETED.** (1 connections) — `tests/unit/test_host_resolution.py`
- **TC-149: --list-hosts populates PlayDefinition.resolved_hosts.** (1 connections) — `tests/unit/test_host_resolution.py`
- **TC-152: v2_playbook_on_stats with failures transitions state to FAILED.** (1 connections) — `tests/unit/test_host_resolution.py`
- **TC-152: v2_playbook_on_stats with unreachable hosts transitions to FAILED.** (1 connections) — `tests/unit/test_host_resolution.py`
- **TC-152: Hosts still marked RUNNING at stats time get finalised.** (1 connections) — `tests/unit/test_host_resolution.py`
- **TC-152 edge: stats event hosts not seen during the run still process cleanly.** (1 connections) — `tests/unit/test_host_resolution.py`

## Relationships

- [RunState](RunState.md) (11 shared connections)
- [PlayDefinition](PlayDefinition.md) (6 shared connections)
- [HostRunState](HostRunState.md) (4 shared connections)
- [TaskDefinition](TaskDefinition.md) (4 shared connections)
- [assemble_definitions](assemble_definitions.md) (4 shared connections)
- [IncludeCacheEntry](IncludeCacheEntry.md) (1 shared connections)
- [StreamPhase](StreamPhase.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [WarningType](WarningType.md) (1 shared connections)

## Source Files

- `tests/unit/test_host_resolution.py`

## Audit Trail

- EXTRACTED: 67 (85%)
- INFERRED: 12 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*