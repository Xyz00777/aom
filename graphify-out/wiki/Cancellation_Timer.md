# Cancellation Timer

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestCancellationTimerLogic** (9 connections) — `tests/integration/test_error_handling.py`
- **.test_cancellation_timer_check_within_window()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_cancellation_timer_initial_state()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_cancellation_timer_resets_after_timeout()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_cancellation_timer_sets_on_first_interrupt()** (2 connections) — `tests/integration/test_error_handling.py`
- **Tests for the double-Ctrl+C cancellation timer.** (1 connections) — `tests/integration/test_error_handling.py`
- **Timer starts unset on initialization.** (1 connections) — `tests/integration/test_error_handling.py`
- **First Ctrl+C sets the timer.** (1 connections) — `tests/integration/test_error_handling.py`
- **Second Ctrl+C within 2s triggers immediate exit.** (1 connections) — `tests/integration/test_error_handling.py`
- **Timer resets after 2 seconds.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[PTY Stream Parser]] (1 shared connections)
- [[State Machine Module]] (1 shared connections)
- [[Execution State Transitions]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 19 (86%)
- INFERRED: 3 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*