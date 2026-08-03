# Plaintext Line Handling

> 19 nodes · cohesion 0.15

## Key Concepts

- **test_invariants_session_roundtrip.py** (16 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **test_tree_builder_matches_live_runstate_totals()** (9 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **test_session_roundtrip_preserves_state_shape()** (7 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **event_sequences()** (6 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_runstate_status_totals()** (5 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_shape()** (5 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_tree_status_totals()** (4 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_make_play_start()** (2 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_make_result()** (2 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_make_task_start()** (2 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **TempPathFactory** (2 connections)
- **DrawFn** (1 connections)
- **Stateful invariants over the session persistence round-trip.  A single sequence** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **Reduce a RunState to its persistence-invariant skeleton.      Plays → task_ids →** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **Aggregate ``StatusCounts`` across every task node in the tree.      ``build_task** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **Walk RunState the way the tree builder walks events.** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **Persist → load → replay yields the same structural state.** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **``build_task_tree`` over the persisted session agrees with the live RunState.** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **Generate a coherent (play_start → task_start → result*) sequence.      Coherence** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`

## Relationships

- [Architecture Layering Tests](Architecture_Layering_Tests.md) (4 shared connections)
- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (3 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (2 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (2 shared connections)
- [Include Role Discovery](Include_Role_Discovery.md) (2 shared connections)
- [Log Filter Helpers](Log_Filter_Helpers.md) (1 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (1 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)

## Source Files

- `tests/integration/test_invariants_session_roundtrip.py`

## Audit Trail

- EXTRACTED: 63 (93%)
- INFERRED: 5 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*