# Three-Pane Inspect App

> 37 nodes · cohesion 0.05

## Key Concepts

- **InspectApp** (94 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **test_inspect_screen.py** (40 connections) — `tests/tui/test_inspect_screen.py`
- **test_status_labels_carry_colour_markup()** (8 connections) — `tests/tui/test_inspect_screen.py`
- **test_detail_pane_handles_huge_stdout_quickly()** (7 connections) — `tests/tui/test_inspect_screen.py`
- **test_highlighting_successful_task_updates_detail()** (7 connections) — `tests/tui/test_inspect_screen.py`
- **test_run_row_renders_local_timezone()** (6 connections) — `tests/tui/test_inspect_screen.py`
- **_copy_to_clipboard()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **test_ctrl_c_quits_the_app()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_d_cancel_keeps_session()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_d_opens_confirm_then_y_deletes()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_dd_double_tap_deletes()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_delete_auto_selects_next_session()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_detail_block_includes_action_and_no_session_stderr()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_e_expands_all_and_c_collapses_all()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_enter_on_run_row_focuses_tasks_pane()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_enter_on_task_focuses_detail_pane()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_escape_steps_back_to_previous_pane()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_focused_pane_gets_visual_class()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_left_arrow_collapses_or_walks_up_tree()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_left_does_not_steal_focus_to_detail_pane()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_n_and_shift_n_cycle_through_failures()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_question_mark_opens_help()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_r_reloads_runs_from_disk()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_right_arrow_on_runs_drills_into_tasks()** (5 connections) — `tests/tui/test_inspect_screen.py`
- **test_run_row_renders_multi_line_content()** (5 connections) — `tests/tui/test_inspect_screen.py`
- *... and 12 more nodes in this community*

## Relationships

- [[Run Config Key Normalization]] (30 shared connections)
- [[Inspect TUI Widget Data]] (16 shared connections)
- [[Session List View]] (10 shared connections)
- [[Task Tree Navigation]] (9 shared connections)
- [[Pane Focus Navigation]] (9 shared connections)
- [[Inspect Data Model Builders]] (4 shared connections)
- [[Inspect CLI Commands]] (3 shared connections)

## Source Files

- `src/ansible_aom/tui/screens/inspect.py`
- `tests/tui/test_inspect_screen.py`

## Audit Trail

- EXTRACTED: 220 (74%)
- INFERRED: 77 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*