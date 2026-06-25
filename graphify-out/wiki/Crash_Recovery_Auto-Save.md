# Crash Recovery Auto-Save

> 15 nodes · cohesion 0.12

## Key Concepts

- **TestStateMachineReset** (8 connections) — `tests/unit/test_state.py`
- **TestCrashRecoveryAutoSavePartialSession** (7 connections) — `tests/integration/test_error_handling.py`
- **.test_loads_tasks_state_preserved_on_crash()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_running_state_preserved_on_crash()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_reset_from_crashed()** (3 connections) — `tests/unit/test_state.py`
- **.test_reset_from_failed()** (3 connections) — `tests/unit/test_state.py`
- **.test_reset_from_idle_is_idempotent()** (3 connections) — `tests/unit/test_state.py`
- **.test_reset_returns_to_idle()** (3 connections) — `tests/unit/test_state.py`
- **TC-444: Crash Recovery - Auto Save Partial Session.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-444: LOADING_TASKS crash preserves partial state.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-444: RUNNING crash preserves execution state.** (1 connections) — `tests/integration/test_error_handling.py`
- **reset returns state to IDLE regardless of current state.** (1 connections) — `tests/unit/test_state.py`
- **reset from FAILED state returns to IDLE.** (1 connections) — `tests/unit/test_state.py`
- **reset from CRASHED state returns to IDLE.** (1 connections) — `tests/unit/test_state.py`
- **reset from IDLE state stays IDLE.** (1 connections) — `tests/unit/test_state.py`

## Relationships

- [[Execution State Transitions]] (8 shared connections)
- [[State Machine Module]] (4 shared connections)
- [[PTY Stream Parser]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`
- `tests/unit/test_state.py`

## Audit Trail

- EXTRACTED: 28 (70%)
- INFERRED: 12 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*