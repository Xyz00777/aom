# Crash Recovery Panels

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestCrashRecoveryPanelsInteractive** (7 connections) — `tests/integration/test_error_handling.py`
- **.test_run_state_preserved_after_failure()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_run_state_still_accessible_after_completion()** (3 connections) — `tests/integration/test_error_handling.py`
- **TC-442: After failure, state data preserved for inspection.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-442: Crash Recovery - Panels Interactive.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-442: After completion, run state data is still available.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[Execution State Transitions]] (3 shared connections)
- [[PTY Stream Parser]] (1 shared connections)
- [[State Machine Module]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 11 (69%)
- INFERRED: 5 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*