# Host Name Resolution

> 26 nodes · cohesion 0.10

## Key Concepts

- **_FakeSink** (11 connections) — `tests/unit/test_runner_heartbeat.py`
- **TestFeedNotesBytes** (7 connections) — `tests/unit/test_runner_heartbeat.py`
- **TestSampleSubprocessActive** (7 connections) — `tests/unit/test_runner_heartbeat.py`
- **_sample_subprocess_active()** (6 connections) — `src/ansible_aom/ansible/runner.py`
- **test_runner_heartbeat.py** (6 connections) — `tests/unit/test_runner_heartbeat.py`
- **.test_task_start_does_not_clear_heartbeat()** (6 connections) — `tests/unit/test_runner_heartbeat.py`
- **_get_psutil()** (5 connections) — `src/ansible_aom/ansible/runner.py`
- **_parser_in_execution_phase()** (5 connections) — `tests/unit/test_runner_heartbeat.py`
- **.test_jsonl_event_line_notes_pty_bytes()** (5 connections) — `tests/unit/test_runner_heartbeat.py`
- **.test_plaintext_line_notes_pty_bytes()** (5 connections) — `tests/unit/test_runner_heartbeat.py`
- **_probe_psutil()** (4 connections) — `src/ansible_aom/ansible/runner.py`
- **Any** (2 connections)
- **.test_returns_bool_for_own_pid()** (2 connections) — `tests/unit/test_runner_heartbeat.py`
- **.test_returns_false_for_nonexistent_pid()** (2 connections) — `tests/unit/test_runner_heartbeat.py`
- **Return the cached psutil module, or None if probing failed.      Lazy: the first** (1 connections) — `src/ansible_aom/ansible/runner.py`
- **Return True if pid or any descendant used CPU since the last call.      Uses ``p** (1 connections) — `src/ansible_aom/ansible/runner.py`
- **Subprocess-probe ``import psutil``; return ``(module, None)`` on     success or** (1 connections) — `src/ansible_aom/ansible/runner.py`
- **.end()** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- **.__init__()** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- **.record_event()** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- **.record_stderr()** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- **Tests for the runner's heartbeat wiring.  The runner is responsible for feeding** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- **The CPU sampler degrades gracefully and never raises.** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- **Return a parser advanced past the PRE_RUN_PROMPTS gate.      ``feed_line`` only** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- **Every successful line fed to ``_feed`` bumps the heartbeat.** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- *... and 1 more nodes in this community*

## Relationships

- [Tree Block Animation](Tree_Block_Animation.md) (7 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (7 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (6 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (3 shared connections)

## Source Files

- `src/ansible_aom/ansible/runner.py`
- `tests/unit/test_runner_heartbeat.py`

## Audit Trail

- EXTRACTED: 66 (78%)
- INFERRED: 19 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*