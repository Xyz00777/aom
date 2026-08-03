# Pause Prompt Heuristic

> 36 nodes · cohesion 0.09

## Key Concepts

- **format_tree_block()** (48 connections) — `src/ansible_aom/compact/format.py`
- **_state_with_play()** (14 connections) — `tests/compact/test_tree_large_playbook.py`
- **_state_with_play()** (14 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_tree_large_playbook.py** (12 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_tree_upcoming_tasks.py** (12 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_spinner_animation.py** (8 connections) — `tests/compact/test_spinner_animation.py`
- **test_default_frame_still_works_for_backward_compat()** (5 connections) — `tests/compact/test_spinner_animation.py`
- **test_100_percent_completed_shows_empty_tree()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_completed_tasks_removed_100_tasks_5_hosts_over_budget()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_completed_tasks_removed_under_budget()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_single_host_tight_budget()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_tree_content_changes_as_tasks_complete()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_tree_shrinks_when_unbounded_fits_budget()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_all_completed_falls_back_to_first_pending()** (5 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_upcoming_tasks_marked_pending()** (5 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_spinner_glyph_changes_with_animation_frame()** (4 connections) — `tests/compact/test_spinner_animation.py`
- **test_completed_tasks_not_in_tree()** (4 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_running_task_visible()** (4 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_upcoming_tasks_visible_after_running()** (4 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **_task_def()** (3 connections) — `tests/compact/test_tree_large_playbook.py`
- **_task_def()** (3 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **Render the tree block as a list of lines.      Returns an empty list when the pr** (1 connections) — `src/ansible_aom/compact/format.py`
- **Running spinner (◐→◓→◑→◒) animates across renders.  Previously ``format_tree_blo** (1 connections) — `tests/compact/test_spinner_animation.py`
- **Existing callers that don't pass animation_frame still render.** (1 connections) — `tests/compact/test_spinner_animation.py`
- **Tree projection with large playbooks: budget saturation and completed-task remov** (1 connections) — `tests/compact/test_tree_large_playbook.py`
- *... and 11 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (23 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (12 shared connections)
- [Four-Layer Redaction System](Four-Layer_Redaction_System.md) (8 shared connections)
- [Rerun Host Set Composition](Rerun_Host_Set_Composition.md) (7 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (5 shared connections)
- [Get All Actions](Get_All_Actions.md) (3 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (3 shared connections)
- [tree.py](tree.py.md) (3 shared connections)
- [Session List View](Session_List_View.md) (2 shared connections)
- [._render_status_panel](_render_status_panel.md) (2 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (1 shared connections)
- [RunState Property Invariants](RunState_Property_Invariants.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_spinner_animation.py`
- `tests/compact/test_tree_large_playbook.py`
- `tests/compact/test_tree_upcoming_tasks.py`

## Audit Trail

- EXTRACTED: 128 (67%)
- INFERRED: 62 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*