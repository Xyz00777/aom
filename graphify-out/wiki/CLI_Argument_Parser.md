# CLI Argument Parser

> 44 nodes · cohesion 0.09

## Key Concepts

- **_play_start()** (16 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestDynamicExpansion** (14 connections) — `tests/unit/test_dynamic_expansion.py`
- **_task_start()** (13 connections) — `tests/unit/test_dynamic_expansion.py`
- **test_dynamic_expansion.py** (10 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestIncludeRoleRuntimeGraft** (10 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_tree_projection_shows_pending_role_tasks()** (10 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_runtime_cache_reuses_preflight_entry()** (9 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_repeated_task_uuid_does_not_re_graft()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_first_role_task_reveals_all_role_tasks_as_pending_siblings()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_grafted_sibling_carries_role_field_for_total_count()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_subsequent_role_tasks_do_not_duplicate_siblings()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_nested_include_role_grafts_inner_role_as_children()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestRuntimeIncludeDiscovery** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_task_path_populates_include_cache()** (8 connections) — `tests/unit/test_dynamic_expansion.py`
- **Path** (7 connections)
- **.test_dynamic_task_inherits_parent_play_fields()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_grafting_works_under_v2_runner_on_start()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_multiple_unknown_tasks_accumulate_under_same_parent()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_orphan_dynamic_task_when_no_parent_seen_yet()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_static_task_following_dynamic_resets_parent()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_unknown_task_grafted_as_child_of_last_matched_task()** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **TestIncludeRoleStubInsideOuterRole** (7 connections) — `tests/unit/test_dynamic_expansion.py`
- **_runner_start()** (5 connections) — `tests/unit/test_dynamic_expansion.py`
- **.test_no_grafting_without_definitions()** (5 connections) — `tests/unit/test_dynamic_expansion.py`
- **_task_start_with_path()** (3 connections) — `tests/unit/test_dynamic_expansion.py`
- *... and 19 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (52 shared connections)
- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (5 shared connections)
- [Hide State Gating Tests](Hide_State_Gating_Tests.md) (4 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)

## Source Files

- `tests/unit/test_dynamic_expansion.py`

## Audit Trail

- EXTRACTED: 166 (73%)
- INFERRED: 60 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*