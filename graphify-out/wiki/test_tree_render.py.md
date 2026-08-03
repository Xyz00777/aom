# test_tree_render.py

> 39 nodes · cohesion 0.08

## Key Concepts

- **test_tree_render.py** (28 connections) — `tests/compact/test_tree_render.py`
- **_state()** (13 connections) — `tests/compact/test_tree_render.py`
- **_visible_projection()** (11 connections) — `tests/compact/test_tree_render.py`
- **_full_panel()** (10 connections) — `tests/compact/test_tree_render.py`
- **_compute_tree_budget()** (7 connections) — `src/ansible_aom/compact/format.py`
- **._capture_panel_snapshot()** (7 connections) — `src/ansible_aom/compact/renderer.py`
- **test_ancestor_spine_continues_under_tail_after()** (5 connections) — `tests/compact/test_tree_render.py`
- **test_format_host_rows_two_space_column_separator()** (5 connections) — `tests/compact/test_tree_render.py`
- **test_format_tree_block_host_leaves_are_plain_indented()** (5 connections) — `tests/compact/test_tree_render.py`
- **test_has_tail_after_demotes_last_to_mid()** (5 connections) — `tests/compact/test_tree_render.py`
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
- **test_compute_tree_budget_math()** (2 connections) — `tests/compact/test_tree_render.py`
- **test_render_status_panel_includes_tree_when_task_running()** (2 connections) — `tests/compact/test_tree_render.py`
- **Tree height budget in lines.      Baseline ~½ of terminal rows; +1 line per 3 ac** (1 connections) — `src/ansible_aom/compact/format.py`
- *... and 14 more nodes in this community*

## Relationships

- [.from_run_state](from_run_state.md) (17 shared connections)
- [format_tree_block](format_tree_block.md) (9 shared connections)
- [HostRunState](HostRunState.md) (6 shared connections)
- [renderer.py](renderer.py.md) (4 shared connections)
- [CompactRenderer](CompactRenderer.md) (4 shared connections)
- [TreeProjection](TreeProjection.md) (4 shared connections)
- [RunState](RunState.md) (3 shared connections)
- [._emit_event_log](_emit_event_log.md) (1 shared connections)
- [_BoundedSet](_BoundedSet.md) (1 shared connections)
- [tree.py](tree.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`
- `tests/compact/test_tree_render.py`

## Audit Trail

- EXTRACTED: 142 (88%)
- INFERRED: 20 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*