# Play Definition Tree Population

> 256 nodes · cohesion 0.01

## Key Concepts

- **PlayDefinition** (333 connections) — `src/ansible_aom/core/models.py`
- **.from_run_state()** (187 connections) — `src/ansible_aom/core/tree.py`
- **TreeLine** (63 connections) — `src/ansible_aom/core/tree.py`
- **HostRow** (37 connections) — `src/ansible_aom/core/tree.py`
- **test_tree_projection.py** (27 connections) — `tests/unit/test_tree_projection.py`
- **TestHostRows** (23 connections) — `tests/unit/test_tree_projection.py`
- **TestPlayDefinition** (21 connections) — `tests/unit/test_models.py`
- **TestTaskCompletionLifecycle** (19 connections) — `tests/unit/test_tree_projection.py`
- **TestMultiPlayTruncationWithRoleFooters** (18 connections) — `tests/unit/test_tree_projection.py`
- **TestSubtreeRoleCounting** (18 connections) — `tests/unit/test_tree_projection.py`
- **TestRoleLabelsAfterTruncation** (16 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesBasic** (16 connections) — `tests/unit/test_tree_projection.py`
- **TestCrossPlayLookupIsolation** (15 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **TestDynamicChildrenAsPendingInTree** (15 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **TestMultiLevelInnerFooters** (15 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesPruning** (15 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesRolesAndFanOut** (15 connections) — `tests/unit/test_tree_projection.py`
- **TestTreePopulationFromDefinitions** (14 connections) — `tests/tui/test_live_refresh.py`
- **TestRuntimeRoleTaskCount** (14 connections) — `tests/unit/test_runtime_role_task_count.py`
- **TestStickyFallbackTreeRender** (14 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **TestIncludeStubHiding** (14 connections) — `tests/unit/test_tree_projection.py`
- **._many_tasks_state()** (14 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLineHasTailAfter** (14 connections) — `tests/unit/test_tree_projection.py`
- **TestVisibility** (14 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeKindIncludesMore** (13 connections) — `tests/unit/test_tree_projection.py`
- *... and 231 more nodes in this community*

## Relationships

- [[Task Definition Live Refresh]] (127 shared connections)
- [[Role Group Task Models]] (120 shared connections)
- [[Run State Summary Panel]] (111 shared connections)
- [[Run State Completion Recap]] (86 shared connections)
- [[Tree Projection Logic]] (39 shared connections)
- [[Compact Renderer Integration Tests]] (18 shared connections)
- [[Two-Cut Tree Truncation]] (17 shared connections)
- [[Tree Block Animation]] (16 shared connections)
- [[Ungrouped Role Tree Tests]] (15 shared connections)
- [[Include Role Discovery]] (13 shared connections)
- [[Preflight Summary Rendering]] (12 shared connections)
- [[Host Overview Table]] (12 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/tree.py`
- `tests/tui/test_live_refresh.py`
- `tests/unit/test_invariants_runstate_renderer.py`
- `tests/unit/test_loop_item_count.py`
- `tests/unit/test_models.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_runtime_role_task_count.py`
- `tests/unit/test_tree_classify_and_role_labels.py`
- `tests/unit/test_tree_meta_hostless.py`
- `tests/unit/test_tree_projection.py`

## Audit Trail

- EXTRACTED: 1137 (60%)
- INFERRED: 746 (40%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*