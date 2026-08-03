# Panel Refresh Snapshot

> 16 nodes · cohesion 0.21

## Key Concepts

- **test_session_diagnostics.py** (12 connections) — `tests/unit/test_session_diagnostics.py`
- **Path** (7 connections)
- **_start_and_end()** (7 connections) — `tests/unit/test_session_diagnostics.py`
- **test_disk_failure_during_diagnostics_write_does_not_break_end()** (5 connections) — `tests/unit/test_session_diagnostics.py`
- **test_diagnostics_json_handles_no_run_diagnostics()** (4 connections) — `tests/unit/test_session_diagnostics.py`
- **test_diagnostics_json_written_alongside_meta()** (4 connections) — `tests/unit/test_session_diagnostics.py`
- **test_load_session_returns_diagnostics_when_present()** (4 connections) — `tests/unit/test_session_diagnostics.py`
- **test_load_session_returns_none_diagnostics_for_legacy_session()** (4 connections) — `tests/unit/test_session_diagnostics.py`
- **test_diagnostics_json_includes_aom_version()** (3 connections) — `tests/unit/test_session_diagnostics.py`
- **MonkeyPatch** (1 connections)
- **Phase 5: SessionManager writes diagnostics.json next to meta.json.  Spec: docs/s** (1 connections) — `tests/unit/test_session_diagnostics.py`
- **diagnostics.json write is best-effort: an OSError must not propagate     out of** (1 connections) — `tests/unit/test_session_diagnostics.py`
- **end_session writes diagnostics.json containing the schema version + histogram.** (1 connections) — `tests/unit/test_session_diagnostics.py`
- **If the run path never published a RunDiagnostics, schema still writes     with z** (1 connections) — `tests/unit/test_session_diagnostics.py`
- **A session directory without diagnostics.json (older session) is still loadable;** (1 connections) — `tests/unit/test_session_diagnostics.py`
- **_reset()** (1 connections) — `tests/unit/test_session_diagnostics.py`

## Relationships

- [load_session](load_session.md) (3 shared connections)
- [SessionManager](SessionManager.md) (2 shared connections)
- [core/__init__.py](core-__init__.py.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)

## Source Files

- `tests/unit/test_session_diagnostics.py`

## Audit Trail

- EXTRACTED: 57 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*