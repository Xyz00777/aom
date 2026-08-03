# format_tree_block

> 31 nodes · cohesion 0.11

## Key Concepts

- **format_tree_block()** (48 connections) — `src/ansible_aom/compact/format.py`
- **_state_with_play()** (14 connections) — `tests/compact/test_tree_large_playbook.py`
- **_state_with_play()** (14 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_tree_large_playbook.py** (12 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_tree_upcoming_tasks.py** (12 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_100_percent_completed_shows_empty_tree()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_completed_tasks_removed_100_tasks_5_hosts_over_budget()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_completed_tasks_removed_under_budget()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_single_host_tight_budget()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_tree_content_changes_as_tasks_complete()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_tree_shrinks_when_unbounded_fits_budget()** (5 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_all_completed_falls_back_to_first_pending()** (5 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_upcoming_tasks_marked_pending()** (5 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_completed_tasks_not_in_tree()** (4 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_running_task_visible()** (4 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_upcoming_tasks_visible_after_running()** (4 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **_task_def()** (3 connections) — `tests/compact/test_tree_large_playbook.py`
- **_task_def()** (3 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **Render the tree block as a list of lines.      Returns an empty list when the pr** (1 connections) — `src/ansible_aom/compact/format.py`
- **Tree projection with large playbooks: budget saturation and completed-task remov** (1 connections) — `tests/compact/test_tree_large_playbook.py`
- **With 65/100 tasks completed (still over budget), completed tasks     must NOT ap** (1 connections) — `tests/compact/test_tree_large_playbook.py`
- **With 90/100 tasks completed (well under budget), completed tasks     must NOT ap** (1 connections) — `tests/compact/test_tree_large_playbook.py`
- **Simulate progression from task-0000 running to task-0065 running.     At each st** (1 connections) — `tests/compact/test_tree_large_playbook.py`
- **When enough tasks complete that the unbounded tree fits under     budget, the re** (1 connections) — `tests/compact/test_tree_large_playbook.py`
- **With 1 host and budget=8 (minimum), completed tasks still removed.** (1 connections) — `tests/compact/test_tree_large_playbook.py`
- *... and 6 more nodes in this community*

## Relationships

- [HostRunState](HostRunState.md) (17 shared connections)
- [.from_run_state](from_run_state.md) (12 shared connections)
- [test_tree_render.py](test_tree_render.py.md) (9 shared connections)
- [Rerun Host Set Composition](Rerun_Host_Set_Composition.md) (7 shared connections)
- [renderer.py](renderer.py.md) (6 shared connections)
- [Get All Actions](Get_All_Actions.md) (3 shared connections)
- [icons.py](icons.py.md) (2 shared connections)
- [tree.py](tree.py.md) (2 shared connections)
- [PlayDefinition](PlayDefinition.md) (2 shared connections)
- [RunState](RunState.md) (2 shared connections)
- [TaskDefinition](TaskDefinition.md) (2 shared connections)
- [Dirty Flag Throttle](Dirty_Flag_Throttle.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_tree_large_playbook.py`
- `tests/compact/test_tree_upcoming_tasks.py`

## Audit Trail

- EXTRACTED: 162 (95%)
- INFERRED: 9 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*