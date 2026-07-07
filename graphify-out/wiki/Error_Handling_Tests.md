# Error Handling Tests

> 17 nodes · cohesion 0.04

## Key Concepts

- **test_error_handling.py** (16 connections) — `tests/integration/test_error_handling.py`
- **TestLogging** (9 connections) — `tests/integration/test_error_handling.py`
- **TestCancellationSecondCtrlC** (5 connections) — `tests/integration/test_error_handling.py`
- **TestPasswordPromptHandling** (5 connections) — `tests/integration/test_error_handling.py`
- **.test_log_path_xdg_compliant()** (4 connections) — `tests/integration/test_error_handling.py`
- **.test_log_rotation_configuration()** (4 connections) — `tests/integration/test_error_handling.py`
- **.test_log_silent_during_normal_operation()** (4 connections) — `tests/integration/test_error_handling.py`
- **TestPasswordTimeoutMechanisn** (4 connections) — `tests/integration/test_error_handling.py`
- **TestQueueHandlerLogging** (4 connections) — `tests/integration/test_error_handling.py`
- **.test_second_sigint_after_2s_is_normal()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_second_sigint_within_2s_is_immediate_exit()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_log_levels_present()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_verbose_flag_enables_debug()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_verbose_flag_info_level_without_flag()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_password_timeout_value()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_queue_handler_exists_in_stdlib()** (2 connections) — `tests/integration/test_error_handling.py`
- **Integration tests for error handling (TEST_SPECIFICATION.md Section 14).  Tests** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[PTY Stream Parser]] (7 shared connections)
- [[Run Config Key Normalization]] (3 shared connections)
- [[Stderr Capture Handling]] (2 shared connections)
- [[Cancellation Timer]] (1 shared connections)
- [[Exit Code Constants]] (1 shared connections)
- [[JSONL Parse Failure Handling]] (1 shared connections)
- [[Missing Ansible Playbook]] (1 shared connections)
- [[Password Timeout]] (1 shared connections)
- [[Process Liveness Monitoring]] (1 shared connections)
- [[Process State Monitoring]] (1 shared connections)
- [[Watchdog Timer]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 65 (93%)
- INFERRED: 5 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*