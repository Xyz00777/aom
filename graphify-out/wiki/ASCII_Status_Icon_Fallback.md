# ASCII Status Icon Fallback

> 58 nodes · cohesion 0.06

## Key Concepts

- **TaskTreeNode** (43 connections) — `src/ansible_aom/core/inspect_model.py`
- **text.py** (36 connections) — `src/ansible_aom/inspect/text.py`
- **DetailBlock** (18 connections) — `src/ansible_aom/core/inspect_model.py`
- **build_detail_block()** (17 connections) — `src/ansible_aom/core/inspect_model.py`
- **render_session_from_index()** (14 connections) — `src/ansible_aom/inspect/text.py`
- **_only_block()** (12 connections) — `tests/unit/test_inspect_model.py`
- **_render_verbose()** (11 connections) — `src/ansible_aom/inspect/text.py`
- **TestAsyncPollDoesNotLeakDictIntoLoopItem** (10 connections) — `tests/unit/test_inspect_model.py`
- **_render_failures_from_index()** (8 connections) — `src/ansible_aom/inspect/text.py`
- **_make_loop_item()** (7 connections) — `src/ansible_aom/core/inspect_model.py`
- **_resolve_verbose_scope()** (7 connections) — `src/ansible_aom/inspect/text.py`
- **_hydrate_node()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_iter_tree()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_play_name_for_task()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_render_failures()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_render_header()** (6 connections) — `src/ansible_aom/inspect/text.py`
- **_iter_failed_tasks()** (5 connections) — `src/ansible_aom/inspect/text.py`
- **_render_detail()** (5 connections) — `src/ansible_aom/inspect/text.py`
- **LoopItem** (4 connections) — `src/ansible_aom/core/inspect_model.py`
- **_fmt_duration()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **render_session_list()** (4 connections) — `src/ansible_aom/inspect/text.py`
- **_host_counts_line()** (3 connections) — `src/ansible_aom/inspect/text.py`
- **Path** (3 connections)
- **_verbose_section()** (3 connections) — `src/ansible_aom/inspect/text.py`
- **test_detail_block_ignores_result_keys_without_verbose_flag()** (3 connections) — `tests/unit/test_inspect_model.py`
- *... and 33 more nodes in this community*

## Relationships

- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (21 shared connections)
- [Log Filter Helpers](Log_Filter_Helpers.md) (18 shared connections)
- [Data Model Unit Tests](Data_Model_Unit_Tests.md) (18 shared connections)
- [Include Role Discovery](Include_Role_Discovery.md) (16 shared connections)
- [Task Summary Count Tests](Task_Summary_Count_Tests.md) (9 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (9 shared connections)
- [Two-Cut Tree Truncation](Two-Cut_Tree_Truncation.md) (5 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (3 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `src/ansible_aom/inspect/text.py`
- `tests/unit/test_inspect_model.py`

## Audit Trail

- EXTRACTED: 253 (85%)
- INFERRED: 45 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*