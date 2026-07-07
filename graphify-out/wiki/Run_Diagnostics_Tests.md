# Run Diagnostics Tests

> 22 nodes · cohesion 0.10

## Key Concepts

- **test_run_diagnostics.py** (17 connections) — `tests/unit/test_run_diagnostics.py`
- **_FakeSink** (9 connections) — `tests/unit/test_run_diagnostics.py`
- **test_feed_without_diag_does_not_crash()** (6 connections) — `tests/unit/test_run_diagnostics.py`
- **test_feed_with_diag_increments_histogram()** (5 connections) — `tests/unit/test_run_diagnostics.py`
- **test_run_playbook_publishes_last_run_diagnostics()** (4 connections) — `tests/unit/test_run_diagnostics.py`
- **test_run_playbook_records_lifecycle_marks_with_debug()** (4 connections) — `tests/unit/test_run_diagnostics.py`
- **_execution_parser()** (3 connections) — `tests/unit/test_run_diagnostics.py`
- **_fake_ansible_command()** (3 connections) — `tests/unit/test_run_diagnostics.py`
- **test_note_event_first_event_records_mark_regardless_of_debug()** (2 connections) — `tests/unit/test_run_diagnostics.py`
- **.end()** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **.record_event()** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **.record_stderr()** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **Tests for ``RunDiagnostics`` and the runner-side instrumentation.  Phase 3 of do** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **Lifecycle marks are now always-on (phase 15); the first event mark     fires wit** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **_reset()** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **test_last_run_diagnostics_cleared_on_reset()** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **test_last_run_diagnostics_registry()** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **test_note_event_increments_counter_and_histogram()** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **test_note_event_records_first_event_lifecycle_mark_once()** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **test_note_pty_bytes_accumulates()** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **test_note_stall_tracks_max()** (1 connections) — `tests/unit/test_run_diagnostics.py`
- **test_note_timeout_increments()** (1 connections) — `tests/unit/test_run_diagnostics.py`

## Relationships

- [[PTY Stream Parser]] (3 shared connections)
- [[Runner Session Recording]] (2 shared connections)
- [[Playbook Run Integration Tests]] (2 shared connections)
- [[Role Group Task Models]] (1 shared connections)

## Source Files

- `tests/unit/test_run_diagnostics.py`

## Audit Trail

- EXTRACTED: 57 (86%)
- INFERRED: 9 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*