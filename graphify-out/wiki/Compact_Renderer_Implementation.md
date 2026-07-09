# Compact Renderer Implementation

> 147 nodes · cohesion 0.02

## Key Concepts

- **TaskDefinition** (393 connections) — `src/ansible_aom/core/models.py`
- **TestTaskDefinition** (24 connections) — `tests/unit/test_models.py`
- **test_models.py** (17 connections) — `tests/unit/test_models.py`
- **TestTaskMatchingAlgorithm** (16 connections) — `tests/unit/test_event_processing.py`
- **TestDefinitionVsStateSeparation** (15 connections) — `tests/unit/test_models.py`
- **TestLinearForceCompletion** (15 connections) — `tests/unit/test_models.py`
- **TestTaskMatching** (15 connections) — `tests/unit/test_models.py`
- **TestRunnerTaskCompletionPromotion** (14 connections) — `tests/unit/test_models.py`
- **TestDynamicChildrenAsPendingInTree** (13 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **TestFreeStrategyMetaTaskVisibility** (12 connections) — `tests/unit/test_models.py`
- **TestStickyFallbackTreeRender** (12 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **TestIncludeStubHiding** (10 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesAsyncTaskIdentity** (8 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesDelegatedTaskIdentity** (8 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesNestedChildIdentity** (8 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesPreflightTaskIdentity** (8 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesSerialWindowIdentity** (8 connections) — `tests/unit/test_tree_projection.py`
- **.test_host_leaves_for_running_dynamic_child()** (7 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **.test_sticky_2_two_plays_both_running()** (7 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **._active_state()** (7 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeProjectionCacheRefresh** (7 connections) — `tests/unit/test_tree_projection.py`
- **.test_completed_dynamic_child_filtered_from_tree()** (6 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **.test_dynamic_child_under_role_header()** (6 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **.test_dynamic_children_show_pending_before_announcement()** (6 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **.test_no_duplicate_for_runtime_announced_dynamic_child()** (6 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- *... and 122 more nodes in this community*

## Relationships

- [CLI Argument Parser](CLI_Argument_Parser.md) (75 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (60 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (60 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (53 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (47 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (37 shared connections)
- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (28 shared connections)
- [Runner Session Recording](Runner_Session_Recording.md) (20 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (14 shared connections)
- [Run Diagnostics Tests](Run_Diagnostics_Tests.md) (12 shared connections)
- [Status Bar Color Tests](Status_Bar_Color_Tests.md) (11 shared connections)
- [WarningType Enum](WarningType_Enum.md) (8 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `tests/unit/test_event_processing.py`
- `tests/unit/test_invariants_runstate_renderer.py`
- `tests/unit/test_models.py`
- `tests/unit/test_tree_classify_and_role_labels.py`
- `tests/unit/test_tree_projection.py`

## Audit Trail

- EXTRACTED: 411 (44%)
- INFERRED: 521 (56%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*