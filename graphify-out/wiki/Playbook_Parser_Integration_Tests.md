# Playbook Parser Integration Tests

> 64 nodes · cohesion 0.06

## Key Concepts

- **StatusCounts** (61 connections) — `src/ansible_aom/core/inspect_model.py`
- **build_task_tree()** (40 connections) — `src/ansible_aom/core/inspect_model.py`
- **test_inspect_model.py** (39 connections) — `tests/unit/test_inspect_model.py`
- **build_run_summary()** (20 connections) — `src/ansible_aom/core/inspect_model.py`
- **_load_fixture()** (13 connections) — `tests/unit/test_inspect_model.py`
- **test_status_tally_bar.py** (11 connections) — `tests/compact/test_status_tally_bar.py`
- **_bar()** (9 connections) — `tests/compact/test_status_tally_bar.py`
- **test_status_tally.py** (8 connections) — `tests/unit/test_status_tally.py`
- **_run_state()** (8 connections) — `tests/unit/test_status_tally.py`
- **build_run_summaries()** (5 connections) — `src/ansible_aom/core/inspect_model.py`
- **test_task_tree_rolls_up_nested_include_stats_to_directive()** (5 connections) — `tests/unit/test_inspect_model.py`
- **.add_event()** (4 connections) — `src/ansible_aom/core/inspect_model.py`
- **_nested_include_session()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_detail_block_loop_failure()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_detail_block_ok_task_no_failure_items()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_detail_block_unreachable()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_run_summary_clean()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_run_summary_failed_loop()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_run_summary_string_task_field()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_task_tree_clean_run_groups_by_role()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_task_tree_failed_loop_marks_failure_path()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_task_tree_multi_host_per_host_breakdown()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_task_tree_nests_dynamic_include_tasks_under_directive()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_task_tree_real_event_shape()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_task_tree_string_task_field()** (4 connections) — `tests/unit/test_inspect_model.py`
- *... and 39 more nodes in this community*

## Relationships

- [Log Filter Helpers](Log_Filter_Helpers.md) (22 shared connections)
- [ASCII Status Icon Fallback](ASCII_Status_Icon_Fallback.md) (21 shared connections)
- [Data Model Unit Tests](Data_Model_Unit_Tests.md) (14 shared connections)
- [Include Role Discovery](Include_Role_Discovery.md) (6 shared connections)
- [Task Summary Count Tests](Task_Summary_Count_Tests.md) (5 shared connections)
- [tree.py](tree.py.md) (5 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (5 shared connections)
- [Diagnostics and Profiler](Diagnostics_and_Profiler.md) (4 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (3 shared connections)
- [Plaintext Line Handling](Plaintext_Line_Handling.md) (3 shared connections)
- [Two-Cut Tree Truncation](Two-Cut_Tree_Truncation.md) (2 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (2 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `tests/compact/test_status_tally_bar.py`
- `tests/unit/test_inspect_model.py`
- `tests/unit/test_status_tally.py`

## Audit Trail

- EXTRACTED: 262 (76%)
- INFERRED: 85 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*