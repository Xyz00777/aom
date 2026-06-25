# State Machine Invariants

> 16 nodes · cohesion 0.12

## Key Concepts

- **ExecutionStateMachine** (12 connections) — `tests/unit/test_invariants_state_machine.py`
- **.try_transition()** (3 connections) — `tests/unit/test_invariants_state_machine.py`
- **RuleBasedStateMachine** (2 connections)
- **test_invariants_state_machine.py** (2 connections) — `tests/unit/test_invariants_state_machine.py`
- **.can_transition_matches_transition()** (2 connections) — `tests/unit/test_invariants_state_machine.py`
- **.__init__()** (2 connections) — `tests/unit/test_invariants_state_machine.py`
- **.reset()** (2 connections) — `tests/unit/test_invariants_state_machine.py`
- **.state_is_in_enum()** (2 connections) — `tests/unit/test_invariants_state_machine.py`
- **.terminal_states_only_exit_via_idle()** (2 connections) — `tests/unit/test_invariants_state_machine.py`
- **Stateful invariants on the ExecutionState machine in ``core.state_machine``.  ``** (1 connections) — `tests/unit/test_invariants_state_machine.py`
- **``can_transition`` and ``transition`` agree on every state pair.          Catche** (1 connections) — `tests/unit/test_invariants_state_machine.py`
- **Random walk over ExecutionState; verifies table ↔ implementation.** (1 connections) — `tests/unit/test_invariants_state_machine.py`
- **Attempt a transition; outcome must match the VALID_TRANSITIONS table.** (1 connections) — `tests/unit/test_invariants_state_machine.py`
- **``reset()`` always returns to IDLE regardless of current state.          Documen** (1 connections) — `tests/unit/test_invariants_state_machine.py`
- **No matter what we did, the state is one of the declared values.** (1 connections) — `tests/unit/test_invariants_state_machine.py`
- **COMPLETED/FAILED/CRASHED have exactly one outbound edge: IDLE.          Asserts** (1 connections) — `tests/unit/test_invariants_state_machine.py`

## Relationships

- [[State Machine Module]] (3 shared connections)
- [[Execution State Transitions]] (2 shared connections)
- [[RunState Renderer Invariants]] (1 shared connections)

## Source Files

- `tests/unit/test_invariants_state_machine.py`

## Audit Trail

- EXTRACTED: 32 (89%)
- INFERRED: 4 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*