# Run History Mining

> 32 nodes · cohesion 0.10

## Key Concepts

- **_SequenceChild** (14 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **_NullSink** (12 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **test_runner_eof_watchdog.py** (11 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.test_watchdog_emits_warning_and_returns_when_no_eof()** (9 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.test_watchdog_emits_warning_via_logger()** (9 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.test_watchdog_path_calls_expect()** (9 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.test_clean_eof_after_stats_no_warning()** (8 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.test_pre_stats_timeout_does_not_trigger_watchdog()** (7 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **_start_line()** (6 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **TestWatchdogFiresAfterStats** (6 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **_stats_line()** (5 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **TestCleanEofAfterStats** (5 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **TestPreStatsSilenceUnchanged** (5 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **TestWatchdogUsesBoundedTimeout** (5 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.end()** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.record_event()** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **.record_stderr()** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **Unit tests for the EOF watchdog after ``v2_playbook_on_stats`` (R8).  R8 spec: a** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **Stand-in for ``_SessionSink`` — the runner treats both the same.** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **When the child goes silent after the stats event, the runner must     not wait f** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **Synthetic EOF after a stats event in a hung child triggers a         warning vis** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **The warning should also land in the standard logger so debug         mode surfac** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **The normal case — child emits stats, then closes stdout cleanly —     must compl** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **The watchdog only applies AFTER stats. Before stats, the runner     must keep us** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- **The post-stats ``expect`` call must use the watchdog timeout,     not the per-re** (1 connections) — `tests/unit/test_runner_eof_watchdog.py`
- *... and 7 more nodes in this community*

## Relationships

- [Run State Completion Recap](Run_State_Completion_Recap.md) (11 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (11 shared connections)
- [Architecture Layering Tests](Architecture_Layering_Tests.md) (5 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Community 611](Community_611.md) (1 shared connections)

## Source Files

- `tests/unit/test_runner_eof_watchdog.py`

## Audit Trail

- EXTRACTED: 102 (79%)
- INFERRED: 27 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*