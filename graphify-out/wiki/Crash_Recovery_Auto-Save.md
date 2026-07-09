# Crash Recovery Auto-Save

> 20 nodes · cohesion 0.13

## Key Concepts

- **._body()** (10 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **.compose()** (7 connections) — `src/ansible_aom/tui/screens/help.py`
- **._host_breakdown()** (7 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **._command_panel()** (5 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **_build_shortcuts_section()** (4 connections) — `src/ansible_aom/tui/screens/help.py`
- **Text** (4 connections)
- **.compose()** (4 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **._session_header()** (4 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **Panel** (3 connections)
- **help.py** (3 connections) — `src/ansible_aom/tui/screens/help.py`
- **Group** (2 connections)
- **Text** (2 connections)
- **ComposeResult** (1 connections)
- **Help overlay for AOM TUI.  Triggered by '?' key. See SPECIFICATION.md Section 10** (1 connections) — `src/ansible_aom/tui/screens/help.py`
- **Render the keybindings section as a Rich Text.      Each context gets a bold hea** (1 connections) — `src/ansible_aom/tui/screens/help.py`
- **ComposeResult** (1 connections)
- **First section: identify which session this rerun targets.** (1 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **Second section: failed / unreachable / changed host groups.** (1 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **Third section: the exact ansible-playbook invocation.** (1 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **Compose all sections into a single Rich renderable.** (1 connections) — `src/ansible_aom/tui/screens/rerun.py`

## Relationships

- [Session Replay Round Trip](Session_Replay_Round_Trip.md) (5 shared connections)
- [Dynamic Include Expansion](Dynamic_Include_Expansion.md) (3 shared connections)
- [Inventory Auto Detection](Inventory_Auto_Detection.md) (2 shared connections)
- [Data Model Unit Tests](Data_Model_Unit_Tests.md) (2 shared connections)
- [Shell Completion Helpers](Shell_Completion_Helpers.md) (1 shared connections)

## Source Files

- `src/ansible_aom/tui/screens/help.py`
- `src/ansible_aom/tui/screens/rerun.py`

## Audit Trail

- EXTRACTED: 53 (84%)
- INFERRED: 10 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*