# Task Definition Live Refresh

> 189 nodes · cohesion 0.02

## Key Concepts

- **TaskDefinition** (383 connections) — `src/ansible_aom/core/models.py`
- **TaskTree** (54 connections) — `src/ansible_aom/tui/widgets/task_tree.py`
- **TestTaskDefinition** (25 connections) — `tests/unit/test_models.py`
- **TestRoleGroupCreationThreshold** (18 connections) — `tests/tui/test_tree_view.py`
- **TestPopulateFromProjectionFooters** (17 connections) — `tests/tui/test_tree_more_footers.py`
- **TestMainScreenTreeIntegration** (16 connections) — `tests/tui/test_live_refresh.py`
- **TestTaskMatchingAlgorithm** (16 connections) — `tests/unit/test_event_processing.py`
- **TestTaskMatching** (16 connections) — `tests/unit/test_models.py`
- **TestPeriodicRefresh** (15 connections) — `tests/tui/test_live_refresh.py`
- **TestApplyStateIcons** (14 connections) — `tests/tui/test_live_refresh.py`
- **TestCompletionTitleUpdate** (14 connections) — `tests/tui/test_live_refresh.py`
- **TestCallFromThreadRouting** (13 connections) — `tests/tui/test_live_refresh.py`
- **TestEndToEndThreeTasks** (13 connections) — `tests/tui/test_live_refresh.py`
- **_two_level_state()** (13 connections) — `tests/tui/test_tree_more_footers.py`
- **TestTreeViewWidgetIntegration** (13 connections) — `tests/tui/test_tree_view.py`
- **test_tree_nested_roles.py** (13 connections) — `tests/unit/test_tree_nested_roles.py`
- **_play_def()** (11 connections) — `tests/unit/test_tree_nested_roles.py`
- **_fire_startup()** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **TestArbitraryDepthRendersCorrectly** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **TestFlatRoleTasksUnchanged** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **TestMixedConsecutiveAndNestedRoles** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **.test_mixed_consecutive_and_nested_roles()** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **TestNestedRoleRendersAsSubBranch** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **.test_nested_role_renders_as_sub_branch()** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **TestPreflightDuplicateRoleHeaderBug** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- *... and 164 more nodes in this community*

## Relationships

- [[Play Definition Tree Population]] (127 shared connections)
- [[Role Group Task Models]] (107 shared connections)
- [[Run State Completion Recap]] (67 shared connections)
- [[Run State Summary Panel]] (65 shared connections)
- [[Include Role Discovery]] (18 shared connections)
- [[Compact Renderer Integration Tests]] (18 shared connections)
- [[TUI Tree View Tests]] (18 shared connections)
- [[Data Model Unit Tests]] (13 shared connections)
- [[Tree Projection Logic]] (12 shared connections)
- [[Ungrouped Role Tree Tests]] (12 shared connections)
- [[Dynamic Include Expansion]] (11 shared connections)
- [[AOM TUI Application]] (10 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/tui/widgets/task_tree.py`
- `tests/tui/test_live_refresh.py`
- `tests/tui/test_tree_more_footers.py`
- `tests/tui/test_tree_view.py`
- `tests/unit/test_event_processing.py`
- `tests/unit/test_models.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_tree_nested_roles.py`

## Audit Trail

- EXTRACTED: 522 (45%)
- INFERRED: 638 (55%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*