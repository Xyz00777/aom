# test_run_state_memory_bounds.py

> 20 nodes · cohesion 0.17

## Key Concepts

- **test_run_state_memory_bounds.py** (14 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **_play_start()** (7 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **_task_start()** (6 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **test_max_hosts_per_task_enforced()** (6 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **test_max_total_host_run_states_enforced()** (6 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **_ts()** (6 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **test_max_tasks_per_play_enforced()** (5 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **test_truncated_events_independent_counters()** (5 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **test_max_plays_enforced()** (4 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **test_truncated_events_starts_empty()** (3 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **_runner_on_ok()** (2 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **test_truncated_constants_pinned()** (2 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12 — enforce MAX_PLAYS / MAX_TASKS_PER_PLAY / MAX_HOSTS_PER_TASK / MAX_TOTAL_HO** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: a task's 10001st host is dropped.** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: the 1 000 001st HostRunState insertion is dropped.      The MAX_TOTAL_HOST_** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: a fresh RunState has no truncations recorded.** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: each cap has its own counter, not shared.** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: pin the documented cap values so accidental edits are caught.** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: the 1001st ``v2_playbook_on_play_start`` is dropped.** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: a play's 10001st task is dropped (other plays unaffected).** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`

## Relationships

- [RunState](RunState.md) (6 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [state_machine.py](state_machine.py.md) (1 shared connections)

## Source Files

- `tests/unit/test_run_state_memory_bounds.py`

## Audit Trail

- EXTRACTED: 74 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*