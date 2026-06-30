# Execution State Transitions

> 55 nodes · cohesion 0.06

## Key Concepts

- **StateMachine** (123 connections) — `src/ansible_aom/core/state_machine.py`
- **TestStateMachineTransitions** (19 connections) — `tests/unit/test_state.py`
- **TestStateMachineInvalidTransitions** (18 connections) — `tests/unit/test_state.py`
- **IDLE cannot transition directly to READY.** (4 connections) — `tests/unit/test_state.py`
- **.test_idle_to_completed_invalid()** (4 connections) — `tests/unit/test_state.py`
- **.test_idle_to_failed_invalid()** (4 connections) — `tests/unit/test_state.py`
- **.test_idle_to_running_invalid()** (4 connections) — `tests/unit/test_state.py`
- **.test_running_to_ready_invalid()** (4 connections) — `tests/unit/test_state.py`
- **.test_completed_to_idle()** (4 connections) — `tests/unit/test_state.py`
- **.test_crashed_to_idle()** (4 connections) — `tests/unit/test_state.py`
- **.test_starting_to_crashed()** (4 connections) — `tests/unit/test_state.py`
- **Valid transition from FAILED to IDLE on user exit.** (3 connections) — `tests/unit/test_state.py`
- **.test_completed_to_running_invalid()** (3 connections) — `tests/unit/test_state.py`
- **.test_crashed_to_running_invalid()** (3 connections) — `tests/unit/test_state.py`
- **.test_failed_to_running_invalid()** (3 connections) — `tests/unit/test_state.py`
- **.test_idle_to_crashed_invalid()** (3 connections) — `tests/unit/test_state.py`
- **.test_idle_to_ready_invalid()** (3 connections) — `tests/unit/test_state.py`
- **.test_loading_tasks_to_idle_invalid()** (3 connections) — `tests/unit/test_state.py`
- **.test_running_to_idle_invalid()** (3 connections) — `tests/unit/test_state.py`
- **.test_running_to_loading_tasks_invalid()** (3 connections) — `tests/unit/test_state.py`
- **.test_running_to_starting_invalid()** (3 connections) — `tests/unit/test_state.py`
- **.test_failed_to_idle()** (3 connections) — `tests/unit/test_state.py`
- **.test_idle_to_starting()** (3 connections) — `tests/unit/test_state.py`
- **.test_loading_tasks_to_crashed()** (3 connections) — `tests/unit/test_state.py`
- **.test_loading_tasks_to_ready()** (3 connections) — `tests/unit/test_state.py`
- *... and 30 more nodes in this community*

## Relationships

- [[State Machine Module]] (26 shared connections)
- [[Error Handling Tests]] (13 shared connections)
- [[Subprocess Exit Codes]] (9 shared connections)
- [[Crash Recovery Auto-Save]] (8 shared connections)
- [[State Machine Happy Path]] (6 shared connections)
- [[State Transition Validation]] (5 shared connections)
- [[Crash Recovery Stay Open]] (4 shared connections)
- [[First Ctrl-C Cancellation]] (3 shared connections)
- [[Crash Recovery Notification]] (3 shared connections)
- [[Crash Recovery Panels]] (3 shared connections)
- [[List-Tasks Failure Handling]] (3 shared connections)
- [[Process State Monitoring]] (3 shared connections)

## Source Files

- `src/ansible_aom/core/state_machine.py`
- `tests/unit/test_state.py`

## Audit Trail

- EXTRACTED: 132 (47%)
- INFERRED: 149 (53%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*