# TestWatchdogTimer

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestWatchdogTimer** (7 connections) — `tests/integration/test_error_handling.py`
- **.test_watchdog_disabled_during_password()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_watchdog_error_at_300_seconds()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_watchdog_resets_on_output()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_watchdog_warning_at_60_seconds()** (2 connections) — `tests/integration/test_error_handling.py`
- **TC-484 to TC-487: Watchdog timer tests.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-484: No output for 60 seconds logs WARNING.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-485: No output for 300 seconds logs ERROR.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-486: Watchdog timer resets on any subprocess output.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-487: Watchdog disabled during password prompt phase.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [PtyStreamParser](PtyStreamParser.md) (1 shared connections)
- [Completion Host Table](Completion_Host_Table.md) (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 19 (95%)
- INFERRED: 1 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*