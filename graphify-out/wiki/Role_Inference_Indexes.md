# Role Inference Indexes

> 15 nodes · cohesion 0.15

## Key Concepts

- **TestLogging** (9 connections) — `tests/integration/test_error_handling.py`
- **Path** (5 connections)
- **.test_log_path_xdg_compliant()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_log_rotation_configuration()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_log_silent_during_normal_operation()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_log_levels_present()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_verbose_flag_enables_debug()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_verbose_flag_info_level_without_flag()** (2 connections) — `tests/integration/test_error_handling.py`
- **TC-455 to TC-464: Logging tests.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-455: Log file follows XDG state directory convention.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-456: Log file written but console silent during normal operation.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-457: RotatingFileHandler with 10MB/file, 5 backups.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-459 to TC-462: Log levels for different event types.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-463: --verbose flag enables DEBUG logging to file.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-463: Without --verbose, INFO level used.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [TestStderrCapture](TestStderrCapture.md) (1 shared connections)
- [TestStderrHandling](TestStderrHandling.md) (1 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (1 shared connections)
- [Completion Host Table](Completion_Host_Table.md) (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 35 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*