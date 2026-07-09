# Inventory Auto Detection

> 33 nodes · cohesion 0.09

## Key Concepts

- **HelpOverlay** (20 connections) — `src/ansible_aom/tui/screens/help.py`
- **TestHelpOverlayContent** (10 connections) — `tests/tui/test_help_screen.py`
- **test_help_screen.py** (8 connections) — `tests/tui/test_help_screen.py`
- **_render_overlay_text()** (8 connections) — `tests/tui/test_help_screen.py`
- **TestHelpOverlayBindings** (7 connections) — `tests/tui/test_help_screen.py`
- **TestHelpOverlayStructure** (6 connections) — `tests/tui/test_help_screen.py`
- **TestHelpOverlayDismissAction** (5 connections) — `tests/tui/test_help_screen.py`
- **TestHelpOverlayLineCount** (5 connections) — `tests/tui/test_help_screen.py`
- **.test_includes_all_keybinding_contexts()** (4 connections) — `tests/tui/test_help_screen.py`
- **.test_includes_command_reference_section()** (4 connections) — `tests/tui/test_help_screen.py`
- **.test_includes_help_shortcut()** (4 connections) — `tests/tui/test_help_screen.py`
- **.test_includes_navigation_section()** (4 connections) — `tests/tui/test_help_screen.py`
- **.test_includes_quit_shortcut()** (4 connections) — `tests/tui/test_help_screen.py`
- **.test_lists_keyboard_shortcuts()** (4 connections) — `tests/tui/test_help_screen.py`
- **.action_show_help()** (3 connections) — `src/ansible_aom/tui/app.py`
- **.test_dismiss_via_escape_key()** (3 connections) — `tests/tui/test_help_screen.py`
- **.action_dismiss()** (2 connections) — `src/ansible_aom/tui/screens/help.py`
- **.test_help_overlay_is_modal_screen()** (2 connections) — `tests/tui/test_help_screen.py`
- **Push the help overlay on top of whatever screen is active.** (1 connections) — `src/ansible_aom/tui/app.py`
- **Any** (1 connections)
- **Help overlay showing keybindings, commands, and navigation.      Closes on Escap** (1 connections) — `src/ansible_aom/tui/screens/help.py`
- **Unit tests for the TUI help overlay screen.  Tests cover the L2 help.py expansio** (1 connections) — `tests/tui/test_help_screen.py`
- **The dismiss action must close the screen without returning a value.** (1 connections) — `tests/tui/test_help_screen.py`
- **The expansion must be substantive — not a one-paragraph stub.** (1 connections) — `tests/tui/test_help_screen.py`
- **Structural assertions about the HelpOverlay screen.** (1 connections) — `tests/tui/test_help_screen.py`
- *... and 8 more nodes in this community*

## Relationships

- [Session Recording Tests](Session_Recording_Tests.md) (14 shared connections)
- [Crash Recovery Auto-Save](Crash_Recovery_Auto-Save.md) (2 shared connections)
- [State Machine Invariants](State_Machine_Invariants.md) (1 shared connections)
- [Frame Parameter Handling](Frame_Parameter_Handling.md) (1 shared connections)

## Source Files

- `src/ansible_aom/tui/app.py`
- `src/ansible_aom/tui/screens/help.py`
- `tests/tui/test_help_screen.py`

## Audit Trail

- EXTRACTED: 76 (64%)
- INFERRED: 42 (36%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*