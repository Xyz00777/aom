# Session Roundtrip Invariants

> 17 nodes · cohesion 0.17

## Key Concepts

- **test_invariants_session_roundtrip.py** (12 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **test_tree_builder_matches_live_runstate_totals()** (9 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **event_sequences()** (6 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_drive()** (5 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_runstate_status_totals()** (5 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_tree_status_totals()** (4 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **DrawFn** (3 connections)
- **test_runstate_never_holds_orphan_hostrunstate()** (3 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_make_play_start()** (2 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_make_result()** (2 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_make_task_start()** (2 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **Stateful invariants over the session persistence round-trip.  A single sequence** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **Aggregate ``StatusCounts`` across every task node in the tree.      ``build_task** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **Walk RunState the way the tree builder walks events.** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **``build_task_tree`` over the persisted session agrees with the live RunState.** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **A ``HostRunState`` only exists under a TaskRunState we know about.      Sanity c** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **Generate a coherent (play_start → task_start → result*) sequence.      Coherence** (1 connections) — `tests/integration/test_invariants_session_roundtrip.py`

## Relationships

- [[RunState Persistence Shape]] (4 shared connections)
- [[Inspect Data Model Builders]] (3 shared connections)
- [[Run State Summary Panel]] (2 shared connections)
- [[Property Based Tests]] (1 shared connections)
- [[RunState Property Invariants]] (1 shared connections)
- [[Session Recording Tests]] (1 shared connections)
- [[Inspect CLI Commands]] (1 shared connections)

## Source Files

- `tests/integration/test_invariants_session_roundtrip.py`

## Audit Trail

- EXTRACTED: 56 (95%)
- INFERRED: 3 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*