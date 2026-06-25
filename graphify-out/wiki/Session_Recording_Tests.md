# Session Recording Tests

> 103 nodes · cohesion 0.03

## Key Concepts

- **SessionManager** (75 connections) — `src/ansible_aom/session/store.py`
- **test_session.py** (17 connections) — `tests/integration/test_session.py`
- **TestStartSession** (10 connections) — `tests/integration/test_session.py`
- **test_sink_disable_and_preflight_ms.py** (8 connections) — `tests/unit/test_sink_disable_and_preflight_ms.py`
- **TestCreateArtifact** (7 connections) — `tests/integration/test_session.py`
- **TestEndSession** (7 connections) — `tests/integration/test_session.py`
- **TestSessionFilePermissions** (7 connections) — `tests/integration/test_session.py`
- **TestRecordEvent** (6 connections) — `tests/integration/test_session.py`
- **TestRecordStderr** (5 connections) — `tests/integration/test_session.py`
- **TestSessionManagerInit** (5 connections) — `tests/integration/test_session.py`
- **TestArtifactPermissions** (4 connections) — `tests/integration/test_session.py`
- **.test_artifact_file_permissions()** (4 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_creates_aom_file()** (4 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_event_lines()** (4 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_metadata_header()** (4 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_stats_line()** (4 connections) — `tests/integration/test_session.py`
- **.test_end_session_records_duration()** (4 connections) — `tests/integration/test_session.py`
- **.test_end_session_status_crashed()** (4 connections) — `tests/integration/test_session.py`
- **.test_end_session_status_failed()** (4 connections) — `tests/integration/test_session.py`
- **.test_end_session_updates_meta_with_status()** (4 connections) — `tests/integration/test_session.py`
- **TestInspectDiff** (4 connections) — `tests/integration/test_session.py`
- **.test_diff_shows_task_comparison()** (4 connections) — `tests/integration/test_session.py`
- **.test_record_event_appends_to_file()** (4 connections) — `tests/integration/test_session.py`
- **.test_record_event_json_format()** (4 connections) — `tests/integration/test_session.py`
- **.test_record_event_preserves_event_order()** (4 connections) — `tests/integration/test_session.py`
- *... and 78 more nodes in this community*

## Relationships

- [[Run Config Key Normalization]] (41 shared connections)
- [[Inspect CLI Commands]] (10 shared connections)
- [[Playbook Run Integration Tests]] (5 shared connections)
- [[UUIDv7 Session Generation]] (3 shared connections)
- [[Runner Session Recording]] (3 shared connections)
- [[Inspect Session List]] (2 shared connections)
- [[Session Diagnostics Writing]] (2 shared connections)
- [[Run History Mining]] (1 shared connections)
- [[RunState Persistence Shape]] (1 shared connections)
- [[Session Roundtrip Invariants]] (1 shared connections)
- [[Playbook Event Parsing]] (1 shared connections)

## Source Files

- `src/ansible_aom/session/store.py`
- `tests/integration/test_session.py`
- `tests/unit/test_session_meta_persistence.py`
- `tests/unit/test_sink_disable_and_preflight_ms.py`

## Audit Trail

- EXTRACTED: 245 (70%)
- INFERRED: 105 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*