# Data Model Unit Tests

> 58 nodes · cohesion 0.06

## Key Concepts

- **inspect.py** (17 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **DetailBlock** (15 connections) — `src/ansible_aom/core/inspect_model.py`
- **RunSummary** (14 connections) — `src/ansible_aom/core/inspect_model.py`
- **_RunRow** (12 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_ConfirmDelete** (11 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_FooterStatus** (11 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_RunsListView** (11 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_DetailLog** (10 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_HelpScreen** (8 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **test_status_labels_carry_colour_markup()** (8 connections) — `tests/tui/test_inspect_screen.py`
- **_render_run_lines()** (7 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.compose()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._refresh_list()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._render_detail_block()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._visible_summaries()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_stats_label()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **Static** (6 connections)
- **test_run_row_renders_local_timezone()** (6 connections) — `tests/tui/test_inspect_screen.py`
- **.action_toggle_failed()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.__init__()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._select_session()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.update()** (4 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **ComposeResult** (4 connections)
- **_summarise_hosts()** (4 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_fmt_duration_short()** (3 connections) — `src/ansible_aom/tui/screens/inspect.py`
- *... and 33 more nodes in this community*

## Relationships

- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (38 shared connections)
- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (14 shared connections)
- [Task Summary Count Tests](Task_Summary_Count_Tests.md) (6 shared connections)
- [Community 503](Community_503.md) (2 shared connections)
- [Crash Recovery Auto-Save](Crash_Recovery_Auto-Save.md) (2 shared connections)
- [ASCII Status Icon Fallback](ASCII_Status_Icon_Fallback.md) (1 shared connections)
- [Generate Script](Generate_Script.md) (1 shared connections)
- [Module Init File](Module_Init_File.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `src/ansible_aom/tui/screens/inspect.py`
- `tests/tui/test_inspect_screen.py`

## Audit Trail

- EXTRACTED: 178 (72%)
- INFERRED: 69 (28%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*