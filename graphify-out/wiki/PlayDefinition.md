# PlayDefinition

> 145 nodes · cohesion 0.02

## Key Concepts

- **PlayDefinition** (323 connections) — `src/ansible_aom/core/models.py`
- **TestPlayDefinition** (20 connections) — `tests/unit/test_models.py`
- **count_total_tasks()** (17 connections) — `src/ansible_aom/compact/format.py`
- **test_task_progress.py** (17 connections) — `tests/compact/test_task_progress.py`
- **_play_start()** (16 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestDynamicExpansion** (14 connections) — `tests/unit/test_dynamic_expansion.py`
- **_task_start()** (13 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestDynamicChildrenAsPendingInTree** (13 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **count_completed_tasks()** (12 connections) — `src/ansible_aom/compact/format.py`
- **count_total_tasks_seen()** (12 connections) — `src/ansible_aom/compact/format.py`
- **test_dynamic_counters.py** (12 connections) — `tests/unit/test_dynamic_counters.py`
- **TestStickyFallbackTreeRender** (12 connections) — `tests/unit/test_tree_classify_and_role_labels.py`
- **test_dynamic_expansion.py** (10 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestIncludeRoleRuntimeGraft** (10 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_tree_projection_shows_pending_role_tasks()** (10 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestHostCrossCheckDuringExecution** (10 connections) — `tests/unit/test_host_resolution.py`
- **test_completed_tasks_counts_dynamic_children()** (9 connections) — `tests/unit/test_dynamic_counters.py`
- **.test_runtime_cache_reuses_preflight_entry()** (9 connections) — `tests/unit/test_dynamic_expansion.py`
- **_count_tasks()** (8 connections) — `src/ansible_aom/compact/format.py`
- **test_count_total_tasks_grows_with_runtime_announced_tasks()** (8 connections) — `tests/compact/test_task_progress.py`
- **test_handle_completion_keeps_runtime_grown_denominator()** (8 connections) — `tests/compact/test_task_progress.py`
- **test_total_tasks_seen_no_cache_falls_back_to_preflight_runtime_max()** (8 connections) — `tests/unit/test_dynamic_counters.py`
- **.test_repeated_task_uuid_does_not_re_graft()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_first_role_task_reveals_all_role_tasks_as_pending_siblings()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_grafted_sibling_carries_role_field_for_total_count()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- *... and 120 more nodes in this community*

## Relationships

- [TaskDefinition](TaskDefinition.md) (104 shared connections)
- [HostRunState](HostRunState.md) (62 shared connections)
- [RunState](RunState.md) (42 shared connections)
- [.from_run_state](from_run_state.md) (42 shared connections)
- [TestCrossPlayLookupIsolation](TestCrossPlayLookupIsolation.md) (20 shared connections)
- [format_preflight_summary](format_preflight_summary.md) (13 shared connections)
- [IncludeCacheEntry](IncludeCacheEntry.md) (11 shared connections)
- [WarningType](WarningType.md) (11 shared connections)
- [renderer.py](renderer.py.md) (10 shared connections)
- [TreeProjection](TreeProjection.md) (6 shared connections)
- [TestV2PlaybookOnStatsCrossCheck](TestV2PlaybookOnStatsCrossCheck.md) (6 shared connections)
- [AOM TUI Application](AOM_TUI_Application.md) (6 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/core/models.py`
- `tests/compact/test_task_progress.py`
- `tests/unit/test_dynamic_counters.py`
- `tests/unit/test_dynamic_expansion.py`
- `tests/unit/test_host_resolution.py`
- `tests/unit/test_models.py`
- `tests/unit/test_tree_classify_and_role_labels.py`

## Audit Trail

- EXTRACTED: 713 (76%)
- INFERRED: 227 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*