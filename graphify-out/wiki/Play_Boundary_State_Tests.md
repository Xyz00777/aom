# Play Boundary State Tests

> 33 nodes · cohesion 0.10

## Key Concepts

- **Path** (12 connections)
- **test_replay_schema_boundary.py** (9 connections) — `tests/unit/test_replay_schema_boundary.py`
- **_make_v1_and_v2_sessions()** (8 connections) — `tests/unit/test_replay_schema_boundary.py`
- **_make_v1_session()** (7 connections) — `tests/unit/test_replay_schema_boundary.py`
- **_make_v2_session()** (7 connections) — `tests/unit/test_replay_schema_boundary.py`
- **TestLoadSessionSchemaBranch** (6 connections) — `tests/unit/test_replay_schema_boundary.py`
- **TestReplayHonorsSchemaBoundary** (6 connections) — `tests/unit/test_replay_schema_boundary.py`
- **.test_replay_both_regimes_with_identical_event_stream()** (6 connections) — `tests/unit/test_replay_schema_boundary.py`
- **test_load_session_branches_at_schema_boundary()** (5 connections) — `tests/unit/test_replay_schema_boundary.py`
- **.test_v1_session_loads_with_defaulted_schema_version_1()** (5 connections) — `tests/unit/test_replay_schema_boundary.py`
- **.test_v2_session_loads_with_schema_version_2_verbatim()** (5 connections) — `tests/unit/test_replay_schema_boundary.py`
- **.test_v2_session_written_by_session_manager_round_trips_as_v2()** (5 connections) — `tests/unit/test_replay_schema_boundary.py`
- **.test_replay_v1_session_drives_renderer_to_completion()** (5 connections) — `tests/unit/test_replay_schema_boundary.py`
- **.test_replay_v2_session_drives_renderer_to_completion()** (5 connections) — `tests/unit/test_replay_schema_boundary.py`
- **TestSchemaBoundarySideBySide** (5 connections) — `tests/unit/test_replay_schema_boundary.py`
- **.test_replay_v1_and_v2_in_same_dir_both_complete()** (5 connections) — `tests/unit/test_replay_schema_boundary.py`
- **.test_v1_and_v2_loaded_from_same_dir_branch_independently()** (5 connections) — `tests/unit/test_replay_schema_boundary.py`
- **Schema-boundary regression test (Phase 8 / Task 8.3).  What this test pins -----** (1 connections) — `tests/unit/test_replay_schema_boundary.py`
- **Build a current AOM v2 session: meta.json carries ``_schema_version: 2``.      T** (1 connections) — `tests/unit/test_replay_schema_boundary.py`
- **Build both regimes side-by-side in the same ``base`` directory.      Returning t** (1 connections) — `tests/unit/test_replay_schema_boundary.py`
- **``load_session`` is the branch site. Pin both sides here.** (1 connections) — `tests/unit/test_replay_schema_boundary.py`
- **Legacy v1 meta.json → ``_schema_version`` defaults to ``1``.** (1 connections) — `tests/unit/test_replay_schema_boundary.py`
- **v2 meta.json → ``_schema_version`` stays at ``2``, not rewritten to ``1``.** (1 connections) — `tests/unit/test_replay_schema_boundary.py`
- **End-to-end: ``SessionManager`` writes ``2``; ``load_session`` returns ``2``.** (1 connections) — `tests/unit/test_replay_schema_boundary.py`
- **The schema boundary must be invisible to ``replay_session`` and the renderer.** (1 connections) — `tests/unit/test_replay_schema_boundary.py`
- *... and 8 more nodes in this community*

## Relationships

- [Total Task Counting](Total_Task_Counting.md) (5 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (4 shared connections)
- [Hide State Normalization](Hide_State_Normalization.md) (4 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/unit/test_replay_schema_boundary.py`

## Audit Trail

- EXTRACTED: 109 (89%)
- INFERRED: 13 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*