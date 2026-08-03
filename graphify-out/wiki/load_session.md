# load_session

> 54 nodes · cohesion 0.07

## Key Concepts

- **load_session()** (50 connections) — `src/ansible_aom/session/store.py`
- **store.py** (34 connections) — `src/ansible_aom/session/store.py`
- **inspect/cli.py** (27 connections) — `src/ansible_aom/inspect/cli.py`
- **rerun/cli.py** (22 connections) — `src/ansible_aom/rerun/cli.py`
- **main()** (18 connections) — `src/ansible_aom/cli.py`
- **list_sessions()** (14 connections) — `src/ansible_aom/session/store.py`
- **load_session_meta()** (14 connections) — `src/ansible_aom/session/store.py`
- **inspect_text()** (12 connections) — `src/ansible_aom/inspect/cli.py`
- **main()** (12 connections) — `src/ansible_aom/rerun/cli.py`
- **find_latest_session()** (11 connections) — `src/ansible_aom/session/store.py`
- **._reload_runs()** (11 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **main()** (10 connections) — `src/ansible_aom/inspect/cli.py`
- **ensure_index()** (10 connections) — `src/ansible_aom/session/index.py`
- **cleanup_old_sessions()** (10 connections) — `src/ansible_aom/session/store.py`
- **._load_model_blocking()** (10 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **install_from_env()** (9 connections) — `src/ansible_aom/core/diagnostics.py`
- **Path** (9 connections)
- **inspect_debug()** (8 connections) — `src/ansible_aom/inspect/cli.py`
- **test_session_helpers.py** (7 connections) — `tests/unit/test_session_helpers.py`
- **inspect_tui()** (6 connections) — `src/ansible_aom/inspect/cli.py`
- **inspect_prune()** (5 connections) — `src/ansible_aom/inspect/cli.py`
- **Path** (5 connections)
- **_build_parser()** (4 connections) — `src/ansible_aom/inspect/cli.py`
- **prewarm_parallel_pool()** (4 connections) — `src/ansible_aom/session/index.py`
- **Any** (4 connections)
- *... and 29 more nodes in this community*

## Relationships

- [Path](Path.md) (19 shared connections)
- [index.py](index.py.md) (16 shared connections)
- [diagnostics.py](diagnostics.py.md) (8 shared connections)
- [ansible_aom/cli.py](ansible_aom-cli.py.md) (7 shared connections)
- [InspectApp](InspectApp.md) (7 shared connections)
- [test_inspect_index_wiring.py](test_inspect_index_wiring.py.md) (7 shared connections)
- [inspect.py](inspect.py.md) (7 shared connections)
- [json.py](json.py.md) (7 shared connections)
- [text.py](text.py.md) (5 shared connections)
- [Play Boundary State Tests](Play_Boundary_State_Tests.md) (5 shared connections)
- [Color ASCII Fallback](Color_ASCII_Fallback.md) (4 shared connections)
- [_AsyncEventWriter](_AsyncEventWriter.md) (4 shared connections)

## Source Files

- `src/ansible_aom/cli.py`
- `src/ansible_aom/core/diagnostics.py`
- `src/ansible_aom/inspect/cli.py`
- `src/ansible_aom/rerun/cli.py`
- `src/ansible_aom/session/__init__.py`
- `src/ansible_aom/session/index.py`
- `src/ansible_aom/session/store.py`
- `src/ansible_aom/tui/screens/inspect.py`
- `tests/unit/test_session_helpers.py`

## Audit Trail

- EXTRACTED: 354 (95%)
- INFERRED: 18 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*