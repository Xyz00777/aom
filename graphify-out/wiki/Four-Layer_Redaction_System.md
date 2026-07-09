# Four-Layer Redaction System

> 39 nodes · cohesion 0.08

## Key Concepts

- **test_tree_render.py** (25 connections) — `tests/compact/test_tree_render.py`
- **_state()** (13 connections) — `tests/compact/test_tree_render.py`
- **_visible_projection()** (11 connections) — `tests/compact/test_tree_render.py`
- **_full_panel()** (10 connections) — `tests/compact/test_tree_render.py`
- **._capture_panel_snapshot()** (7 connections) — `src/ansible_aom/compact/renderer.py`
- **_compute_tree_budget()** (6 connections) — `src/ansible_aom/compact/format.py`
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

- [CLI Interface Tests](CLI_Interface_Tests.md) (11 shared connections)
- [Pause Prompt Heuristic](Pause_Prompt_Heuristic.md) (9 shared connections)
- [RunState Property Invariants](RunState_Property_Invariants.md) (6 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (5 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (4 shared connections)
- [Hide State Gating Tests](Hide_State_Gating_Tests.md) (4 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (3 shared connections)
- [Renderer Set Definitions](Renderer_Set_Definitions.md) (1 shared connections)
- [Community 560](Community_560.md) (1 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (1 shared connections)
- [Community 642](Community_642.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`
- `tests/compact/test_tree_render.py`

## Audit Trail

- EXTRACTED: 127 (80%)
- INFERRED: 31 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*