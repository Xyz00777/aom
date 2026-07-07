# RunState Persistence Shape

> 5 nodes · cohesion 0.29

## Key Concepts

- **test_session_roundtrip_preserves_state_shape()** (8 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **_shape()** (5 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **isolated_state_dir()** (5 connections) — `tests/conftest.py`
- **TempPathFactory** (3 connections)
- **Pin AOM's state directory to a per-test tmp dir for every test.      Without thi** (1 connections) — `tests/conftest.py`

## Relationships

- [[Session Roundtrip Invariants]] (4 shared connections)
- [[Role Group Task Models]] (1 shared connections)
- [[Session Recording Tests]] (1 shared connections)
- [[Inspect CLI Commands]] (1 shared connections)
- [[Run Config Key Normalization]] (1 shared connections)
- [[Inventory Auto Detection]] (1 shared connections)
- [[Test Event Fixtures]] (1 shared connections)

## Source Files

- `tests/conftest.py`
- `tests/integration/test_invariants_session_roundtrip.py`

## Audit Trail

- EXTRACTED: 20 (91%)
- INFERRED: 2 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*