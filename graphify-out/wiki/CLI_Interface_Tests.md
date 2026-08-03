# CLI Interface Tests

> 472 nodes · cohesion 0.01

## Key Concepts

- **RunState** (592 connections) — `src/ansible_aom/core/run_state.py`
- **TaskDefinition** (376 connections) — `src/ansible_aom/core/models.py`
- **PlayDefinition** (349 connections) — `src/ansible_aom/core/models.py`
- **.from_run_state()** (203 connections) — `src/ansible_aom/core/tree_projection.py`
- **RoleGroupDefinition** (156 connections) — `src/ansible_aom/core/models.py`
- **test_tree_projection.py** (28 connections) — `tests/unit/test_tree_projection.py`
- **TestHostRows** (19 connections) — `tests/unit/test_tree_projection.py`
- **TestRoleGroupDefinition** (18 connections) — `tests/unit/test_models.py`
- **TestTwoLevelTruncation** (17 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesBasic** (16 connections) — `tests/unit/test_tree_projection.py`
- **TestLinearForceCompletion** (15 connections) — `tests/unit/test_models.py`
- **test_tree_nested_roles.py** (15 connections) — `tests/unit/test_tree_nested_roles.py`
- **TestTaskCompletionLifecycle** (15 connections) — `tests/unit/test_tree_projection.py`
- **TestRunnerTaskCompletionPromotion** (14 connections) — `tests/unit/test_models.py`
- **TestSubtreeRoleCounting** (14 connections) — `tests/unit/test_tree_projection.py`
- **HostRow** (13 connections) — `src/ansible_aom/core/tree_projection.py`
- **TestPopulateFromProjectionFooters** (13 connections) — `tests/tui/test_tree_more_footers.py`
- **_two_level_state()** (13 connections) — `tests/tui/test_tree_more_footers.py`
- **TestCrossPlayLookupIsolation** (13 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **TestDynamicChildrenAsPendingInTree** (13 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **_RowLease** (12 connections) — `src/ansible_aom/core/tree_projection.py`
- **test_dynamic_counters.py** (12 connections) — `tests/unit/test_dynamic_counters.py`
- **TestFreeStrategyMetaTaskVisibility** (12 connections) — `tests/unit/test_models.py`
- **TestRuntimeRoleTaskCount** (12 connections) — `tests/unit/test_runtime_role_task_count.py`
- **TestStickyFallbackTreeRender** (12 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- *... and 447 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (236 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (98 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (92 shared connections)
- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (64 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (52 shared connections)
- [Check Mode Chip](Check_Mode_Chip.md) (35 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (31 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (30 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (28 shared connections)
- [AOM TUI Application](AOM_TUI_Application.md) (27 shared connections)
- [Runner Session Recording](Runner_Session_Recording.md) (24 shared connections)
- [Pause Prompt Heuristic](Pause_Prompt_Heuristic.md) (23 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/run_state.py`
- `src/ansible_aom/core/tree_projection.py`
- `tests/compact/test_spinner_animation.py`
- `tests/compact/test_tree_render.py`
- `tests/tui/test_live_refresh.py`
- `tests/tui/test_tree_more_footers.py`
- `tests/unit/test_dynamic_counters.py`
- `tests/unit/test_host_resolution.py`
- `tests/unit/test_invariants_runstate_renderer.py`
- `tests/unit/test_loop_item_count.py`
- `tests/unit/test_models.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_runtime_role_task_count.py`
- `tests/unit/test_stale_running_cleanup.py`
- `tests/unit/test_template_variable_names.py`
- `tests/unit/test_tree_classify_and_role_labels.py`
- `tests/unit/test_tree_meta_hostless.py`
- `tests/unit/test_tree_nested_roles.py`
- `tests/unit/test_tree_projection.py`

## Audit Trail

- EXTRACTED: 2040 (57%)
- INFERRED: 1555 (43%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*