# Run Diagnostics Tests

> 33 nodes · cohesion 0.08

## Key Concepts

- **TestUngroupedRoleTasksInTree** (12 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **_play_def()** (11 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **TestRolePrefixStripping** (10 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **TestPendingPlayUngroupedRoles** (8 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **._state_with_ungrouped_role_running()** (8 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **.test_pending_play_shows_ungrouped_role_header()** (6 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **.test_runtime_play_counts_ungrouped_role_tasks_in_label()** (6 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **.test_host_leaf_under_prefixed_runtime_task()** (6 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **.test_no_duplicate_tasks_with_prefixed_runtime_names()** (6 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **.test_runtime_prefixed_task_under_role_header()** (6 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **.test_task_role_with_prefixed_name()** (6 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **.test_task_role_indexes_ungrouped_tasks()** (6 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **.test_ungrouped_role_label_shows_task_count()** (6 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **test_tree_ungrouped_roles.py** (5 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **.test_host_leaf_visible_under_ungrouped_role()** (4 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **.test_running_task_prioritized_over_pending()** (4 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **.test_ungrouped_role_appears_under_role_header()** (4 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **Regression tests for ungrouped role tasks in the tree view.  Ungrouped role task** (1 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **Role label for ungrouped role must show the total task count         from defini** (1 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **_task_role must return the role for ungrouped TaskDefinition entries,         no** (1 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **When a running task is at the end of the definition list,         the stable par** (1 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **Host leaf must appear under the running task within an         ungrouped role, e** (1 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **Pending plays must also show ungrouped role tasks under role headers.** (1 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **A pending play with bare TaskDefinition entries that have role         set must** (1 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- **Runtime play role labels must count ungrouped role tasks from         definition** (1 connections) — `tests/unit/test_tree_ungrouped_roles.py`
- *... and 8 more nodes in this community*

## Relationships

- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (12 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (11 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (9 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (4 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (3 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (3 shared connections)

## Source Files

- `tests/unit/test_tree_ungrouped_roles.py`

## Audit Trail

- EXTRACTED: 109 (84%)
- INFERRED: 21 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*