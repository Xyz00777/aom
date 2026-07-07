# Tree Render Snapshot Tests

> 34 nodes · cohesion 0.08

## Key Concepts

- **test_tree_render.py** (25 connections) — `tests/compact/test_tree_render.py`
- **_state()** (13 connections) — `tests/compact/test_tree_render.py`
- **_full_panel()** (10 connections) — `tests/compact/test_tree_render.py`
- **test_ancestor_spine_continues_under_tail_after()** (5 connections) — `tests/compact/test_tree_render.py`
- **test_format_host_rows_two_space_column_separator()** (5 connections) — `tests/compact/test_tree_render.py`
- **test_format_tree_block_host_leaves_are_plain_indented()** (5 connections) — `tests/compact/test_tree_render.py`
- **test_has_tail_after_demotes_last_to_mid()** (5 connections) — `tests/compact/test_tree_render.py`
- **test_hosts_completed_doesnt_oscillate_with_in_flight_task()** (5 connections) — `tests/compact/test_tree_render.py`
- **test_more_kind_suppresses_branch_glyph()** (5 connections) — `tests/compact/test_tree_render.py`
- **test_format_host_rows_idle_host_shows_idle_marker()** (4 connections) — `tests/compact/test_tree_render.py`
- **test_format_host_rows_running_host_includes_current_task_suffix()** (4 connections) — `tests/compact/test_tree_render.py`
- **test_format_host_rows_unreachable_host_shows_unreachable()** (4 connections) — `tests/compact/test_tree_render.py`
- **test_format_tree_block_ascii_fallback()** (4 connections) — `tests/compact/test_tree_render.py`
- **test_format_tree_block_emits_tree_shape()** (4 connections) — `tests/compact/test_tree_render.py`
- **test_format_tree_block_invisible_returns_empty()** (4 connections) — `tests/compact/test_tree_render.py`
- **test_free_strategy_panel_shows_two_tasks()** (4 connections) — `tests/compact/test_tree_render.py`
- **test_linear_strategy_panel_shape()** (4 connections) — `tests/compact/test_tree_render.py`
- **test_post_recap_panel_drops_tree_and_suffix()** (4 connections) — `tests/compact/test_tree_render.py`
- **test_render_status_panel_is_status_bar_only_before_any_task()** (3 connections) — `tests/compact/test_tree_render.py`
- **test_render_status_panel_status_bar_is_last_line()** (3 connections) — `tests/compact/test_tree_render.py`
- **test_render_status_panel_includes_tree_when_task_running()** (2 connections) — `tests/compact/test_tree_render.py`
- **Snapshot tests for the compact renderer's tree + host-row block.  These pin the** (1 connections) — `tests/compact/test_tree_render.py`
- **Regression guard: spacing between count cells and the suffix is     two spaces (** (1 connections) — `tests/compact/test_tree_render.py`
- **Regression guard: host children render WITHOUT a branch glyph,     matching the** (1 connections) — `tests/compact/test_tree_render.py`
- **When no task is RUNNING, the panel shows only the status bar —     no tree, no h** (1 connections) — `tests/compact/test_tree_render.py`
- *... and 9 more nodes in this community*

## Relationships

- [[Tree Block Animation]] (8 shared connections)
- [[Run State Completion Recap]] (7 shared connections)
- [[Host Overview Table]] (5 shared connections)
- [[Compact Renderer Implementation]] (4 shared connections)
- [[Panel Refresh Snapshot]] (2 shared connections)
- [[Compact Renderer Formatters]] (1 shared connections)

## Source Files

- `tests/compact/test_tree_render.py`

## Audit Trail

- EXTRACTED: 112 (83%)
- INFERRED: 23 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*