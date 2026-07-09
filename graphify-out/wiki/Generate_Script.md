# Generate Script

> 10 nodes · cohesion 0.20

## Key Concepts

- **QuitConfirmScreen** (7 connections) — `src/ansible_aom/tui/screens/quit_confirm.py`
- **.action_quit()** (3 connections) — `src/ansible_aom/tui/app.py`
- **.compose()** (3 connections) — `src/ansible_aom/tui/screens/quit_confirm.py`
- **quit_confirm.py** (2 connections) — `src/ansible_aom/tui/screens/quit_confirm.py`
- **Quit with confirmation per SPECIFICATION.md Section 10.          Shows confirmat** (1 connections) — `src/ansible_aom/tui/app.py`
- **ComposeResult** (1 connections)
- **.action_cancel()** (1 connections) — `src/ansible_aom/tui/screens/quit_confirm.py`
- **.action_confirm()** (1 connections) — `src/ansible_aom/tui/screens/quit_confirm.py`
- **Quit confirmation dialog for AOM TUI.  Triggered by 'q' key when a playbook is r** (1 connections) — `src/ansible_aom/tui/screens/quit_confirm.py`
- **Modal dialog confirming quit action.      Returns:         True: User confirmed** (1 connections) — `src/ansible_aom/tui/screens/quit_confirm.py`

## Relationships

- [Session Recording Tests](Session_Recording_Tests.md) (2 shared connections)
- [Data Model Unit Tests](Data_Model_Unit_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/tui/app.py`
- `src/ansible_aom/tui/screens/quit_confirm.py`

## Audit Trail

- EXTRACTED: 17 (81%)
- INFERRED: 4 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*