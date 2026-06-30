# TUI Keybindings Config

> 20 nodes · cohesion 0.14

## Key Concepts

- **KeyContext** (26 connections) — `src/ansible_aom/tui/keybindings.py`
- **KeyAction** (23 connections) — `src/ansible_aom/tui/keybindings.py`
- **keybindings.py** (9 connections) — `src/ansible_aom/tui/keybindings.py`
- **get_keybindings_by_context()** (8 connections) — `src/ansible_aom/tui/keybindings.py`
- **TestGetKeybindingsByContext** (8 connections) — `tests/tui/test_keybindings.py`
- **.test_get_global_keybindings()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_get_log_keybindings()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_get_post_run_keybindings()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_get_tree_keybindings()** (3 connections) — `tests/tui/test_keybindings.py`
- **str** (1 connections)
- **Keybindings configuration for AOM TUI.  This module defines all keyboard shortcu** (1 connections) — `src/ansible_aom/tui/keybindings.py`
- **Context where a keybinding is active.** (1 connections) — `src/ansible_aom/tui/keybindings.py`
- **Definition of a keybinding action.** (1 connections) — `src/ansible_aom/tui/keybindings.py`
- **Get all keybindings for a specific context.      Args:         context: The cont** (1 connections) — `src/ansible_aom/tui/keybindings.py`
- **Tests for get_keybindings_by_context function.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_keybindings_by_context filters by GLOBAL context.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_keybindings_by_context filters by TREE context.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_keybindings_by_context filters by LOG context.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_keybindings_by_context filters by POST_RUN context.** (1 connections) — `tests/tui/test_keybindings.py`
- **TypedDict** (1 connections)

## Relationships

- [[TUI Keybindings Tests]] (5 shared connections)
- [[Global Key Bindings]] (4 shared connections)
- [[Action Keybindings Lookup]] (3 shared connections)
- [[Get All Actions]] (3 shared connections)
- [[Keybinding Conflict Validation]] (3 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Ctrl-C Keybindings]] (2 shared connections)
- [[Get Keybinding Function]] (2 shared connections)
- [[Invalid Key Handling]] (2 shared connections)
- [[KeyAction TypedDict]] (2 shared connections)
- [[Keybinding Context Coverage]] (2 shared connections)
- [[KeyContext Enum]] (2 shared connections)

## Source Files

- `src/ansible_aom/tui/keybindings.py`
- `tests/tui/test_keybindings.py`

## Audit Trail

- EXTRACTED: 48 (49%)
- INFERRED: 49 (51%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*