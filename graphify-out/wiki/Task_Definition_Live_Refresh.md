# Task Definition Live Refresh

> 137 nodes · cohesion 0.02

## Key Concepts

- **TaskDefinition** (389 connections) — `src/ansible_aom/core/models.py`
- **TaskTree** (40 connections) — `src/ansible_aom/tui/widgets/task_tree.py`
- **TestTaskDefinition** (24 connections) — `tests/unit/test_models.py`
- **TestTaskMatchingAlgorithm** (16 connections) — `tests/unit/test_event_processing.py`
- **TestMainScreenTreeIntegration** (15 connections) — `tests/tui/test_live_refresh.py`
- **TestTaskMatching** (15 connections) — `tests/unit/test_models.py`
- **TestPeriodicRefresh** (14 connections) — `tests/tui/test_live_refresh.py`
- **TestPopulateFromProjectionFooters** (14 connections) — `tests/tui/test_tree_more_footers.py`
- **TestApplyStateIcons** (13 connections) — `tests/tui/test_live_refresh.py`
- **TestCompletionTitleUpdate** (13 connections) — `tests/tui/test_live_refresh.py`
- **_two_level_state()** (13 connections) — `tests/tui/test_tree_more_footers.py`
- **test_tree_nested_roles.py** (13 connections) — `tests/unit/test_tree_nested_roles.py`
- **TestCallFromThreadRouting** (12 connections) — `tests/tui/test_live_refresh.py`
- **TestEndToEndThreeTasks** (12 connections) — `tests/tui/test_live_refresh.py`
- **_play_def()** (11 connections) — `tests/unit/test_tree_nested_roles.py`
- **_fire_startup()** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **.test_mixed_consecutive_and_nested_roles()** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **.test_nested_role_renders_as_sub_branch()** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **.test_runtime_podman_prefix_does_not_duplicate_role_header()** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **test_live_refresh.py** (9 connections) — `tests/tui/test_live_refresh.py`
- **_line_summary()** (9 connections) — `tests/unit/test_tree_nested_roles.py`
- **.test_regression_flat_role_tasks_unchanged()** (9 connections) — `tests/unit/test_tree_nested_roles.py`
- **.test_apply_state_icons_updates_host_icon()** (8 connections) — `tests/tui/test_live_refresh.py`
- **.test_apply_state_icons_updates_task_icon()** (8 connections) — `tests/tui/test_live_refresh.py`
- **_fire_running_task()** (8 connections) — `tests/unit/test_tree_nested_roles.py`
- *... and 112 more nodes in this community*

## Relationships

- [[Play Definition Tree Population]] (111 shared connections)
- [[Role Group Task Models]] (100 shared connections)
- [[Run State Completion Recap]] (52 shared connections)
- [[Run State Summary Panel]] (30 shared connections)
- [[Include Role Discovery]] (18 shared connections)
- [[Compact Renderer Integration Tests]] (18 shared connections)
- [[Data Model Unit Tests]] (13 shared connections)
- [[Ungrouped Role Tree Tests]] (12 shared connections)
- [[Dynamic Include Expansion]] (11 shared connections)
- [[AOM TUI Application]] (10 shared connections)
- [[Total Task Counting]] (6 shared connections)
- [[Main TUI Screen]] (6 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/tui/widgets/task_tree.py`
- `tests/tui/test_live_refresh.py`
- `tests/tui/test_tree_more_footers.py`
- `tests/unit/test_event_processing.py`
- `tests/unit/test_models.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_tree_nested_roles.py`

## Audit Trail

- EXTRACTED: 454 (44%)
- INFERRED: 573 (56%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*