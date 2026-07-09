# PTY Buffer Stall Handling

> 64 nodes · cohesion 0.07

## Key Concepts

- **InspectApp** (98 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **TaskTreeNode** (27 connections) — `src/ansible_aom/core/inspect_model.py`
- **_NavTree** (23 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **VerboseScope** (11 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._update_detail()** (10 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._load_tasks_for()** (9 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._refresh_footer()** (9 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._focus_pane_id()** (8 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._current_pane()** (7 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._failure_pairs()** (7 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._footer_scope()** (7 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.on_mount()** (7 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._reload_runs()** (7 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._verbose_scope_from_focus()** (7 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.focus_detail()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._focus_failure_at()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._refresh_pane_focus_classes()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_copy_to_clipboard()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.action_open_verbose()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._add_node()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.focus_tasks()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._set_verbose_flash()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.action_next_failure()** (4 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.action_prev_failure()** (4 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._ancestor_tree_node()** (4 connections) — `src/ansible_aom/tui/screens/inspect.py`
- *... and 39 more nodes in this community*

## Relationships

- [Task Summary Count Tests](Task_Summary_Count_Tests.md) (39 shared connections)
- [Data Model Unit Tests](Data_Model_Unit_Tests.md) (38 shared connections)
- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (10 shared connections)
- [ASCII Status Icon Fallback](ASCII_Status_Icon_Fallback.md) (4 shared connections)
- [Total Task Counting](Total_Task_Counting.md) (2 shared connections)
- [Community 503](Community_503.md) (1 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (1 shared connections)
- [Event Source Adapters](Event_Source_Adapters.md) (1 shared connections)
- [Loop Item Line Tests](Loop_Item_Line_Tests.md) (1 shared connections)
- [Log Filter Helpers](Log_Filter_Helpers.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `src/ansible_aom/tui/screens/inspect.py`

## Audit Trail

- EXTRACTED: 286 (74%)
- INFERRED: 100 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*