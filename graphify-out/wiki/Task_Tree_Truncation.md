# Task Tree Truncation

> 14 nodes · cohesion 0.15

## Key Concepts

- **truncate_name()** (6 connections) — `src/ansible_aom/tui/widgets/task_tree.py`
- **task_tree.py** (4 connections) — `src/ansible_aom/tui/widgets/task_tree.py`
- **compact_truncate()** (4 connections) — `src/ansible_aom/tui/widgets/task_tree.py`
- **.test_compact_mode_truncates_at_width_minus_20()** (3 connections) — `tests/tui/test_tree_view.py`
- **.test_truncation_exact_width()** (3 connections) — `tests/tui/test_tree_view.py`
- **.test_truncation_long_name_with_ellipsis()** (3 connections) — `tests/tui/test_tree_view.py`
- **.test_truncation_minimum_10_visible_chars()** (3 connections) — `tests/tui/test_tree_view.py`
- **TC-270: Long task names are truncated with ellipsis.** (1 connections) — `tests/tui/test_tree_view.py`
- **TC-270: Minimum 10 visible characters before ellipsis.** (1 connections) — `tests/tui/test_tree_view.py`
- **TC-270 edge case: Name exactly at width boundary.** (1 connections) — `tests/tui/test_tree_view.py`
- **TC-272: Compact mode hard-truncates at terminal width minus 20 chars.** (1 connections) — `tests/tui/test_tree_view.py`
- **Task tree widget for AOM TUI.  Tree view showing Play/RoleGroup/Task/Host hierar** (1 connections) — `src/ansible_aom/tui/widgets/task_tree.py`
- **Truncate name with ellipsis if too long.      Args:         name: The name to tr** (1 connections) — `src/ansible_aom/tui/widgets/task_tree.py`
- **Truncate for compact mode, leaving space for icons.      Args:         name: The** (1 connections) — `src/ansible_aom/tui/widgets/task_tree.py`

## Relationships

- [[TUI Tree View Tests]] (4 shared connections)
- [[Task Definition Live Refresh]] (1 shared connections)

## Source Files

- `src/ansible_aom/tui/widgets/task_tree.py`
- `tests/tui/test_tree_view.py`

## Audit Trail

- EXTRACTED: 25 (76%)
- INFERRED: 8 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*