# Playbook Parser Integration Tests

> 65 nodes · cohesion 0.06

## Key Concepts

- **StatusCounts** (40 connections) — `src/ansible_aom/core/inspect_model.py`
- **test_inspect_model.py** (29 connections) — `tests/unit/test_inspect_model.py`
- **build_task_tree()** (27 connections) — `src/ansible_aom/core/inspect_model.py`
- **inspect_model.py** (22 connections) — `src/ansible_aom/core/inspect_model.py`
- **build_run_summary()** (13 connections) — `src/ansible_aom/core/inspect_model.py`
- **_load_fixture()** (13 connections) — `tests/unit/test_inspect_model.py`
- **build_detail_block()** (11 connections) — `src/ansible_aom/core/inspect_model.py`
- **build_run_summaries()** (5 connections) — `src/ansible_aom/core/inspect_model.py`
- **_nest_includes()** (5 connections) — `src/ansible_aom/core/inspect_model.py`
- **_parse_iso()** (5 connections) — `src/ansible_aom/core/inspect_model.py`
- **test_task_tree_rolls_up_nested_include_stats_to_directive()** (5 connections) — `tests/unit/test_inspect_model.py`
- **.add_event()** (4 connections) — `src/ansible_aom/core/inspect_model.py`
- **_task_ids_by_play()** (4 connections) — `src/ansible_aom/core/inspect_model.py`
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
- *... and 40 more nodes in this community*

## Relationships

- [Data Model Unit Tests](Data_Model_Unit_Tests.md) (14 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (10 shared connections)
- [Community 503](Community_503.md) (5 shared connections)
- [ASCII Status Icon Fallback](ASCII_Status_Icon_Fallback.md) (5 shared connections)
- [Log Filter Helpers](Log_Filter_Helpers.md) (4 shared connections)
- [Plaintext Line Handling](Plaintext_Line_Handling.md) (3 shared connections)
- [Task Summary Count Tests](Task_Summary_Count_Tests.md) (2 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `tests/unit/test_inspect_model.py`

## Audit Trail

- EXTRACTED: 207 (70%)
- INFERRED: 90 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*