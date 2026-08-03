# _drive

> 54 nodes · cohesion 0.06

## Key Concepts

- **_drive()** (15 connections) — `tests/integration/test_invariants_session_roundtrip.py`
- **test_runner_eof_watchdog.py** (14 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **_SequenceChild** (14 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **_NullSink** (12 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.test_watchdog_emits_warning_and_returns_when_no_eof()** (10 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.test_watchdog_emits_warning_via_logger()** (10 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.test_watchdog_path_calls_expect()** (10 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **_FakeChildIsaliveDead** (10 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **.test_clean_eof_after_stats_no_warning()** (9 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **test_runner_isalive_in_loop.py** (9 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **.test_pre_stats_timeout_does_not_trigger_watchdog()** (8 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **test_drive_exits_promptly_when_child_dead_but_pty_open()** (7 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **_start_line()** (6 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **TestEofWatchdogConfig** (6 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **TestWatchdogFiresAfterStats** (6 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **test_drive_isalive_check_handles_eof_exception_path()** (6 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **test_drive_isalive_check_on_timeout_branch()** (6 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **_stats_line()** (5 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **TestCleanEofAfterStats** (5 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **TestPreStatsSilenceUnchanged** (5 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **TestWatchdogUsesBoundedTimeout** (5 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **_build_parser_in_post_run_recap()** (5 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **.test_watchdog_is_at_least_five_seconds()** (2 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.expect()** (2 connections) — `tests/unit/test_runner_isalive_in_loop.py`
- **.end()** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- *... and 29 more nodes in this community*

## Relationships

- [RunState](RunState.md) (17 shared connections)
- [PtyStreamParser](PtyStreamParser.md) (14 shared connections)
- [run_playbook](run_playbook.md) (10 shared connections)
- [test_invariants_session_roundtrip.py](test_invariants_session_roundtrip.py.md) (4 shared connections)
- [StreamPhase](StreamPhase.md) (3 shared connections)
- [json.py](json.py.md) (3 shared connections)
- [Runner Heartbeat Wiring](Runner_Heartbeat_Wiring.md) (1 shared connections)
- [Stale Running Cleanup](Stale_Running_Cleanup.md) (1 shared connections)

## Source Files

- `tests/integration/test_invariants_session_roundtrip.py`
- `tests/unit/test_runner_eof_watchdog.py`
- `tests/unit/test_runner_isalive_in_loop.py`

## Audit Trail

- EXTRACTED: 182 (84%)
- INFERRED: 35 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*