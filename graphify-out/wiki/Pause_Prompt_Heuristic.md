# Pause Prompt Heuristic

> 31 nodes · cohesion 0.11

## Key Concepts

- **format_tree_block()** (47 connections) — `src/ansible_aom/compact/format.py`
- **_state_with_play()** (14 connections) — `tests/compact/test_tree_large_playbook.py`
- **_state_with_play()** (14 connections) — `tests/compact/test_tree_upcoming_tasks.py`
- **test_tree_large_playbook.py** (9 connections) — `tests/compact/test_tree_large_playbook.py`
- **test_tree_upcoming_tasks.py** (9 connections) — `tests/compact/test_tree_upcoming_tasks.py`
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

- [CLI Interface Tests](CLI_Interface_Tests.md) (13 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (13 shared connections)
- [Four-Layer Redaction System](Four-Layer_Redaction_System.md) (9 shared connections)
- [Rerun Host Set Composition](Rerun_Host_Set_Composition.md) (7 shared connections)
- [Get All Actions](Get_All_Actions.md) (3 shared connections)
- [Renderer Set Definitions](Renderer_Set_Definitions.md) (2 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (2 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (2 shared connections)
- [RunState Property Invariants](RunState_Property_Invariants.md) (1 shared connections)
- [Community 642](Community_642.md) (1 shared connections)
- [Crash Recovery Notification](Crash_Recovery_Notification.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_tree_large_playbook.py`
- `tests/compact/test_tree_upcoming_tasks.py`

## Audit Trail

- EXTRACTED: 104 (63%)
- INFERRED: 60 (37%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*