# Global Key Bindings

> 17 nodes · cohesion 0.19

## Key Concepts

- **_make_play()** (9 connections) — `tests/unit/test_run_state_index.py`
- **TestTaskDefIndex** (8 connections) — `tests/unit/test_run_state_index.py`
- **test_run_state_index.py** (7 connections) — `tests/unit/test_run_state_index.py`
- **TestPlayDefIndex** (7 connections) — `tests/unit/test_run_state_index.py`
- **_make_task()** (6 connections) — `tests/unit/test_run_state_index.py`
- **TestIndexReassignment** (6 connections) — `tests/unit/test_run_state_index.py`
- **.test_perf_012_resolve_play_hosts_o1()** (5 connections) — `tests/unit/test_run_state_index.py`
- **.test_play_index_handles_unknown_play_name()** (5 connections) — `tests/unit/test_run_state_index.py`
- **.test_perf_010_index_built_on_definitions_assignment()** (5 connections) — `tests/unit/test_run_state_index.py`
- **.test_perf_011_graft_uses_index_not_linear_scan()** (5 connections) — `tests/unit/test_run_state_index.py`
- **.test_perf_012_path_index_disambiguates_async_launcher_and_status()** (5 connections) — `tests/unit/test_run_state_index.py`
- **.test_reassigning_definitions_rebuilds_index()** (4 connections) — `tests/unit/test_run_state_index.py`
- **_resolve_play_hosts uses _play_def_by_name dict lookup.** (1 connections) — `tests/unit/test_run_state_index.py`
- **Unknown play name → empty list, just like the linear scan returned.** (1 connections) — `tests/unit/test_run_state_index.py`
- **After definitions = [...], _task_def_index contains every leaf by name.** (1 connections) — `tests/unit/test_run_state_index.py`
- **_graft_or_match_task must NOT call _iter_leaf_task_defs.          Mock _iter_lea** (1 connections) — `tests/unit/test_run_state_index.py`
- **Async launcher + async-status rows with the same display name stay separate.** (1 connections) — `tests/unit/test_run_state_index.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (15 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (5 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (3 shared connections)
- [core/__init__.py](core-__init__.py.md) (1 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)

## Source Files

- `tests/unit/test_run_state_index.py`

## Audit Trail

- EXTRACTED: 57 (74%)
- INFERRED: 20 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*