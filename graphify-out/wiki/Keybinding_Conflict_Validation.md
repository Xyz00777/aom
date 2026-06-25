# Keybinding Conflict Validation

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestKeybindingConflicts** (7 connections) — `tests/tui/test_keybindings.py`
- **validate_keybindings()** (3 connections) — `src/ansible_aom/tui/keybindings.py`
- **.test_multiple_keys_can_map_to_same_action()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_validate_keybindings_returns_no_errors()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_no_duplicate_keys_in_keybindings_dict()** (2 connections) — `tests/tui/test_keybindings.py`
- **Validate that there are no duplicate keybindings.      Returns:         List of** (1 connections) — `src/ansible_aom/tui/keybindings.py`
- **Tests for keybinding conflicts - no duplicate bindings.** (1 connections) — `tests/tui/test_keybindings.py`
- **The KEYBINDINGS dict should have no duplicate keys.** (1 connections) — `tests/tui/test_keybindings.py`
- **validate_keybindings should return empty list if valid.** (1 connections) — `tests/tui/test_keybindings.py`
- **Multiple keys can map to the same action (e.g., '/' and 'ctrl+f' for search).** (1 connections) — `tests/tui/test_keybindings.py`

## Relationships

- [[TUI Keybindings Config]] (3 shared connections)
- [[TUI Keybindings Tests]] (1 shared connections)
- [[Action Keybindings Lookup]] (1 shared connections)

## Source Files

- `src/ansible_aom/tui/keybindings.py`
- `tests/tui/test_keybindings.py`

## Audit Trail

- EXTRACTED: 18 (78%)
- INFERRED: 5 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*