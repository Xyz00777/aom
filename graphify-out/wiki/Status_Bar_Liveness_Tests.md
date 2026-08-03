# Status Bar Liveness Tests

> 21 nodes · cohesion 0.13

## Key Concepts

- **.handle_password_prompt()** (22 connections) — `tests/unit/test_event_source.py`
- **TestCompactModeTerminalPassThrough** (12 connections) — `tests/compact/test_password.py`
- **.test_all_password_types_use_same_pass_through()** (3 connections) — `tests/compact/test_password.py`
- **.test_cursor_positioning_before_getpass()** (3 connections) — `tests/compact/test_password.py`
- **.test_cursor_positioning_silent_on_non_tty()** (3 connections) — `tests/compact/test_password.py`
- **.test_empty_password_returned_as_empty_string()** (3 connections) — `tests/compact/test_password.py`
- **.test_getpass_masks_password_input()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_prompt_text_displayed_to_user()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_returned_as_string()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_with_special_characters()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_with_unicode_characters()** (3 connections) — `tests/compact/test_password.py`
- **TC-145: Verify password masked by getpass, sent to PTY.      In compact mode, th** (1 connections) — `tests/compact/test_password.py`
- **TC-145: getpass.getpass is used which masks input (no echo).** (1 connections) — `tests/compact/test_password.py`
- **TC-145: The prompt text (e.g., 'Vault password: ') is shown to user via getpass.** (1 connections) — `tests/compact/test_password.py`
- **TC-145: All password prompt types use the same terminal pass-through path.** (1 connections) — `tests/compact/test_password.py`
- **TC-145: Password returned as a plain string for PTY sending.** (1 connections) — `tests/compact/test_password.py`
- **TC-145: Passwords with special characters handled correctly.** (1 connections) — `tests/compact/test_password.py`
- **TC-145: Passwords with unicode characters handled correctly.** (1 connections) — `tests/compact/test_password.py`
- **TC-145: Empty password (user pressed Enter) returned as empty string.** (1 connections) — `tests/compact/test_password.py`
- **TC-145: Cursor is positioned at bottom of terminal before getpass.          This** (1 connections) — `tests/compact/test_password.py`
- **TC-145: Cursor positioning silently ignored on non-TTY environments.          If** (1 connections) — `tests/compact/test_password.py`

## Relationships

- [List Hosts Output Parser](List_Hosts_Output_Parser.md) (8 shared connections)
- [Pause Lingering Cleanup](Pause_Lingering_Cleanup.md) (2 shared connections)
- [Display Helper Class](Display_Helper_Class.md) (2 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [test_password.py](test_password.py.md) (1 shared connections)
- [Diagnostics Layer Tests](Diagnostics_Layer_Tests.md) (1 shared connections)

## Source Files

- `tests/compact/test_password.py`
- `tests/unit/test_event_source.py`

## Audit Trail

- EXTRACTED: 40 (56%)
- INFERRED: 31 (44%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*