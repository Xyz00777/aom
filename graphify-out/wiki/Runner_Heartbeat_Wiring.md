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

- [Run State Completion Recap](Run_State_Completion_Recap.md) (3 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (3 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Architecture Layering Tests](Architecture_Layering_Tests.md) (1 shared connections)
- [Replay Determinism Tests](Replay_Determinism_Tests.md) (1 shared connections)

## Source Files

- `tests/unit/test_runner_events_recorded.py`

## Audit Trail

- EXTRACTED: 51 (86%)
- INFERRED: 8 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*