# Process Liveness Monitoring

> 12 nodes · cohesion 0.21

## Key Concepts

- **TestGetAllActions** (8 connections) — `tests/tui/test_keybindings.py`
- **get_all_actions()** (6 connections) — `src/ansible_aom/tui/keybindings.py`
- **.test_get_all_actions_contains_known_actions()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_get_all_actions_count_matches_bindings()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_get_all_actions_excludes_unknown()** (3 connections) — `tests/tui/test_keybindings.py`
- **.test_get_all_actions_returns_set()** (3 connections) — `tests/tui/test_keybindings.py`
- **Get all unique action names defined in keybindings.      Returns:         Set of** (1 connections) — `src/ansible_aom/tui/keybindings.py`
- **Tests for get_all_actions function.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_all_actions returns a set.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_all_actions contains expected actions.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_all_actions should not contain invalid actions.** (1 connections) — `tests/tui/test_keybindings.py`
- **Number of unique actions should match or be less than bindings.** (1 connections) — `tests/tui/test_keybindings.py`

## Relationships

- [State Machine Invariants](State_Machine_Invariants.md) (3 shared connections)
- [Warning Color Formatting](Warning_Color_Formatting.md) (1 shared connections)

## Source Files

- `src/ansible_aom/tui/keybindings.py`
- `tests/tui/test_keybindings.py`

## Audit Trail

- EXTRACTED: 22 (69%)
- INFERRED: 10 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*