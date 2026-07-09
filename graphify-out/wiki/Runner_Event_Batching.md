# Runner Event Batching

> 28 nodes · cohesion 0.10

## Key Concepts

- **get_keybinding()** (57 connections) — `src/ansible_aom/tui/keybindings.py`
- **TestGlobalKeybindings** (16 connections) — `tests/tui/test_keybindings.py`
- **.test_compact_view_toggle_is_global()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_cycle_theme_is_global()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_debug_panel_toggle_is_global()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_filter_panel_key_is_global()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_help_key_is_global()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_log_panel_toggle_is_global()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_quit_key_is_global()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_refresh_is_global()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_settings_key_is_global()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_shift_tab_reverse_panel_switch()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_sort_cycle_key_is_global()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_tab_switches_panel_globally()** (3 connections) — `tests/tui/test_keybindings.py`
- **Look up a keybinding by key string.      Args:         key: The key string to lo** (1 connections) — `src/ansible_aom/tui/keybindings.py`
- **Tests for global keybindings - TC-364.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-340, TC-364: 'q' key is global and requires confirmation.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-349: '?' key shows help overlay globally.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-353: 'f' key opens filter panel globally.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-350: 'S' key opens settings screen globally.** (1 connections) — `tests/tui/test_keybindings.py`
- **s' key cycles sort order globally.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-345: Tab switches panel focus globally.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-345: Shift+Tab reverses panel focus.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-348: 'd' key toggles debug panel globally.** (1 connections) — `tests/tui/test_keybindings.py`
- **TC-354: Alt+T cycles themes globally.** (1 connections) — `tests/tui/test_keybindings.py`
- *... and 3 more nodes in this community*

## Relationships

- [TUI Keybindings Tests](TUI_Keybindings_Tests.md) (9 shared connections)
- [CLI Help Matrix](CLI_Help_Matrix.md) (6 shared connections)
- [Warning Color Formatting](Warning_Color_Formatting.md) (5 shared connections)
- [Help Overlay TUI](Help_Overlay_TUI.md) (5 shared connections)
- [Include Tasks Dynamic Grafting](Include_Tasks_Dynamic_Grafting.md) (5 shared connections)
- [State Machine Invariants](State_Machine_Invariants.md) (4 shared connections)
- [Community 459](Community_459.md) (4 shared connections)
- [Community 509](Community_509.md) (3 shared connections)
- [Community 569](Community_569.md) (2 shared connections)
- [Community 568](Community_568.md) (2 shared connections)
- [Community 567](Community_567.md) (2 shared connections)

## Source Files

- `src/ansible_aom/tui/keybindings.py`
- `tests/tui/test_keybindings.py`

## Audit Trail

- EXTRACTED: 55 (45%)
- INFERRED: 68 (55%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*