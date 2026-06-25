# State Machine Module

> 54 nodes · cohesion 0.05

## Key Concepts

- **ExecutionState** (48 connections) — `src/ansible_aom/core/state_machine.py`
- **InvalidTransitionError** (19 connections) — `src/ansible_aom/core/state_machine.py`
- **test_state.py** (14 connections) — `tests/unit/test_state.py`
- **TestExecutionStateEnum** (8 connections) — `tests/unit/test_state.py`
- **TestStateMachineIsolation** (8 connections) — `tests/unit/test_state.py`
- **TestInvalidTransitionError** (7 connections) — `tests/unit/test_state.py`
- **TestStateMachineInit** (7 connections) — `tests/unit/test_state.py`
- **TestTerminalStates** (7 connections) — `tests/unit/test_state.py`
- **TestAllInvalidTransitionsExhaustive** (6 connections) — `tests/unit/test_state.py`
- **state_machine.py** (5 connections) — `src/ansible_aom/core/state_machine.py`
- **.transition()** (5 connections) — `src/ansible_aom/core/state_machine.py`
- **.can_transition()** (4 connections) — `src/ansible_aom/core/state_machine.py`
- **.__init__()** (3 connections) — `src/ansible_aom/core/state_machine.py`
- **.test_known_invalid_transitions()** (3 connections) — `tests/unit/test_state.py`
- **.test_error_message_contains_states()** (3 connections) — `tests/unit/test_state.py`
- **.test_error_message_shows_valid_transitions()** (3 connections) — `tests/unit/test_state.py`
- **.test_initial_state_is_idle()** (3 connections) — `tests/unit/test_state.py`
- **.test_state_property_is_readonly()** (3 connections) — `tests/unit/test_state.py`
- **.test_instance_one_starts_idle()** (3 connections) — `tests/unit/test_state.py`
- **.test_instance_two_starts_idle()** (3 connections) — `tests/unit/test_state.py`
- **.test_instances_dont_share_state()** (3 connections) — `tests/unit/test_state.py`
- **.test_terminal_rejects_invalid()** (3 connections) — `tests/unit/test_state.py`
- **.__init__()** (2 connections) — `src/ansible_aom/core/state_machine.py`
- **.state()** (2 connections) — `src/ansible_aom/core/state_machine.py`
- **.test_all_states_exist()** (2 connections) — `tests/unit/test_state.py`
- *... and 29 more nodes in this community*

## Relationships

- [[Execution State Transitions]] (26 shared connections)
- [[Error Handling Tests]] (9 shared connections)
- [[State Transition Validation]] (6 shared connections)
- [[Crash Recovery Auto-Save]] (4 shared connections)
- [[State Machine Invariants]] (3 shared connections)
- [[Memory Bounds Constants]] (3 shared connections)
- [[State Machine Happy Path]] (3 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Stderr Capture Handling]] (2 shared connections)
- [[First Ctrl-C Cancellation]] (1 shared connections)
- [[Cancellation Timer]] (1 shared connections)
- [[Crash Recovery Notification]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/state_machine.py`
- `tests/unit/test_state.py`

## Audit Trail

- EXTRACTED: 125 (61%)
- INFERRED: 81 (39%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*