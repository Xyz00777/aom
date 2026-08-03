# TaskDefinition

> 203 nodes · cohesion 0.02

## Key Concepts

- **TaskDefinition** (357 connections) — `src/ansible_aom/core/models.py`
- **RoleGroupDefinition** (152 connections) — `src/ansible_aom/core/models.py`
- **TestTaskDefinition** (24 connections) — `tests/unit/test_models.py`
- **test_models.py** (18 connections) — `tests/unit/test_models.py`
- **TestRoleGroupDefinition** (18 connections) — `tests/unit/test_models.py`
- **TestMemoryBounds** (17 connections) — `tests/unit/test_models.py`
- **TestTaskMatchingAlgorithm** (16 connections) — `tests/unit/test_event_processing.py`
- **TestDefinitionVsStateSeparation** (15 connections) — `tests/unit/test_models.py`
- **TestLinearForceCompletion** (15 connections) — `tests/unit/test_models.py`
- **TestTaskMatching** (15 connections) — `tests/unit/test_models.py`
- **TestRunnerTaskCompletionPromotion** (14 connections) — `tests/unit/test_models.py`
- **test_tree_nested_roles.py** (14 connections) — `tests/unit/test_tree_nested_roles.py`
- **HostRow** (13 connections) — `src/ansible_aom/core/tree_projection.py`
- **TestFreeStrategyMetaTaskVisibility** (12 connections) — `tests/unit/test_models.py`
- **_iter_leaf_task_defs()** (10 connections) — `src/ansible_aom/core/run_state.py`
- **_play_def()** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **.test_mixed_consecutive_and_nested_roles()** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **.test_nested_role_renders_as_sub_branch()** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **.test_runtime_podman_prefix_does_not_duplicate_role_header()** (10 connections) — `tests/unit/test_tree_nested_roles.py`
- **TestIncludeStubHiding** (10 connections) — `tests/unit/test_tree_projection.py`
- **_fire_startup()** (9 connections) — `tests/unit/test_tree_nested_roles.py`
- **_line_summary()** (9 connections) — `tests/unit/test_tree_nested_roles.py`
- **.test_regression_flat_role_tasks_unchanged()** (9 connections) — `tests/unit/test_tree_nested_roles.py`
- **TestTreeKindIncludesMore** (9 connections) — `tests/unit/test_tree_projection.py`
- **.test_arbitrary_depth_renders_correctly()** (8 connections) — `tests/unit/test_tree_nested_roles.py`
- *... and 178 more nodes in this community*

## Relationships

- [HostRunState](HostRunState.md) (105 shared connections)
- [PlayDefinition](PlayDefinition.md) (104 shared connections)
- [.from_run_state](from_run_state.md) (79 shared connections)
- [RunState](RunState.md) (65 shared connections)
- [WarningType](WarningType.md) (29 shared connections)
- [TestCrossPlayLookupIsolation](TestCrossPlayLookupIsolation.md) (25 shared connections)
- [TestUngroupedRoleTasksInTree](TestUngroupedRoleTasksInTree.md) (15 shared connections)
- [TestRoleGrouping](TestRoleGrouping.md) (13 shared connections)
- [IncludeCacheEntry](IncludeCacheEntry.md) (12 shared connections)
- [WarningEntry](WarningEntry.md) (11 shared connections)
- [json.py](json.py.md) (10 shared connections)
- [TreeProjection](TreeProjection.md) (8 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/core/includes.py`
- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/run_state.py`
- `src/ansible_aom/core/tree_projection.py`
- `tests/unit/test_event_processing.py`
- `tests/unit/test_invariants_runstate_renderer.py`
- `tests/unit/test_models.py`
- `tests/unit/test_tree_nested_roles.py`
- `tests/unit/test_tree_projection.py`

## Audit Trail

- EXTRACTED: 859 (65%)
- INFERRED: 454 (35%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*