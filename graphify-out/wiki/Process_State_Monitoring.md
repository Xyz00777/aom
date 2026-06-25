# Process State Monitoring

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestProcessStateMonitoring** (8 connections) — `tests/integration/test_error_handling.py`
- **.test_orphan_detection_during_execution()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_orphan_detection_during_loading_tasks()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_monitoring_interval_is_half_second()** (2 connections) — `tests/integration/test_error_handling.py`
- **TC-480 to TC-483: Process state monitoring.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-480: Process state checked every 0.5 seconds.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-482: Early termination during LOADING_TASKS causes CRASHED.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-483: Process termination during EXECUTION parses remaining buffer.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[Execution State Transitions]] (3 shared connections)
- [[PTY Stream Parser]] (1 shared connections)
- [[State Machine Module]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 15 (75%)
- INFERRED: 5 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*