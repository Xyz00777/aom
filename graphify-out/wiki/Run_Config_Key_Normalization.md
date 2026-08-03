# Run Config Key Normalization

> 132 nodes · cohesion 0.03

## Key Concepts

- **SessionManager** (97 connections) — `src/ansible_aom/session/store.py`
- **Path** (45 connections)
- **test_session.py** (19 connections) — `tests/integration/test_session.py`
- **list_sessions()** (15 connections) — `src/ansible_aom/session/store.py`
- **test_history_roundtrip.py** (13 connections) — `tests/integration/test_history_roundtrip.py`
- **TestStartSession** (10 connections) — `tests/integration/test_session.py`
- **test_runner_pushes_prior_run_into_renderer()** (8 connections) — `tests/integration/test_history_roundtrip.py`
- **TestInspectList** (8 connections) — `tests/integration/test_session.py`
- **TestCreateArtifact** (7 connections) — `tests/integration/test_session.py`
- **TestEndSession** (7 connections) — `tests/integration/test_session.py`
- **TestSessionFilePermissions** (7 connections) — `tests/integration/test_session.py`
- **Path** (6 connections)
- **test_different_tags_match_via_fallback()** (6 connections) — `tests/integration/test_history_roundtrip.py`
- **test_failed_session_is_not_returned()** (6 connections) — `tests/integration/test_history_roundtrip.py`
- **TestCorruptedSessionHandling** (6 connections) — `tests/integration/test_session.py`
- **TestInspectShow** (6 connections) — `tests/integration/test_session.py`
- **TestRecordEvent** (6 connections) — `tests/integration/test_session.py`
- **test_different_host_count_does_not_match()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **test_most_recent_completed_wins()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **test_session_then_history_roundtrip()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **.test_inspect_shows_malformed_count()** (5 connections) — `tests/integration/test_session.py`
- **TestOutputFormats** (5 connections) — `tests/integration/test_session.py`
- **TestRecordStderr** (5 connections) — `tests/integration/test_session.py`
- **.test_record_stderr_emits_aom_stderr_line_event()** (5 connections) — `tests/integration/test_session.py`
- **TestSessionManagerInit** (5 connections) — `tests/integration/test_session.py`
- *... and 107 more nodes in this community*

## Relationships

- [StatusBarConfig Model](StatusBarConfig_Model.md) (12 shared connections)
- [Loop Item Line Tests](Loop_Item_Line_Tests.md) (11 shared connections)
- [JSON Renderer](JSON_Renderer.md) (11 shared connections)
- [Include Role Discovery](Include_Role_Discovery.md) (10 shared connections)
- [Session Storage Module](Session_Storage_Module.md) (9 shared connections)
- [Status Color Mapping](Status_Color_Mapping.md) (6 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (4 shared connections)
- [Play Boundary State Tests](Play_Boundary_State_Tests.md) (4 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (3 shared connections)
- [Keybinding Context Coverage](Keybinding_Context_Coverage.md) (3 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (2 shared connections)
- [Plaintext Line Handling](Plaintext_Line_Handling.md) (2 shared connections)

## Source Files

- `src/ansible_aom/session/store.py`
- `tests/integration/test_history_roundtrip.py`
- `tests/integration/test_session.py`

## Audit Trail

- EXTRACTED: 386 (70%)
- INFERRED: 162 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*