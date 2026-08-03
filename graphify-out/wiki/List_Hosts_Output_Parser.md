# List Hosts Output Parser

> 24 nodes · cohesion 0.08

## Key Concepts

- **TestPasswordPromptPTYIntegration** (26 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_cursor_positioning_on_tty()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_delegates_to_getpass()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_empty_child_param()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_passes_prompt_text_to_getpass()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_returns_empty_on_eof()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_returns_empty_on_keyboard_interrupt()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_returns_empty_on_os_error()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_with_mock_pexpect_child()** (3 connections) — `tests/compact/test_password.py`
- **.test_is_password_prompt_rejects_partial_match_only()** (3 connections) — `tests/compact/test_password.py`
- **.test_all_password_patterns_are_valid_regex()** (2 connections) — `tests/compact/test_password.py`
- **.test_password_patterns_count()** (2 connections) — `tests/compact/test_password.py`
- **TC-143: Text containing but not ending with password pattern prefix still matche** (1 connections) — `tests/compact/test_password.py`
- **TC-143: All PASSWORD_PATTERNS entries compile as valid regex.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: All 10 documented password patterns present.          Ansible-native (7)** (1 connections) — `tests/compact/test_password.py`
- **TC-143: handle_password_prompt uses getpass.getpass for PTY integration.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: The prompt text is passed to getpass for display on /dev/tty.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: child param exists for interface compatibility but unused in compact mod** (1 connections) — `tests/compact/test_password.py`
- **TC-143: child param accepted for TUI interface compatibility.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: Cursor positioning escape sequence written before getpass.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: EOFError from getpass returns empty string (user cancelled).** (1 connections) — `tests/compact/test_password.py`
- **TC-143: KeyboardInterrupt from getpass returns empty string (user cancelled).** (1 connections) — `tests/compact/test_password.py`
- **TC-143: OSError from getpass (no TTY) returns empty string.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: Verify pexpect spawns with PTY, Ansible's getpass reads from /dev/tty.** (1 connections) — `tests/compact/test_password.py`

## Relationships

- [Golden Frame Tests](Golden_Frame_Tests.md) (13 shared connections)
- [Status Bar Liveness Tests](Status_Bar_Liveness_Tests.md) (8 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [test_password.py](test_password.py.md) (1 shared connections)

## Source Files

- `tests/compact/test_password.py`

## Audit Trail

- EXTRACTED: 59 (86%)
- INFERRED: 10 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*