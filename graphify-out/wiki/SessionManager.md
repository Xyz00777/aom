# SessionManager

> 66 nodes · cohesion 0.05

## Key Concepts

- **SessionManager** (97 connections) — `src/ansible_aom/session/store.py`
- **test_session_store_async_write.py** (12 connections) — `tests/unit/test_session_store_async_write.py`
- **Path** (9 connections)
- **TestCreateArtifact** (7 connections) — `tests/integration/test_session.py`
- **TestEndSession** (7 connections) — `tests/integration/test_session.py`
- **TestRecordEvent** (6 connections) — `tests/integration/test_session.py`
- **test_session_meta_persistence.py** (5 connections) — `tests/unit/test_session_meta_persistence.py`
- **_break_events_file()** (5 connections) — `tests/unit/test_session_store_async_write.py`
- **test_queue_full_drops_event_and_counts()** (5 connections) — `tests/unit/test_session_store_async_write.py`
- **test_record_event_returns_quickly()** (5 connections) — `tests/unit/test_session_store_async_write.py`
- **test_write_failure_does_not_propagate()** (5 connections) — `tests/unit/test_session_store_async_write.py`
- **test_write_failure_surfaces_via_recording_failed()** (5 connections) — `tests/unit/test_session_store_async_write.py`
- **.test_create_artifact_creates_aom_file()** (4 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_event_lines()** (4 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_metadata_header()** (4 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_stats_line()** (4 connections) — `tests/integration/test_session.py`
- **.test_end_session_records_duration()** (4 connections) — `tests/integration/test_session.py`
- **.test_end_session_status_crashed()** (4 connections) — `tests/integration/test_session.py`
- **.test_end_session_status_failed()** (4 connections) — `tests/integration/test_session.py`
- **.test_end_session_updates_meta_with_status()** (4 connections) — `tests/integration/test_session.py`
- **.test_record_event_appends_to_file()** (4 connections) — `tests/integration/test_session.py`
- **.test_record_event_json_format()** (4 connections) — `tests/integration/test_session.py`
- **.test_record_event_preserves_event_order()** (4 connections) — `tests/integration/test_session.py`
- **test_end_session_without_counts_writes_nulls()** (4 connections) — `tests/unit/test_session_meta_persistence.py`
- **test_index_built_from_complete_events_after_end_session()** (4 connections) — `tests/unit/test_session_store_async_write.py`
- *... and 41 more nodes in this community*

## Relationships

- [Path](Path.md) (38 shared connections)
- [_AsyncEventWriter](_AsyncEventWriter.md) (7 shared connections)
- [test_history_roundtrip.py](test_history_roundtrip.py.md) (6 shared connections)
- [Status Color Mapping](Status_Color_Mapping.md) (6 shared connections)
- [run_playbook](run_playbook.md) (4 shared connections)
- [load_session](load_session.md) (4 shared connections)
- [Play Boundary State Tests](Play_Boundary_State_Tests.md) (4 shared connections)
- [TestRecordStderr](TestRecordStderr.md) (3 shared connections)
- [Keybinding Context Coverage](Keybinding_Context_Coverage.md) (2 shared connections)
- [test_invariants_session_roundtrip.py](test_invariants_session_roundtrip.py.md) (2 shared connections)
- [test_inspect_index_wiring.py](test_inspect_index_wiring.py.md) (2 shared connections)
- [Total Task Counting](Total_Task_Counting.md) (2 shared connections)

## Source Files

- `src/ansible_aom/session/store.py`
- `tests/integration/test_session.py`
- `tests/unit/test_session_meta_persistence.py`
- `tests/unit/test_session_store_async_write.py`

## Audit Trail

- EXTRACTED: 232 (83%)
- INFERRED: 49 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*