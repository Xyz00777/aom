# Crash Recovery Stay Open

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestCrashRecoveryStayOpen** (8 connections) — `tests/integration/test_error_handling.py`
- **.test_stays_open_after_crash()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_stays_open_after_failure()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_stays_open_after_successful_completion()** (3 connections) — `tests/integration/test_error_handling.py`
- **TC-441: Crash Recovery - Stay Open After Exit.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-441: AOM stays open after playbook completes successfully.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-441: AOM stays open after task failure.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-441: AOM stays open after subprocess crash.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[Execution State Transitions]] (4 shared connections)
- [[PTY Stream Parser]] (1 shared connections)
- [[State Machine Module]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 15 (71%)
- INFERRED: 6 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*