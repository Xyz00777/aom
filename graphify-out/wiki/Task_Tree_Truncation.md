# Task Tree Truncation

> 16 nodes · cohesion 0.24

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
- **_runner_on_ok()** (2 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12 — enforce MAX_PLAYS / MAX_TASKS_PER_PLAY / MAX_HOSTS_PER_TASK / MAX_TOTAL_HO** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: a task's 10001st host is dropped.** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: the 1 000 001st HostRunState insertion is dropped.      The MAX_TOTAL_HOST_** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: each cap has its own counter, not shared.** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: the 1001st ``v2_playbook_on_play_start`` is dropped.** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`
- **R12: a play's 10001st task is dropped (other plays unaffected).** (1 connections) — `tests/unit/test_run_state_memory_bounds.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (5 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)
- [TUI Screens Module](TUI_Screens_Module.md) (1 shared connections)
- [Small Terminal Handling](Small_Terminal_Handling.md) (1 shared connections)
- [ANSI Rewind Correctness](ANSI_Rewind_Correctness.md) (1 shared connections)

## Source Files

- `tests/unit/test_run_state_memory_bounds.py`

## Audit Trail

- EXTRACTED: 62 (93%)
- INFERRED: 5 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*