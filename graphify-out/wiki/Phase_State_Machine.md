# Phase State Machine

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestPhaseStateMachine** (8 connections) — `tests/unit/test_pty_stream.py`
- **.test_cannot_go_backwards_from_execution()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_phase_properties_immutability()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_phase_transition_order()** (3 connections) — `tests/unit/test_pty_stream.py`
- **Test phase state machine transitions.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Phases transition in correct order: PRE -> EXECUTION -> POST.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Cannot transition from EXECUTION back to PRE_RUN_PROMPTS.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Phase properties return correct values in each state.** (1 connections) — `tests/unit/test_pty_stream.py`

## Relationships

- [[PTY Stream Parser]] (4 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[PTY Stream Parser Tests]] (1 shared connections)

## Source Files

- `tests/unit/test_pty_stream.py`

## Audit Trail

- EXTRACTED: 15 (71%)
- INFERRED: 6 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*