# State Transition Validation

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestStateMachineCanTransition** (8 connections) — `tests/unit/test_state.py`
- **.test_can_transition_after_state_change()** (3 connections) — `tests/unit/test_state.py`
- **.test_can_transition_invalid()** (3 connections) — `tests/unit/test_state.py`
- **.test_can_transition_valid()** (3 connections) — `tests/unit/test_state.py`
- **Test can_transition method.** (1 connections) — `tests/unit/test_state.py`
- **can_transition returns True for valid transitions.** (1 connections) — `tests/unit/test_state.py`
- **can_transition returns False for invalid transitions.** (1 connections) — `tests/unit/test_state.py`
- **can_transition reflects current state.** (1 connections) — `tests/unit/test_state.py`

## Relationships

- [[Execution State Transitions]] (4 shared connections)
- [[State Machine Module]] (3 shared connections)

## Source Files

- `tests/unit/test_state.py`

## Audit Trail

- EXTRACTED: 15 (71%)
- INFERRED: 6 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*