# Session Roundtrip Invariants

> 5 nodes · cohesion 0.40

## Key Concepts

- **isolated_state_dir()** (5 connections) — `tests/conftest.py`
- **MonkeyPatch** (1 connections)
- **Path** (1 connections)
- **TempPathFactory** (1 connections)
- **Pin AOM's state directory to a per-test tmp dir for every test.      Without thi** (1 connections) — `tests/conftest.py`

## Relationships

- [Test Event Fixtures](Test_Event_Fixtures.md) (1 shared connections)

## Source Files

- `tests/conftest.py`

## Audit Trail

- EXTRACTED: 9 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*