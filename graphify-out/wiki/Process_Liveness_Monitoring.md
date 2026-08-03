# Process Liveness Monitoring

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestGetAllActions** (6 connections) — `tests/tui/test_keybindings.py`
- **.test_get_all_actions_contains_known_actions()** (2 connections) — `tests/tui/test_keybindings.py`
- **.test_get_all_actions_count_matches_bindings()** (2 connections) — `tests/tui/test_keybindings.py`
- **.test_get_all_actions_excludes_unknown()** (2 connections) — `tests/tui/test_keybindings.py`
- **.test_get_all_actions_returns_set()** (2 connections) — `tests/tui/test_keybindings.py`
- **Tests for get_all_actions function.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_all_actions returns a set.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_all_actions contains expected actions.** (1 connections) — `tests/tui/test_keybindings.py`
- **get_all_actions should not contain invalid actions.** (1 connections) — `tests/tui/test_keybindings.py`
- **Number of unique actions should match or be less than bindings.** (1 connections) — `tests/tui/test_keybindings.py`

## Relationships

- [test_keybindings.py](test_keybindings.py.md) (1 shared connections)

## Source Files

- `tests/tui/test_keybindings.py`

## Audit Trail

- EXTRACTED: 19 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*