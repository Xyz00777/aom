# Renderer Module Init

> 11 nodes · cohesion 0.24

## Key Concepts

- **sessions/conftest.py** (7 connections) — `tests/fixtures/sessions/conftest.py`
- **load_session_dict()** (5 connections) — `tests/fixtures/sessions/conftest.py`
- **_resolve()** (4 connections) — `tests/fixtures/sessions/conftest.py`
- **copy_session_fixture()** (3 connections) — `tests/fixtures/sessions/conftest.py`
- **Path** (3 connections)
- **session_fixtures_dir()** (3 connections) — `tests/fixtures/sessions/conftest.py`
- **Loaders for curated session fixtures.  Each subdirectory under ``tests/fixtures/** (1 connections) — `tests/fixtures/sessions/conftest.py`
- **Map a friendly name or raw session_id to its fixture directory.** (1 connections) — `tests/fixtures/sessions/conftest.py`
- **Load a curated session fixture as a dict matching load_session().** (1 connections) — `tests/fixtures/sessions/conftest.py`
- **Path to the curated session fixtures directory.** (1 connections) — `tests/fixtures/sessions/conftest.py`
- **Return a callable that copies a curated session into tmp_path/sessions/.** (1 connections) — `tests/fixtures/sessions/conftest.py`

## Relationships

- [test_replay_determinism.py](test_replay_determinism.py.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [List-Tasks Failure Handling](List-Tasks_Failure_Handling.md) (1 shared connections)

## Source Files

- `tests/fixtures/sessions/conftest.py`

## Audit Trail

- EXTRACTED: 30 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*