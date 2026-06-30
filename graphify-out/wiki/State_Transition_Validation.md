# State Transition Validation

> 20 nodes · cohesion 0.10

## Key Concepts

- **TestValidTransitionsDictionary** (14 connections) — `tests/unit/test_state.py`
- **.test_all_states_have_transitions()** (2 connections) — `tests/unit/test_state.py`
- **.test_completed_transitions()** (2 connections) — `tests/unit/test_state.py`
- **.test_crashed_transitions()** (2 connections) — `tests/unit/test_state.py`
- **.test_failed_transitions()** (2 connections) — `tests/unit/test_state.py`
- **.test_idle_transitions()** (2 connections) — `tests/unit/test_state.py`
- **.test_loading_tasks_transitions()** (2 connections) — `tests/unit/test_state.py`
- **.test_ready_transitions()** (2 connections) — `tests/unit/test_state.py`
- **.test_running_transitions()** (2 connections) — `tests/unit/test_state.py`
- **.test_starting_transitions()** (2 connections) — `tests/unit/test_state.py`
- **CRASHED can only transition to IDLE.** (1 connections) — `tests/unit/test_state.py`
- **TC-252: Valid Transitions Dictionary Completeness.** (1 connections) — `tests/unit/test_state.py`
- **VALID_TRANSITIONS has keys for all 8 states.** (1 connections) — `tests/unit/test_state.py`
- **IDLE can only transition to STARTING.** (1 connections) — `tests/unit/test_state.py`
- **STARTING can transition to LOADING_TASKS or CRASHED.** (1 connections) — `tests/unit/test_state.py`
- **LOADING_TASKS can transition to READY or CRASHED.** (1 connections) — `tests/unit/test_state.py`
- **READY can transition to RUNNING or IDLE (timeout).** (1 connections) — `tests/unit/test_state.py`
- **RUNNING can self-loop or transition to COMPLETED, FAILED, CRASHED.** (1 connections) — `tests/unit/test_state.py`
- **COMPLETED can only transition to IDLE.** (1 connections) — `tests/unit/test_state.py`
- **FAILED can only transition to IDLE.** (1 connections) — `tests/unit/test_state.py`

## Relationships

- [[State Machine Module]] (3 shared connections)
- [[Execution State Transitions]] (1 shared connections)

## Source Files

- `tests/unit/test_state.py`

## Audit Trail

- EXTRACTED: 39 (93%)
- INFERRED: 3 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*