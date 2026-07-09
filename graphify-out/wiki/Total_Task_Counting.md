# Total Task Counting

> 40 nodes · cohesion 0.07

## Key Concepts

- **load_session()** (39 connections) — `src/ansible_aom/session/store.py`
- **test_meta_schema_version.py** (9 connections) — `tests/unit/test_meta_schema_version.py`
- **Path** (7 connections)
- **_start_and_end()** (7 connections) — `tests/unit/test_meta_schema_version.py`
- **TestCorruptedSessionHandling** (6 connections) — `tests/integration/test_session.py`
- **TestInspectShow** (6 connections) — `tests/integration/test_session.py`
- **.test_inspect_shows_malformed_count()** (5 connections) — `tests/integration/test_session.py`
- **TestOutputFormats** (5 connections) — `tests/integration/test_session.py`
- **test_load_session_exposes_schema_version_2()** (5 connections) — `tests/unit/test_meta_schema_version.py`
- **test_load_session_of_v2_session_round_trips_schema_version_2()** (5 connections) — `tests/unit/test_meta_schema_version.py`
- **.test_malformed_json_skipped_with_warning()** (4 connections) — `tests/integration/test_session.py`
- **.test_truncated_jsonl_handled_gracefully()** (4 connections) — `tests/integration/test_session.py`
- **.test_load_nonexistent_session_returns_none()** (4 connections) — `tests/integration/test_session.py`
- **.test_load_session_includes_events()** (4 connections) — `tests/integration/test_session.py`
- **.test_load_session_returns_meta()** (4 connections) — `tests/integration/test_session.py`
- **.test_json_output_format()** (4 connections) — `tests/integration/test_session.py`
- **.test_jsonl_output_format()** (4 connections) — `tests/integration/test_session.py`
- **test_end_session_preserves_schema_version_2()** (4 connections) — `tests/unit/test_meta_schema_version.py`
- **test_load_session_defaults_missing_schema_version_to_1()** (4 connections) — `tests/unit/test_meta_schema_version.py`
- **test_schema_version_2_coexists_with_existing_meta_fields()** (4 connections) — `tests/unit/test_meta_schema_version.py`
- **test_start_session_writes_schema_version_2()** (4 connections) — `tests/unit/test_meta_schema_version.py`
- **Load a session by ID.      Args:         session_id: The session ID to load** (1 connections) — `src/ansible_aom/session/store.py`
- **TC-231, TC-232, TC-233: Corrupted session handling.** (1 connections) — `tests/integration/test_session.py`
- **TC-231: Truncated JSONL is handled gracefully.** (1 connections) — `tests/integration/test_session.py`
- **TC-232: Malformed JSON lines skipped with WARNING.** (1 connections) — `tests/integration/test_session.py`
- *... and 15 more nodes in this community*

## Relationships

- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (18 shared connections)
- [Play Boundary State Tests](Play_Boundary_State_Tests.md) (5 shared connections)
- [Include Import Role Tasks](Include_Import_Role_Tasks.md) (4 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (2 shared connections)
- [Loop Item Line Tests](Loop_Item_Line_Tests.md) (2 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (2 shared connections)
- [Plaintext Line Handling](Plaintext_Line_Handling.md) (2 shared connections)
- [Task Summary Count Tests](Task_Summary_Count_Tests.md) (2 shared connections)
- [Panel Refresh Snapshot](Panel_Refresh_Snapshot.md) (2 shared connections)
- [Hide State Normalization](Hide_State_Normalization.md) (1 shared connections)
- [Shell Completion Helpers](Shell_Completion_Helpers.md) (1 shared connections)
- [Event Source Adapters](Event_Source_Adapters.md) (1 shared connections)

## Source Files

- `src/ansible_aom/session/store.py`
- `tests/integration/test_session.py`
- `tests/unit/test_meta_schema_version.py`

## Audit Trail

- EXTRACTED: 105 (67%)
- INFERRED: 52 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*