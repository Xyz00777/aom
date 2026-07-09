# Play Recap Detection

> 19 nodes · cohesion 0.14

## Key Concepts

- **test_properties_state.py** (11 connections) — `tests/unit/test_properties_state.py`
- **event_sequences()** (7 connections) — `tests/unit/test_properties_state.py`
- **_check_invariants()** (4 connections) — `tests/unit/test_properties_state.py`
- **_run_level_failure_seen()** (4 connections) — `tests/unit/test_properties_state.py`
- **test_failure_propagates_to_run_status()** (4 connections) — `tests/unit/test_properties_state.py`
- **test_runstate_invariants_hold_after_every_event()** (4 connections) — `tests/unit/test_properties_state.py`
- **test_host_terminal_states_are_disjoint()** (3 connections) — `tests/unit/test_properties_state.py`
- **_make_play_start()** (2 connections) — `tests/unit/test_properties_state.py`
- **_make_result()** (2 connections) — `tests/unit/test_properties_state.py`
- **_make_stats()** (2 connections) — `tests/unit/test_properties_state.py`
- **_make_task_start()** (2 connections) — `tests/unit/test_properties_state.py`
- **DrawFn** (1 connections)
- **Property-based tests for RunState invariants (Batch C, family #5c).  These tests** (1 connections) — `tests/unit/test_properties_state.py`
- **Generate a realistic event sequence over n_plays × n_tasks × n_hosts.** (1 connections) — `tests/unit/test_properties_state.py`
- **Assert every documented invariant on ``state``.** (1 connections) — `tests/unit/test_properties_state.py`
- **True if any task's host result is FAILED or UNREACHABLE.** (1 connections) — `tests/unit/test_properties_state.py`
- **Every event leaves RunState in an internally consistent state.** (1 connections) — `tests/unit/test_properties_state.py`
- **If any host result is FAILED or UNREACHABLE, run status is FAILED.      This mus** (1 connections) — `tests/unit/test_properties_state.py`
- **For each (play, task, host), the recorded HostRunState has exactly one status.** (1 connections) — `tests/unit/test_properties_state.py`

## Relationships

- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (5 shared connections)

## Source Files

- `tests/unit/test_properties_state.py`

## Audit Trail

- EXTRACTED: 53 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*