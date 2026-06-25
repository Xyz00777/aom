# Replay Frame Signatures

> 13 nodes · cohesion 0.17

## Key Concepts

- **conftest.py** (5 connections) — `tests/fixtures/sessions/conftest.py`
- **load_session_dict()** (5 connections) — `tests/fixtures/sessions/conftest.py`
- **test_tree_frame_signatures_are_deterministic_and_stable()** (4 connections) — `tests/integration/test_replay_determinism.py`
- **_resolve()** (4 connections) — `tests/fixtures/sessions/conftest.py`
- **_tree_frame_signatures()** (3 connections) — `tests/integration/test_replay_determinism.py`
- **copy_session_fixture()** (3 connections) — `tests/fixtures/sessions/conftest.py`
- **session_fixtures_dir()** (3 connections) — `tests/fixtures/sessions/conftest.py`
- **Recorded replay frames should be reproducible and keep row order stable.** (1 connections) — `tests/integration/test_replay_determinism.py`
- **Loaders for curated session fixtures.  Each subdirectory under ``tests/fixtures/** (1 connections) — `tests/fixtures/sessions/conftest.py`
- **Map a friendly name or raw session_id to its fixture directory.** (1 connections) — `tests/fixtures/sessions/conftest.py`
- **Load a curated session fixture as a dict matching load_session().** (1 connections) — `tests/fixtures/sessions/conftest.py`
- **Path to the curated session fixtures directory.** (1 connections) — `tests/fixtures/sessions/conftest.py`
- **Return a callable that copies a curated session into tmp_path/sessions/.** (1 connections) — `tests/fixtures/sessions/conftest.py`

## Relationships

- [[Replay Determinism Tests]] (3 shared connections)
- [[Run Config Key Normalization]] (3 shared connections)
- [[Playbook Event Parsing]] (1 shared connections)

## Source Files

- `tests/fixtures/sessions/conftest.py`
- `tests/integration/test_replay_determinism.py`

## Audit Trail

- EXTRACTED: 32 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*