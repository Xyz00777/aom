# _fake_ansible_command

> 20 nodes · cohesion 0.13

## Key Concepts

- **_fake_ansible_command()** (8 connections) — `tests/integration/test_runner.py`
- **test_runner.py** (7 connections) — `tests/integration/test_runner.py`
- **TestRunnerPreflight** (6 connections) — `tests/integration/test_runner.py`
- **TestRunnerHappyPath** (5 connections) — `tests/integration/test_runner.py`
- **TestRunnerCommandNotFound** (4 connections) — `tests/integration/test_runner.py`
- **TestRunnerFailureExit** (4 connections) — `tests/integration/test_runner.py`
- **.test_run_playbook_calls_preflight_and_forwards_definitions()** (4 connections) — `tests/integration/test_runner.py`
- **.test_run_playbook_forwards_every_preflight_error_to_add_warning()** (4 connections) — `tests/integration/test_runner.py`
- **.test_run_playbook_marks_failed_on_nonzero_exit()** (3 connections) — `tests/integration/test_runner.py`
- **.test_run_playbook_calls_renderer_start_and_completion()** (3 connections) — `tests/integration/test_runner.py`
- **.test_run_playbook_forwards_jsonl_events_to_update_state()** (3 connections) — `tests/integration/test_runner.py`
- **.test_run_playbook_forwards_preflight_errors_as_warnings()** (3 connections) — `tests/integration/test_runner.py`
- **.test_run_playbook_returns_127_when_command_missing()** (2 connections) — `tests/integration/test_runner.py`
- **Integration tests for the ansible-playbook runner.  The runner spawns `ansible-p** (1 connections) — `tests/integration/test_runner.py`
- **Missing ansible-playbook surfaces as exit 127 without crashing.** (1 connections) — `tests/integration/test_runner.py`
- **Runner calls run_preflight before spawning and forwards its result.** (1 connections) — `tests/integration/test_runner.py`
- **Build a (command, args) pair that emits `events` as JSONL then exits.      Retur** (1 connections) — `tests/integration/test_runner.py`
- **Each error → an add_warning call, even when they share a body.          The coun** (1 connections) — `tests/integration/test_runner.py`
- **Runner spawns the subprocess and pumps events to the renderer.** (1 connections) — `tests/integration/test_runner.py`
- **Non-zero subprocess exit becomes 'failed' state.** (1 connections) — `tests/integration/test_runner.py`

## Relationships

- [run_playbook](run_playbook.md) (7 shared connections)
- [PlayDefinition](PlayDefinition.md) (5 shared connections)
- [json.py](json.py.md) (1 shared connections)

## Source Files

- `tests/integration/test_runner.py`

## Audit Trail

- EXTRACTED: 51 (81%)
- INFERRED: 12 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*