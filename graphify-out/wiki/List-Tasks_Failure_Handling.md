# List-Tasks Failure Handling

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestGracefulDegradationListTasksFailure** (7 connections) — `tests/integration/test_error_handling.py`
- **.test_can_retry_after_list_tasks_failure()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_list_tasks_failure_state_transition()** (3 connections) — `tests/integration/test_error_handling.py`
- **TC-447: Graceful Degradation - list-tasks Failure.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-447: --list-tasks failure transitions to CRASHED.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-447: User can retry after --list-tasks failure.** (1 connections) — `tests/integration/test_error_handling.py`

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