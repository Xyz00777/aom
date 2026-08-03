# View Mode Selection

> 14 nodes · cohesion 0.14

## Key Concepts

- **TestTUIModePasswordModal** (9 connections) — `tests/compact/test_password.py`
- **.test_tui_handle_password_prompt_blocks_until_complete()** (2 connections) — `tests/compact/test_password.py`
- **.test_tui_handle_password_prompt_passes_prompt_with_suffix()** (2 connections) — `tests/compact/test_password.py`
- **.test_tui_handle_password_prompt_returns_empty_on_eof()** (2 connections) — `tests/compact/test_password.py`
- **.test_tui_handle_password_prompt_returns_empty_on_keyboard_interrupt()** (2 connections) — `tests/compact/test_password.py`
- **.test_tui_handle_password_prompt_returns_password()** (2 connections) — `tests/compact/test_password.py`
- **.test_tui_handle_password_prompt_uses_suspend()** (2 connections) — `tests/compact/test_password.py`
- **TC-146: Verify call_from_thread triggers Textual modal, worker blocked.      In** (1 connections) — `tests/compact/test_password.py`
- **TC-146: TUI mode uses app.suspend() context manager for password input.** (1 connections) — `tests/compact/test_password.py`
- **TC-146: TUI mode appends ': ' to prompt when showing to user.** (1 connections) — `tests/compact/test_password.py`
- **TC-146: TUI mode returns the password entered by user.** (1 connections) — `tests/compact/test_password.py`
- **TC-146: TUI mode returns empty string on EOFError (user cancelled).** (1 connections) — `tests/compact/test_password.py`
- **TC-146: TUI mode returns empty string on KeyboardInterrupt.** (1 connections) — `tests/compact/test_password.py`
- **TC-146: handle_password_prompt is synchronous — blocks caller until complete.** (1 connections) — `tests/compact/test_password.py`

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [test_password.py](test_password.py.md) (1 shared connections)

## Source Files

- `tests/compact/test_password.py`

## Audit Trail

- EXTRACTED: 27 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*