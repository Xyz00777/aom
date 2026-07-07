# Runner Heartbeat Wiring

> 13 nodes · cohesion 0.15

## Key Concepts

- **_FakeSink** (11 connections) — `tests/unit/test_runner_heartbeat.py`
- **TestFeedNotesBytes** (7 connections) — `tests/unit/test_runner_heartbeat.py`
- **test_runner_heartbeat.py** (6 connections) — `tests/unit/test_runner_heartbeat.py`
- **TestTaskStartCountsAsHeartbeat** (6 connections) — `tests/unit/test_runner_heartbeat.py`
- **.test_task_start_does_not_clear_heartbeat()** (6 connections) — `tests/unit/test_runner_heartbeat.py`
- **_parser_in_execution_phase()** (5 connections) — `tests/unit/test_runner_heartbeat.py`
- **.test_jsonl_event_line_notes_pty_bytes()** (5 connections) — `tests/unit/test_runner_heartbeat.py`
- **.test_plaintext_line_notes_pty_bytes()** (5 connections) — `tests/unit/test_runner_heartbeat.py`
- **.end()** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- **.__init__()** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- **.record_event()** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- **.record_stderr()** (1 connections) — `tests/unit/test_runner_heartbeat.py`
- **Tests for the runner's heartbeat wiring.  The runner is responsible for feeding** (1 connections) — `tests/unit/test_runner_heartbeat.py`

## Relationships

- [[PTY Stream Parser]] (5 shared connections)
- [[Role Group Task Models]] (3 shared connections)
- [[Runner Session Recording]] (3 shared connections)
- [[CPU Sampling Probing]] (1 shared connections)

## Source Files

- `tests/unit/test_runner_heartbeat.py`

## Audit Trail

- EXTRACTED: 41 (73%)
- INFERRED: 15 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*