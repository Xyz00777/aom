# Display Helper Class

> 20 nodes · cohesion 0.10

## Key Concepts

- **TestPasswordTimeoutDefault** (12 connections) — `tests/compact/test_password.py`
- **.test_compact_renderer_exists_for_password_handling()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_handler_returns_empty_for_cancellation()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_handler_returns_string_for_success()** (3 connections) — `tests/compact/test_password.py`
- **.test_default_password_timeout_is_60()** (2 connections) — `tests/compact/test_password.py`
- **.test_default_password_timeout_is_integer()** (2 connections) — `tests/compact/test_password.py`
- **.test_default_password_timeout_positive()** (2 connections) — `tests/compact/test_password.py`
- **.test_password_handler_timeout_constant_usable_in_expect()** (2 connections) — `tests/compact/test_password.py`
- **.test_password_timeout_available_in_password_module()** (2 connections) — `tests/compact/test_password.py`
- **.test_timeout_behavior_with_mock_clock_getpass()** (2 connections) — `tests/compact/test_password.py`
- **TC-148: Verify 60s timeout default, exception on timeout.      The DEFAULT_PASSW** (1 connections) — `tests/compact/test_password.py`
- **TC-148: DEFAULT_PASSWORD_TIMEOUT equals 60 seconds.** (1 connections) — `tests/compact/test_password.py`
- **TC-148: DEFAULT_PASSWORD_TIMEOUT is an integer (seconds).** (1 connections) — `tests/compact/test_password.py`
- **TC-148: DEFAULT_PASSWORD_TIMEOUT is a positive value.** (1 connections) — `tests/compact/test_password.py`
- **TC-148: Password handling respects timeout — getpass blocks until input or timeo** (1 connections) — `tests/compact/test_password.py`
- **TC-148: CompactRenderer provides handle_password_prompt for timeout integration.** (1 connections) — `tests/compact/test_password.py`
- **TC-148: DEFAULT_PASSWORD_TIMEOUT is importable from password module.** (1 connections) — `tests/compact/test_password.py`
- **TC-148: On successful password entry, returns the password string.** (1 connections) — `tests/compact/test_password.py`
- **TC-148: On cancellation (Ctrl+C/Ctrl+D), returns empty string.          This pre** (1 connections) — `tests/compact/test_password.py`
- **TC-148: DEFAULT_PASSWORD_TIMEOUT can be used as pexpect timeout value.** (1 connections) — `tests/compact/test_password.py`

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (2 shared connections)
- [Status Bar Liveness Tests](Status_Bar_Liveness_Tests.md) (2 shared connections)
- [test_password.py](test_password.py.md) (1 shared connections)

## Source Files

- `tests/compact/test_password.py`

## Audit Trail

- EXTRACTED: 39 (91%)
- INFERRED: 4 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*