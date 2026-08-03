# Data Model Unit Tests

> 58 nodes · cohesion 0.05

## Key Concepts

- **inspect.py** (42 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **RunSummary** (18 connections) — `src/ansible_aom/core/inspect_model.py`
- **_RunRow** (14 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_ConfirmDelete** (11 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_FooterStatus** (11 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_RunsListView** (11 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_DetailLog** (10 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_HelpScreen** (8 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_render_run_lines()** (8 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **test_status_labels_carry_colour_markup()** (8 connections) — `tests/tui/test_inspect_screen.py`
- **._hydrate_run_row()** (7 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.compose()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._refresh_list()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._render_detail_block()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._visible_summaries()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.update_summary()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_stats_label()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.update()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.action_toggle_failed()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.__init__()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._select_session()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **ComposeResult** (4 connections)
- **RunSummary** (4 connections)
- **_summarise_hosts()** (4 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_fmt_duration_short()** (3 connections) — `src/ansible_aom/tui/screens/inspect.py`
- *... and 33 more nodes in this community*

## Relationships

- [Task Summary Count Tests](Task_Summary_Count_Tests.md) (27 shared connections)
- [ASCII Status Icon Fallback](ASCII_Status_Icon_Fallback.md) (18 shared connections)
- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (14 shared connections)
- [Include Role Discovery](Include_Role_Discovery.md) (14 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (9 shared connections)
- [Log Filter Helpers](Log_Filter_Helpers.md) (5 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (2 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (1 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `src/ansible_aom/tui/screens/inspect.py`
- `tests/tui/test_inspect_screen.py`

## Audit Trail

- EXTRACTED: 215 (80%)
- INFERRED: 54 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*