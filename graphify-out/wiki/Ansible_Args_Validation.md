# Ansible Args Validation

> 14 nodes · cohesion 0.15

## Key Concepts

- **TestTreeIcons** (7 connections) — `tests/unit/test_icons.py`
- **get_tree_icon()** (4 connections) — `src/ansible_aom/core/icons.py`
- **.test_get_tree_icon_collapsed()** (3 connections) — `tests/unit/test_icons.py`
- **.test_get_tree_icon_expanded()** (3 connections) — `tests/unit/test_icons.py`
- **.test_tree_collapsed_icon()** (2 connections) — `tests/unit/test_icons.py`
- **.test_tree_expanded_icon()** (2 connections) — `tests/unit/test_icons.py`
- **.test_tree_icons_are_unicode()** (2 connections) — `tests/unit/test_icons.py`
- **Get tree expansion icon.      Args:         expanded: True for expanded node (▼)** (1 connections) — `src/ansible_aom/core/icons.py`
- **Tests for TC-373 and TC-374.** (1 connections) — `tests/unit/test_icons.py`
- **TC-373: Collapsed tree node displays right arrow (▶).** (1 connections) — `tests/unit/test_icons.py`
- **TC-374: Expanded tree node displays down arrow (▼).** (1 connections) — `tests/unit/test_icons.py`
- **TC-373: get_tree_icon returns correct icon for collapsed node.** (1 connections) — `tests/unit/test_icons.py`
- **TC-374: get_tree_icon returns correct icon for expanded node.** (1 connections) — `tests/unit/test_icons.py`
- **Tree icons are valid Unicode characters.** (1 connections) — `tests/unit/test_icons.py`

## Relationships

- [Session List View](Session_List_View.md) (1 shared connections)
- [test_icons.py](test_icons.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/icons.py`
- `tests/unit/test_icons.py`

## Audit Trail

- EXTRACTED: 26 (87%)
- INFERRED: 4 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*