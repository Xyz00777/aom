# Run Config Key Normalization

> 109 nodes · cohesion 0.03

## Key Concepts

- **SessionManager** (86 connections) — `src/ansible_aom/session/store.py`
- **Path** (45 connections)
- **test_session.py** (17 connections) — `tests/integration/test_session.py`
- **TestStartSession** (10 connections) — `tests/integration/test_session.py`
- **test_history_roundtrip.py** (9 connections) — `tests/integration/test_history_roundtrip.py`
- **Path** (8 connections)
- **test_runner_pushes_prior_run_into_renderer()** (8 connections) — `tests/integration/test_history_roundtrip.py`
- **TestCreateArtifact** (7 connections) — `tests/integration/test_session.py`
- **TestEndSession** (7 connections) — `tests/integration/test_session.py`
- **TestSessionFilePermissions** (7 connections) — `tests/integration/test_session.py`
- **Path** (6 connections)
- **test_different_tags_match_via_fallback()** (6 connections) — `tests/integration/test_history_roundtrip.py`
- **test_failed_session_is_not_returned()** (6 connections) — `tests/integration/test_history_roundtrip.py`
- **TestRecordEvent** (6 connections) — `tests/integration/test_session.py`
- **test_different_host_count_does_not_match()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **test_most_recent_completed_wins()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **test_session_then_history_roundtrip()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **TestRecordStderr** (5 connections) — `tests/integration/test_session.py`
- **TestSessionManagerInit** (5 connections) — `tests/integration/test_session.py`
- **TestArtifactPermissions** (4 connections) — `tests/integration/test_session.py`
- **.test_artifact_file_permissions()** (4 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_creates_aom_file()** (4 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_event_lines()** (4 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_metadata_header()** (4 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_stats_line()** (4 connections) — `tests/integration/test_session.py`
- *... and 84 more nodes in this community*

## Relationships

- [Total Task Counting](Total_Task_Counting.md) (18 shared connections)
- [Loop Item Line Tests](Loop_Item_Line_Tests.md) (12 shared connections)
- [JSON Renderer](JSON_Renderer.md) (11 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (7 shared connections)
- [Status Color Mapping](Status_Color_Mapping.md) (6 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (4 shared connections)
- [Play Boundary State Tests](Play_Boundary_State_Tests.md) (4 shared connections)
- [Keybinding Context Coverage](Keybinding_Context_Coverage.md) (3 shared connections)
- [Session Storage Module](Session_Storage_Module.md) (3 shared connections)
- [Plaintext Line Handling](Plaintext_Line_Handling.md) (2 shared connections)
- [Panel Refresh Snapshot](Panel_Refresh_Snapshot.md) (2 shared connections)
- [Community 574](Community_574.md) (2 shared connections)

## Source Files

- `src/ansible_aom/session/store.py`
- `tests/integration/test_history_roundtrip.py`
- `tests/integration/test_session.py`

## Audit Trail

- EXTRACTED: 317 (71%)
- INFERRED: 132 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*