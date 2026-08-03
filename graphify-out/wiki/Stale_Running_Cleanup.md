# Stale Running Cleanup

> 19 nodes · cohesion 0.16

## Key Concepts

- **test_runner_watchdog_endtime.py** (12 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **_RecordingChild** (11 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **_drive_short()** (9 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **test_post_stats_watchdog_drops_to_quiet_after_end_time()** (8 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **test_pre_end_time_uses_full_watchdog()** (8 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **_start_line()** (3 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **_stats_line()** (3 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **Any** (2 connections)
- **.expect()** (2 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **test_quiet_constant_is_smaller_than_full_watchdog()** (2 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **R11 — tighter post-stats EOF watchdog once ``end_time`` is set.  R11 spec: the 3** (1 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **R11: after ``state.end_time`` is set, post-stats timeout shrinks.      The runne** (1 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **R11: until stats is consumed, full ``_EOF_WATCHDOG_S`` applies.      Once the pa** (1 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **R11 invariant: ``_EOF_WATCHDOG_S_QUIET`` < ``_EOF_WATCHDOG_S``.      The whole p** (1 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **Fake pexpect child that records every expect() timeout and never hangs.      Aft** (1 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **Run ``_drive`` with a renderer+sink that prevent pexpect errors.      The dummy** (1 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **.close()** (1 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **.__init__()** (1 connections) — `tests/unit/test_runner_watchdog_endtime.py`
- **.isalive()** (1 connections) — `tests/unit/test_runner_watchdog_endtime.py`

## Relationships

- [Run State Completion Recap](Run_State_Completion_Recap.md) (4 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (4 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (2 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (2 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Architecture Layering Tests](Architecture_Layering_Tests.md) (1 shared connections)

## Source Files

- `tests/unit/test_runner_watchdog_endtime.py`

## Audit Trail

- EXTRACTED: 65 (94%)
- INFERRED: 4 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*