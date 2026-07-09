# Pause Lingering Cleanup

> 14 nodes · cohesion 0.14

## Key Concepts

- **TestTUIModePasswordMasking** (9 connections) — `tests/compact/test_password.py`
- **test_password.py** (7 connections) — `tests/compact/test_password.py`
- **.test_compact_password_uses_getpass_which_masks()** (3 connections) — `tests/compact/test_password.py`
- **.test_password_masking_all_prompt_types()** (3 connections) — `tests/compact/test_password.py`
- **.test_tui_password_input_documented_for_modal_migration()** (3 connections) — `tests/compact/test_password.py`
- **.test_tui_password_masking_via_getpass_not_visible()** (3 connections) — `tests/compact/test_password.py`
- **.test_tui_password_uses_getpass_which_masks()** (3 connections) — `tests/compact/test_password.py`
- **Tests for password prompt handling — TC-143 through TC-148.  Covers: - TC-143: P** (1 connections) — `tests/compact/test_password.py`
- **TC-147: Verify Input(password=True) used for masking.      The TUI mode currentl** (1 connections) — `tests/compact/test_password.py`
- **TC-147: TUI mode uses getpass which provides password masking (no echo).** (1 connections) — `tests/compact/test_password.py`
- **TC-147: Password entered via getpass is not echoed to terminal.** (1 connections) — `tests/compact/test_password.py`
- **TC-147: Compact mode also uses getpass which provides password masking.** (1 connections) — `tests/compact/test_password.py`
- **TC-147: All password prompt types use masking (via getpass).** (1 connections) — `tests/compact/test_password.py`
- **TC-147: Document that TUI mode should eventually use Input(password=True).** (1 connections) — `tests/compact/test_password.py`

## Relationships

- [Status Bar Liveness Tests](Status_Bar_Liveness_Tests.md) (3 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (3 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (2 shared connections)
- [Golden Frame Tests](Golden_Frame_Tests.md) (1 shared connections)
- [Display Helper Class](Display_Helper_Class.md) (1 shared connections)
- [View Mode Selection](View_Mode_Selection.md) (1 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)

## Source Files

- `tests/compact/test_password.py`

## Audit Trail

- EXTRACTED: 31 (82%)
- INFERRED: 7 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*