# Runner Heartbeat Wiring

> 22 nodes · cohesion 0.11

## Key Concepts

- **_BufferedChild** (10 connections) — `tests/unit/test_runner_events_recorded.py`
- **_NullSink** (9 connections) — `tests/unit/test_runner_events_recorded.py`
- **test_drive_feeds_each_event_when_pexpect_returns_multi_event_blob()** (8 connections) — `tests/unit/test_runner_events_recorded.py`
- **test_runner_events_recorded.py** (7 connections) — `tests/unit/test_runner_events_recorded.py`
- **test_run_playbook_writes_all_events_to_disk()** (5 connections) — `tests/unit/test_runner_events_recorded.py`
- **_events_fixture()** (4 connections) — `tests/unit/test_runner_events_recorded.py`
- **.close()** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **.expect()** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **.__init__()** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **.isalive()** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **.sendintr()** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **.end()** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **.__init__()** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **.record_event()** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **.record_stderr()** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **Path** (1 connections)
- **Regression tests for the multi-event PTY read bug.  Bug summary (R-INTERMITTENT-** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **Stand-in for the runner's session sink — records calls for assertions.** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **Single ``expect()`` returning a multi-event blob must still record     every eve** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **End-to-end: a real subprocess emitting the 8-event fixture must     produce an `** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **The 8-event fixture the original bug report used.** (1 connections) — `tests/unit/test_runner_events_recorded.py`
- **Fake pexpect child that simulates the multi-event PTY read.      Each ``expect()** (1 connections) — `tests/unit/test_runner_events_recorded.py`

## Relationships

- [PtyStreamParser](PtyStreamParser.md) (3 shared connections)
- [RunState](RunState.md) (3 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [_drive](_drive.md) (1 shared connections)
- [run_playbook](run_playbook.md) (1 shared connections)

## Source Files

- `tests/unit/test_runner_events_recorded.py`

## Audit Trail

- EXTRACTED: 51 (86%)
- INFERRED: 8 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*