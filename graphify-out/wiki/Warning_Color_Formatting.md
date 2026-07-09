# Warning Color Formatting

> 14 nodes · cohesion 0.14

## Key Concepts

- **test_keybindings.py** (19 connections) — `tests/tui/test_keybindings.py`
- **TestCtrlCKeybindings** (6 connections) — `tests/tui/test_keybindings.py`
- **TestPostRunKeybindings** (6 connections) — `tests/tui/test_keybindings.py`
- **.test_ctrl_c_is_interrupt_action()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_ctrl_c_no_confirmation()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_capital_r_rerun_with_same_args()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_shift_r_rerun_with_modified_args()** (3 connections) — `tests/tui/test_keybindings.py`
- **Unit tests for TUI keybindings (Section 10 of TEST_SPECIFICATION.md).  Test case** (1 connections) — `tests/tui/test_keybindings.py`
- **Tests for Ctrl+C keybindings - TC-341, TC-342.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-341: Ctrl+C forwards interrupt to subprocess.** (1 connections) — `tests/tui/test_keybindings.py`
- **Ctrl+C does not require confirmation.** (1 connections) — `tests/tui/test_keybindings.py`
- **Tests for post-run keybindings - TC-351, TC-352, TC-363.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-351: 'R' re-runs playbook with same args (post-run).** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-352: Shift+R opens dialog to modify args before re-run.** (1 connections) — `tests/tui/test_keybindings.py`

## Relationships

- [State Machine Invariants](State_Machine_Invariants.md) (5 shared connections)
- [Runner Event Batching](Runner_Event_Batching.md) (5 shared connections)
- [Status Icon Mapping](Status_Icon_Mapping.md) (1 shared connections)
- [Process Liveness Monitoring](Process_Liveness_Monitoring.md) (1 shared connections)
- [Help Overlay TUI](Help_Overlay_TUI.md) (1 shared connections)
- [Community 569](Community_569.md) (1 shared connections)
- [Community 458](Community_458.md) (1 shared connections)
- [Module Init File](Module_Init_File.md) (1 shared connections)
- [Community 459](Community_459.md) (1 shared connections)
- [Rerun Command Integration](Rerun_Command_Integration.md) (1 shared connections)
- [Community 568](Community_568.md) (1 shared connections)
- [Include Tasks Dynamic Grafting](Include_Tasks_Dynamic_Grafting.md) (1 shared connections)

## Source Files

- `tests/tui/test_keybindings.py`

## Audit Trail

- EXTRACTED: 42 (84%)
- INFERRED: 8 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*