# Tree Block Animation

> 37 nodes · cohesion 0.08

## Key Concepts

- **format_tree_block()** (39 connections) — `src/ansible_aom/compact/format.py`
- **_state_with_play()** (14 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_tree_pipe_continuation.py** (11 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_tree_upcoming_tasks.py** (9 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_no_preflight_falls_back_to_running_only()** (8 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_default_frame_still_works_for_backward_compat()** (5 connections) — `tests/compact/test_spinner_animation.py`
- **test_ascii_mode_uses_pipe_substitute()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_last_play_children_have_plain_indent()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_non_last_play_children_show_vertical_pipe()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_spur_continues_spine_through_inner_footer()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_spur_continues_spine_through_outer_footer()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_spur_in_ascii_mode_inner_footer()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_spur_in_ascii_mode_outer_footer()** (5 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_all_completed_falls_back_to_first_pending()** (5 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_upcoming_tasks_marked_pending()** (5 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_spinner_animation.py** (4 connections) — `tests/compact/test_spinner_animation.py`
- **test_spinner_glyph_changes_with_animation_frame()** (4 connections) — `tests/compact/test_spinner_animation.py`
- **test_completed_tasks_not_in_tree()** (4 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_running_task_visible()** (4 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_upcoming_tasks_visible_after_running()** (4 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **_task_def()** (3 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **Render the tree block as a list of lines.      Returns an empty list when the pr** (1 connections) — `src/ansible_aom/compact/format.py`
- **Running spinner (◐→◓→◑→◒) animates across renders.  Previously ``format_tree_blo** (1 connections) — `tests/compact/test_spinner_animation.py`
- **Existing callers that don't pass animation_frame still render.** (1 connections) — `tests/compact/test_spinner_animation.py`
- **Tree-block lines under a non-last play must show the vertical continuation pipe** (1 connections) — `tests/compact/test_tree_pipe_continuation.py`
- *... and 12 more nodes in this community*

## Relationships

- [[Run State Completion Recap]] (23 shared connections)
- [[Play Definition Tree Population]] (16 shared connections)
- [[Tree Render Snapshot Tests]] (8 shared connections)
- [[Compact Renderer Formatters]] (3 shared connections)
- [[Panel Refresh Snapshot]] (2 shared connections)
- [[Run State Summary Panel]] (2 shared connections)
- [[Host Overview Table]] (1 shared connections)
- [[Running Animation Frames]] (1 shared connections)
- [[Status Color Mapping]] (1 shared connections)
- [[Tree Projection Logic]] (1 shared connections)
- [[Tree Truncation Utilities]] (1 shared connections)
- [[Run History Mining]] (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_spinner_animation.py`
- `tests/compact/test_tree_pipe_continuation.py`
- `tests/compact/test_tree_upcoming_tasks.py`

## Audit Trail

- EXTRACTED: 112 (66%)
- INFERRED: 58 (34%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*