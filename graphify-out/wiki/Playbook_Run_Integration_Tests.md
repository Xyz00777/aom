# Playbook Run Integration Tests

> 23 nodes · cohesion 0.10

## Key Concepts

- **run_playbook()** (77 connections) — `src/ansible_aom/ansible/runner.py`
- **_fake_ansible_command()** (10 connections) — `tests/integration/test_runner_session_recording.py`
- **test_runner_session_recording.py** (8 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_default_state_dir_is_used_when_none_given()** (8 connections) — `tests/integration/test_runner_session_recording.py`
- **TestSessionRecordingHappyPath** (7 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_oserror_during_record_event_disables_sink_and_warns_once()** (6 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_unwritable_session_dir_does_not_crash_run()** (6 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_records_every_jsonl_event_seen_by_runner()** (6 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_runner_records_ansible_args_in_meta()** (6 connections) — `tests/integration/test_runner_session_recording.py`
- **_read_jsonl()** (5 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_creates_session_directory_with_events_and_meta()** (5 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_meta_records_status_completed_on_success()** (5 connections) — `tests/integration/test_runner_session_recording.py`
- **.test_meta_records_status_failed_on_nonzero_exit()** (5 connections) — `tests/integration/test_runner_session_recording.py`
- **TestSessionRecordingDefaults** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **TestSessionRecordingDisableOnDiskError** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **TestSessionRecordingFailureModes** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **TestSessionRecordingPersistsArgs** (4 connections) — `tests/integration/test_runner_session_recording.py`
- **TestNoPromptNoSpuriousInteractiveCall** (3 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_normal_jsonl_run_does_not_call_interactive_prompt()** (2 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **A normal run with no prompts must NOT call handle_interactive_prompt.** (1 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **Integration tests for the runner's session recording (roadmap #14).  Every `run_** (1 connections) — `tests/integration/test_runner_session_recording.py`
- **(command, args) pair emitting `events` then exiting with `exit_code`.** (1 connections) — `tests/integration/test_runner_session_recording.py`
- **A normal run produces a session directory with events + meta.** (1 connections) — `tests/integration/test_runner_session_recording.py`

## Relationships

- [[Run Config Key Normalization]] (13 shared connections)
- [[Interactive Prompt Tests]] (12 shared connections)
- [[Runner Session Recording]] (9 shared connections)
- [[Ansible Runner Subprocess]] (7 shared connections)
- [[Session Recording Tests]] (5 shared connections)
- [[Renderer Event Protocol]] (2 shared connections)
- [[No-Record Integration Test]] (2 shared connections)
- [[Replay Determinism Tests]] (2 shared connections)
- [[Session Replay Round Trip]] (2 shared connections)
- [[No Record Flag]] (2 shared connections)
- [[Run Diagnostics Tests]] (2 shared connections)
- [[Parallel Pre-flight Runner]] (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/runner.py`
- `tests/integration/test_runner_interactive_prompts.py`
- `tests/integration/test_runner_session_recording.py`

## Audit Trail

- EXTRACTED: 106 (59%)
- INFERRED: 73 (41%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*