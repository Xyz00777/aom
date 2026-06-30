# Error Handling Tests

> 48 nodes · cohesion 0.04

## Key Concepts

- **test_error_handling.py** (28 connections) — `tests/integration/test_error_handling.py`
- **TestLogging** (11 connections) — `tests/integration/test_error_handling.py`
- **TestCancellationSecondCtrlC** (7 connections) — `tests/integration/test_error_handling.py`
- **TestPasswordPromptHandling** (7 connections) — `tests/integration/test_error_handling.py`
- **TestCancellationSavePartialSession** (6 connections) — `tests/integration/test_error_handling.py`
- **TestGracefulDegradationTreeUpdates** (6 connections) — `tests/integration/test_error_handling.py`
- **TestGracefulDegradationWarningMessage** (6 connections) — `tests/integration/test_error_handling.py`
- **TestPasswordTimeoutMechanisn** (6 connections) — `tests/integration/test_error_handling.py`
- **TestQueueHandlerLogging** (6 connections) — `tests/integration/test_error_handling.py`
- **TestStateTransitionsForAllExitCodes** (6 connections) — `tests/integration/test_error_handling.py`
- **.test_interrupt_preserves_state_before_exit()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_state_machine_accepts_valid_events_after_invalid()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_warning_logged_on_list_tasks_failure()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_log_path_xdg_compliant()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_log_rotation_configuration()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_log_silent_during_normal_operation()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_exit_code_to_state_mapping()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_second_sigint_after_2s_is_normal()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_second_sigint_within_2s_is_immediate_exit()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_log_levels_present()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_verbose_flag_enables_debug()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_verbose_flag_info_level_without_flag()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_password_timeout_value()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_queue_handler_exists_in_stdlib()** (2 connections) — `tests/integration/test_error_handling.py`
- **Integration tests for error handling (TEST_SPECIFICATION.md Section 14).  Tests** (1 connections) — `tests/integration/test_error_handling.py`
- *... and 23 more nodes in this community*

## Relationships

- [[Execution State Transitions]] (13 shared connections)
- [[PTY Stream Parser]] (11 shared connections)
- [[State Machine Module]] (9 shared connections)
- [[Run Config Key Normalization]] (3 shared connections)
- [[Stderr Capture Handling]] (2 shared connections)
- [[Run History Mining]] (1 shared connections)
- [[First Ctrl-C Cancellation]] (1 shared connections)
- [[Cancellation Timer]] (1 shared connections)
- [[Crash Recovery Auto-Save]] (1 shared connections)
- [[Crash Recovery Notification]] (1 shared connections)
- [[Crash Recovery Panels]] (1 shared connections)
- [[Crash Recovery Stay Open]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 117 (79%)
- INFERRED: 31 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*