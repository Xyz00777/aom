# UUIDv7 Session Generation

> 27 nodes · cohesion 0.13

## Key Concepts

- **TestPerEventLogColors** (15 connections) — `tests/compact/test_status_bar_colors.py`
- **TestFinalCompletionIndicator** (12 connections) — `tests/compact/test_status_bar_colors.py`
- **test_status_bar_colors.py** (10 connections) — `tests/compact/test_status_bar_colors.py`
- **TestColorEnabled** (10 connections) — `tests/compact/test_status_bar_colors.py`
- **._logged()** (8 connections) — `tests/compact/test_status_bar_colors.py`
- **._renderer()** (8 connections) — `tests/compact/test_status_bar_colors.py`
- **_color_enabled()** (7 connections) — `src/ansible_aom/compact/format.py`
- **._final_line()** (6 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_skipping_line_is_cyan()** (4 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_changed_line_is_yellow()** (3 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_failed_line_is_red()** (3 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_no_color_when_renderer_colorize_off()** (3 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_ok_line_is_green()** (3 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_unreachable_line_is_magenta()** (3 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_off_when_no_color_set_even_for_tty()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_off_when_not_a_tty()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_on_when_tty_and_no_color_unset()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_cancelled_indicator_is_yellow()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_completed_indicator_is_green()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_failed_indicator_is_red()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_no_color_when_disabled()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **True if we should emit SGR codes — TTY only, NO_COLOR honored.** (1 connections) — `src/ansible_aom/compact/format.py`
- **Tests for semantic SGR colouring in the compact status output.  Colour rules (wh** (1 connections) — `tests/compact/test_status_bar_colors.py`
- **The trailing ●/✖ indicator picks its colour from the state.** (1 connections) — `tests/compact/test_status_bar_colors.py`
- **Per-task log lines (ok/changed/fatal/unreachable/skipping) carry     semantic co** (1 connections) — `tests/compact/test_status_bar_colors.py`
- *... and 2 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (9 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (6 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (3 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (3 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (1 shared connections)
- [Frame Parameter Handling](Frame_Parameter_Handling.md) (1 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (1 shared connections)
- [Session List View](Session_List_View.md) (1 shared connections)
- [Renderer Event Protocol](Renderer_Event_Protocol.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_status_bar_colors.py`

## Audit Trail

- EXTRACTED: 93 (81%)
- INFERRED: 22 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*