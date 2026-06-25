# Crash Recovery Notification

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestCrashRecoveryNotification** (7 connections) — `tests/integration/test_error_handling.py`
- **.test_crashed_state_is_terminal()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_graceful_degradation_state_machine_integrity()** (3 connections) — `tests/integration/test_error_handling.py`
- **TC-443: Crash Recovery - Graceful Degradation Notification.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-443: CRASHED state stays open for notification.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-443: State machine remains intact during crash recovery.** (1 connections) — `tests/integration/test_error_handling.py`

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