# Status Bar Liveness Tests

> 37 nodes · cohesion 0.07

## Key Concepts

- **.handle_password_prompt()** (22 connections) — `tests/unit/test_event_source.py`
- **TestCompactModeTerminalPassThrough** (13 connections) — `tests/compact/test_password.py`
- **.test_all_password_types_use_same_pass_through()** (3 connections) — `tests/compact/test_password.py`
- **.test_cursor_positioning_before_getpass()** (3 connections) — `tests/compact/test_password.py`
- **.test_cursor_positioning_silent_on_non_tty()** (3 connections) — `tests/compact/test_password.py`
- **.test_empty_password_returned_as_empty_string()** (3 connections) — `tests/compact/test_password.py`
- **.test_getpass_masks_password_input()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_prompt_text_displayed_to_user()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_returned_as_string()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_with_special_characters()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_with_unicode_characters()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_cursor_positioning_on_tty()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_delegates_to_getpass()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_empty_child_param()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_passes_prompt_text_to_getpass()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_returns_empty_on_eof()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_returns_empty_on_keyboard_interrupt()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_returns_empty_on_os_error()** (3 connections) — `tests/compact/test_password.py`
- **.test_handle_password_prompt_with_mock_pexpect_child()** (3 connections) — `tests/compact/test_password.py`
- **TC-143: handle_password_prompt uses getpass.getpass for PTY integration.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: The prompt text is passed to getpass for display on /dev/tty.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: child param exists for interface compatibility but unused in compact mod** (1 connections) — `tests/compact/test_password.py`
- **TC-143: child param accepted for TUI interface compatibility.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: Cursor positioning escape sequence written before getpass.** (1 connections) — `tests/compact/test_password.py`
- **TC-143: EOFError from getpass returns empty string (user cancelled).** (1 connections) — `tests/compact/test_password.py`
- *... and 12 more nodes in this community*

## Relationships

- [Golden Frame Tests](Golden_Frame_Tests.md) (8 shared connections)
- [Pause Lingering Cleanup](Pause_Lingering_Cleanup.md) (3 shared connections)
- [Display Helper Class](Display_Helper_Class.md) (2 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (1 shared connections)
- [Narrow Terminal View](Narrow_Terminal_View.md) (1 shared connections)

## Source Files

- `tests/compact/test_password.py`
- `tests/unit/test_event_source.py`

## Audit Trail

- EXTRACTED: 64 (62%)
- INFERRED: 40 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*