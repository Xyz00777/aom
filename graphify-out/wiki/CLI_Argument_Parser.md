# CLI Argument Parser

> 130 nodes · cohesion 0.03

## Key Concepts

- **PlayDefinition** (340 connections) — `src/ansible_aom/core/models.py`
- **TestPlayDefinition** (20 connections) — `tests/unit/test_models.py`
- **_play_start()** (16 connections) — `tests/unit/test_dynamic_expansion.py`
- **count_total_tasks()** (15 connections) — `src/ansible_aom/compact/format.py`
- **test_task_progress.py** (15 connections) — `tests/compact/test_task_progress.py`
- **TestDynamicExpansion** (14 connections) — `tests/unit/test_dynamic_expansion.py`
- **_task_start()** (13 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestRuntimeRoleTaskCount** (12 connections) — `tests/unit/test_runtime_role_task_count.py`
- **count_total_tasks_seen()** (11 connections) — `src/ansible_aom/compact/format.py`
- **.handle_completion()** (10 connections) — `src/ansible_aom/compact/renderer.py`
- **test_dynamic_counters.py** (10 connections) — `tests/unit/test_dynamic_counters.py`
- **TestIncludeRoleRuntimeGraft** (10 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_tree_projection_shows_pending_role_tasks()** (10 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestHostCrossCheckDuringExecution** (10 connections) — `tests/unit/test_host_resolution.py`
- **test_dynamic_expansion.py** (9 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_runtime_cache_reuses_preflight_entry()** (9 connections) — `tests/unit/test_dynamic_expansion.py`
- **test_count_total_tasks_grows_with_runtime_announced_tasks()** (8 connections) — `tests/compact/test_task_progress.py`
- **test_handle_completion_keeps_runtime_grown_denominator()** (8 connections) — `tests/compact/test_task_progress.py`
- **test_total_tasks_seen_no_cache_falls_back_to_preflight_runtime_max()** (8 connections) — `tests/unit/test_dynamic_counters.py`
- **.test_repeated_task_uuid_does_not_re_graft()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_first_role_task_reveals_all_role_tasks_as_pending_siblings()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_grafted_sibling_carries_role_field_for_total_count()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_subsequent_role_tasks_do_not_duplicate_siblings()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_nested_include_role_grafts_inner_role_as_children()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestRuntimeIncludeDiscovery** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- *... and 105 more nodes in this community*

## Relationships

- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (75 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (45 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (35 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (34 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (28 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (24 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (20 shared connections)
- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (18 shared connections)
- [Runner Session Recording](Runner_Session_Recording.md) (18 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (12 shared connections)
- [Renderer Set Definitions](Renderer_Set_Definitions.md) (7 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (7 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`
- `src/ansible_aom/core/models.py`
- `tests/compact/test_task_progress.py`
- `tests/unit/test_dynamic_counters.py`
- `tests/unit/test_dynamic_expansion.py`
- `tests/unit/test_host_resolution.py`
- `tests/unit/test_models.py`
- `tests/unit/test_runtime_role_task_count.py`

## Audit Trail

- EXTRACTED: 418 (48%)
- INFERRED: 462 (52%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*