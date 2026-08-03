# Include Role Discovery

> 84 nodes · cohesion 0.06

## Key Concepts

- **load_session()** (50 connections) — `src/ansible_aom/session/store.py`
- **index.py** (41 connections) — `src/ansible_aom/session/index.py`
- **test_session_index.py** (26 connections) — `tests/unit/test_session_index.py`
- **build_index()** (25 connections) — `src/ansible_aom/session/index.py`
- **Path** (20 connections)
- **_write_session()** (20 connections) — `tests/unit/test_session_index.py`
- **index_is_fresh()** (18 connections) — `src/ansible_aom/session/index.py`
- **load_structure()** (18 connections) — `src/ansible_aom/session/index.py`
- **Path** (15 connections)
- **load_summary()** (12 connections) — `src/ansible_aom/session/index.py`
- **query_verbose()** (11 connections) — `src/ansible_aom/session/index.py`
- **read_event()** (11 connections) — `src/ansible_aom/session/index.py`
- **SessionIndex** (10 connections) — `src/ansible_aom/core/inspect_model.py`
- **summary_from_index()** (10 connections) — `src/ansible_aom/core/inspect_model.py`
- **ensure_index()** (10 connections) — `src/ansible_aom/session/index.py`
- **events_stat()** (10 connections) — `src/ansible_aom/session/index.py`
- **index_path()** (10 connections) — `src/ansible_aom/session/index.py`
- **load_tree()** (10 connections) — `src/ansible_aom/session/index.py`
- **._load_model_blocking()** (10 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **EventRef** (9 connections) — `src/ansible_aom/core/inspect_model.py`
- **build_indexes()** (9 connections) — `src/ansible_aom/session/index.py`
- **sessions_needing_index()** (9 connections) — `src/ansible_aom/session/index.py`
- **test_query_verbose_matches_in_memory_builder()** (8 connections) — `tests/unit/test_session_index.py`
- **.finish()** (7 connections) — `src/ansible_aom/core/inspect_model.py`
- **find_task_id_by_name()** (7 connections) — `src/ansible_aom/session/index.py`
- *... and 59 more nodes in this community*

## Relationships

- [Log Filter Helpers](Log_Filter_Helpers.md) (26 shared connections)
- [ASCII Status Icon Fallback](ASCII_Status_Icon_Fallback.md) (16 shared connections)
- [Data Model Unit Tests](Data_Model_Unit_Tests.md) (14 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (12 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (10 shared connections)
- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (6 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (6 shared connections)
- [Task Summary Count Tests](Task_Summary_Count_Tests.md) (6 shared connections)
- [Diagnostics and Profiler](Diagnostics_and_Profiler.md) (5 shared connections)
- [Play Boundary State Tests](Play_Boundary_State_Tests.md) (5 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (4 shared connections)
- [Include Import Role Tasks](Include_Import_Role_Tasks.md) (4 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `src/ansible_aom/session/index.py`
- `src/ansible_aom/session/store.py`
- `src/ansible_aom/tui/screens/inspect.py`
- `tests/unit/test_session_index.py`

## Audit Trail

- EXTRACTED: 534 (94%)
- INFERRED: 35 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*