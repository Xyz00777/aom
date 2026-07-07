# Inspect Data Model Builders

> 42 nodes · cohesion 0.07

## Key Concepts

- **StatusCounts** (40 connections) — `src/ansible_aom/core/inspect_model.py`
- **build_task_tree()** (28 connections) — `src/ansible_aom/core/inspect_model.py`
- **test_inspect_model.py** (28 connections) — `tests/unit/test_inspect_model.py`
- **inspect_model.py** (21 connections) — `src/ansible_aom/core/inspect_model.py`
- **build_run_summary()** (14 connections) — `src/ansible_aom/core/inspect_model.py`
- **build_detail_block()** (13 connections) — `src/ansible_aom/core/inspect_model.py`
- **_load_fixture()** (13 connections) — `tests/unit/test_inspect_model.py`
- **_make_loop_item()** (7 connections) — `src/ansible_aom/core/inspect_model.py`
- **build_run_summaries()** (5 connections) — `src/ansible_aom/core/inspect_model.py`
- **_parse_iso()** (5 connections) — `src/ansible_aom/core/inspect_model.py`
- **LoopItem** (4 connections) — `src/ansible_aom/core/inspect_model.py`
- **.add_event()** (4 connections) — `src/ansible_aom/core/inspect_model.py`
- **test_detail_block_loop_failure()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_detail_block_ok_task_no_failure_items()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_detail_block_unreachable()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_run_summary_clean()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_run_summary_failed_loop()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_run_summary_string_task_field()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_task_tree_clean_run_groups_by_role()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_task_tree_failed_loop_marks_failure_path()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_task_tree_multi_host_per_host_breakdown()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_task_tree_real_event_shape()** (4 connections) — `tests/unit/test_inspect_model.py`
- **test_task_tree_string_task_field()** (4 connections) — `tests/unit/test_inspect_model.py`
- **_group_key()** (3 connections) — `src/ansible_aom/core/inspect_model.py`
- **test_run_summaries_sorted_newest_first()** (3 connections) — `tests/unit/test_inspect_model.py`
- *... and 17 more nodes in this community*

## Relationships

- [[Inspect TUI Widget Data]] (13 shared connections)
- [[Inspect Text Golden Tests]] (5 shared connections)
- [[Three-Pane Inspect App]] (4 shared connections)
- [[Task Tree Navigation]] (3 shared connections)
- [[Design Specs Plans]] (3 shared connections)
- [[Session Roundtrip Invariants]] (3 shared connections)
- [[Session List View]] (2 shared connections)
- [[Pane Focus Navigation]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `tests/unit/test_inspect_model.py`

## Audit Trail

- EXTRACTED: 173 (66%)
- INFERRED: 90 (34%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*