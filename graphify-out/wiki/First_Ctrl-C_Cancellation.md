# First Ctrl-C Cancellation

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestCancellationFirstCtrlC** (7 connections) — `tests/integration/test_error_handling.py`
- **.test_first_sigint_valid_transition_from_running()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_running_state_allows_cleanup_continuation()** (3 connections) — `tests/integration/test_error_handling.py`
- **TC-449: Cancellation - First Ctrl+C Forward to Subprocess.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-449: First Ctrl+C from RUNNING stays in RUNNING (cleanup mode).** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-449: RUNNING state allows continued operation during cleanup.** (1 connections) — `tests/integration/test_error_handling.py`

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