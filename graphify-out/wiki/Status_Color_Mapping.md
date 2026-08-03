# Status Color Mapping

> 28 nodes · cohesion 0.12

## Key Concepts

- **_fake_ansible_command()** (10 connections) — `tests/integration/test_runner_session_recording.py`
- **test_runner_session_recording.py** (9 connections) — `tests/integration/test_runner_session_recording.py`
- **Path** (9 connections)
- **TestSessionRecordingHappyPath** (7 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_default_state_dir_is_used_when_none_given()** (6 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_oserror_during_record_event_disables_sink_and_warns_once()** (6 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_unwritable_session_dir_does_not_crash_run()** (5 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_records_every_jsonl_event_seen_by_runner()** (5 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_runner_records_ansible_args_in_meta()** (5 connections) — `tests/integration/test_runner_session_recording.py`
- **_read_jsonl()** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **TestSessionRecordingDefaults** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **TestSessionRecordingDisableOnDiskError** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **TestSessionRecordingFailureModes** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_creates_session_directory_with_events_and_meta()** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_meta_records_status_completed_on_success()** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_meta_records_status_failed_on_nonzero_exit()** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **TestSessionRecordingPersistsArgs** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **MonkeyPatch** (1 connections)
- **Integration tests for the runner's session recording (roadmap #14).  Every `run_** (1 connections) — `tests/integration/test_runner_session_recording.py`
- **Recording is best-effort — disk failures don't crash the run.** (1 connections) — `tests/integration/test_runner_session_recording.py`
- **If session_dir can't be written to, the playbook still runs and exits cleanly.** (1 connections) — `tests/integration/test_runner_session_recording.py`
- **R3: an OSError mid-run (disk full, FS quota, NFS hiccup) disables     further re** (1 connections) — `tests/integration/test_runner_session_recording.py`
- **(command, args) pair emitting `events` then exiting with `exit_code`.** (1 connections) — `tests/integration/test_runner_session_recording.py`
- **When no session_dir is passed, the runner picks the standard state dir.** (1 connections) — `tests/integration/test_runner_session_recording.py`
- **run_playbook must produce a session under whatever the         ``_default_sessio** (1 connections) — `tests/integration/test_runner_session_recording.py`
- *... and 3 more nodes in this community*

## Relationships

- [run_playbook](run_playbook.md) (8 shared connections)
- [SessionManager](SessionManager.md) (6 shared connections)
- [json.py](json.py.md) (1 shared connections)

## Source Files

- `tests/integration/test_runner_session_recording.py`

## Audit Trail

- EXTRACTED: 91 (87%)
- INFERRED: 14 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*