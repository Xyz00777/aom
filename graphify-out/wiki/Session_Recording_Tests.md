# Session Recording Tests

> 68 nodes · cohesion 0.03

## Key Concepts

- **SessionManager** (85 connections) — `src/ansible_aom/session/store.py`
- **test_session.py** (16 connections) — `tests/integration/test_session.py`
- **TestStartSession** (10 connections) — `tests/integration/test_session.py`
- **test_sink_disable_and_preflight_ms.py** (8 connections) — `tests/unit/test_sink_disable_and_preflight_ms.py`
- **TestCreateArtifact** (7 connections) — `tests/integration/test_session.py`
- **TestEndSession** (7 connections) — `tests/integration/test_session.py`
- **TestSessionFilePermissions** (7 connections) — `tests/integration/test_session.py`
- **TestRecordEvent** (6 connections) — `tests/integration/test_session.py`
- **.test_record_event_appends_to_file()** (6 connections) — `tests/integration/test_session.py`
- **.test_artifact_file_permissions()** (5 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_creates_aom_file()** (5 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_event_lines()** (5 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_metadata_header()** (5 connections) — `tests/integration/test_session.py`
- **.test_create_artifact_stats_line()** (5 connections) — `tests/integration/test_session.py`
- **.test_end_session_records_duration()** (5 connections) — `tests/integration/test_session.py`
- **.test_end_session_status_crashed()** (5 connections) — `tests/integration/test_session.py`
- **.test_end_session_status_failed()** (5 connections) — `tests/integration/test_session.py`
- **.test_end_session_updates_meta_with_status()** (5 connections) — `tests/integration/test_session.py`
- **TestInspectDiff** (5 connections) — `tests/integration/test_session.py`
- **.test_diff_shows_task_comparison()** (5 connections) — `tests/integration/test_session.py`
- **.test_record_event_json_format()** (5 connections) — `tests/integration/test_session.py`
- **.test_record_event_preserves_event_order()** (5 connections) — `tests/integration/test_session.py`
- **TestRecordStderr** (5 connections) — `tests/integration/test_session.py`
- **.test_record_stderr_utf8_encoding()** (5 connections) — `tests/integration/test_session.py`
- **.test_events_file_permissions()** (5 connections) — `tests/integration/test_session.py`
- *... and 43 more nodes in this community*

## Relationships

- [[Run Config Key Normalization]] (38 shared connections)
- [[Inspect CLI Commands]] (12 shared connections)
- [[Playbook Run Integration Tests]] (5 shared connections)
- [[UUIDv7 Session Generation]] (3 shared connections)
- [[Runner Session Recording]] (3 shared connections)
- [[Inspect Session List]] (2 shared connections)
- [[Session Diagnostics Writing]] (2 shared connections)
- [[RunState Persistence Shape]] (1 shared connections)
- [[Session Roundtrip Invariants]] (1 shared connections)
- [[Playbook Event Parsing]] (1 shared connections)

## Source Files

- `src/ansible_aom/session/store.py`
- `tests/integration/test_session.py`
- `tests/unit/test_session_meta_persistence.py`
- `tests/unit/test_sink_disable_and_preflight_ms.py`

## Audit Trail

- EXTRACTED: 237 (68%)
- INFERRED: 112 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*