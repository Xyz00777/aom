# State Machine Happy Path

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestStateMachineHappyPath** (10 connections) — `tests/unit/test_state.py`
- **.test_crash_at_starting_path()** (3 connections) — `tests/unit/test_state.py`
- **.test_crash_during_loading_path()** (3 connections) — `tests/unit/test_state.py`
- **.test_crash_during_running_path()** (3 connections) — `tests/unit/test_state.py`
- **.test_failure_path()** (3 connections) — `tests/unit/test_state.py`
- **.test_full_success_path()** (3 connections) — `tests/unit/test_state.py`
- **Test complete happy path transitions.** (1 connections) — `tests/unit/test_state.py`
- **Complete successful execution path: IDLE -> STARTING -> ... -> COMPLETED -> IDLE** (1 connections) — `tests/unit/test_state.py`
- **Complete failure path: IDLE -> ... -> RUNNING -> FAILED -> IDLE.** (1 connections) — `tests/unit/test_state.py`
- **Crash during loading: IDLE -> STARTING -> CRASHED -> IDLE.** (1 connections) — `tests/unit/test_state.py`
- **Crash during loading: IDLE -> STARTING -> LOADING_TASKS -> CRASHED -> IDLE.** (1 connections) — `tests/unit/test_state.py`
- **Crash during execution: IDLE -> ... -> RUNNING -> CRASHED -> IDLE.** (1 connections) — `tests/unit/test_state.py`

## Relationships

- [[Execution State Transitions]] (6 shared connections)
- [[State Machine Module]] (3 shared connections)

## Source Files

- `tests/unit/test_state.py`

## Audit Trail

- EXTRACTED: 23 (74%)
- INFERRED: 8 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*