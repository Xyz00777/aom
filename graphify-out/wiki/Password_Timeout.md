# Password Timeout

> 5 nodes · cohesion 0.25

## Key Concepts

- **TestPasswordTimeout** (6 connections) — `tests/integration/test_error_handling.py`
- **.test_password_timeout_retry_option()** (3 connections) — `tests/integration/test_error_handling.py`
- **TC-484 to TC-487: Watchdog timer tests.** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_password_timeout_cancels_with_error()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_password_timeout_default_is_60_seconds()** (2 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[Watchdog Timer]] (1 shared connections)
- [[PTY Stream Parser]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)
- [[Crash Recovery Notification]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 14 (93%)
- INFERRED: 1 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*