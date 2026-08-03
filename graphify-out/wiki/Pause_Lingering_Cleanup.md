# Pause Lingering Cleanup

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestTUIModePasswordMasking** (8 connections) — `tests/compact/test_password.py`
- **.test_compact_password_uses_getpass_which_masks()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_masking_all_prompt_types()** (3 connections) — `tests/compact/test_password.py`
- **.test_tui_password_input_documented_for_modal_migration()** (3 connections) — `tests/compact/test_password.py`
- **.test_tui_password_masking_via_getpass_not_visible()** (2 connections) — `tests/compact/test_password.py`
- **.test_tui_password_uses_getpass_which_masks()** (2 connections) — `tests/compact/test_password.py`
- **TC-147: Verify Input(password=True) used for masking.      The TUI mode currentl** (1 connections) — `tests/compact/test_password.py`
- **TC-147: TUI mode uses getpass which provides password masking (no echo).** (1 connections) — `tests/compact/test_password.py`
- **TC-147: Password entered via getpass is not echoed to terminal.** (1 connections) — `tests/compact/test_password.py`
- **TC-147: Compact mode also uses getpass which provides password masking.** (1 connections) — `tests/compact/test_password.py`
- **TC-147: All password prompt types use masking (via getpass).** (1 connections) — `tests/compact/test_password.py`
- **TC-147: Document that TUI mode should eventually use Input(password=True).** (1 connections) — `tests/compact/test_password.py`

## Relationships

- [Status Bar Liveness Tests](Status_Bar_Liveness_Tests.md) (2 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [test_password.py](test_password.py.md) (1 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)

## Source Files

- `tests/compact/test_password.py`

## Audit Trail

- EXTRACTED: 23 (85%)
- INFERRED: 4 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*