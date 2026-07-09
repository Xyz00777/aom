# Session Recording Tests

> 146 nodes · cohesion 0.02

## Key Concepts

- **AOMApp** (181 connections) — `src/ansible_aom/tui/app.py`
- **TaskTree** (47 connections) — `src/ansible_aom/tui/widgets/task_tree.py`
- **MainScreen** (31 connections) — `src/ansible_aom/tui/screens/main.py`
- **TestRendererProtocol** (19 connections) — `tests/unit/test_cli.py`
- **TestDirtyCounter** (16 connections) — `tests/tui/test_live_refresh.py`
- **TestMainScreenTreeIntegration** (15 connections) — `tests/tui/test_live_refresh.py`
- **TestCompletionTitleUpdate** (13 connections) — `tests/tui/test_live_refresh.py`
- **TestPeriodicRefresh** (13 connections) — `tests/tui/test_live_refresh.py`
- **TestTreePopulationFromDefinitions** (13 connections) — `tests/tui/test_live_refresh.py`
- **TestCallFromThreadRouting** (12 connections) — `tests/tui/test_live_refresh.py`
- **TestEndToEndThreeTasks** (12 connections) — `tests/tui/test_live_refresh.py`
- **Event** (11 connections)
- **.test_update_from_state_drops_completed_tasks()** (10 connections) — `tests/tui/test_live_refresh.py`
- **.test_update_from_state_keeps_running_task_visible()** (10 connections) — `tests/tui/test_live_refresh.py`
- **.test_update_from_state_shows_ok_icon_after_completion()** (10 connections) — `tests/tui/test_live_refresh.py`
- **TestRunStateOwnership** (9 connections) — `tests/tui/test_app_end_to_end.py`
- **test_live_refresh.py** (9 connections) — `tests/tui/test_live_refresh.py`
- **TestAOMAppInteractivePrompt** (9 connections) — `tests/unit/test_interactive_prompt.py`
- **.update_from_state()** (8 connections) — `src/ansible_aom/tui/screens/main.py`
- **TestAOMAppConstruction** (7 connections) — `tests/tui/test_app_end_to_end.py`
- **TestWarningsAndLogsRoutedToState** (7 connections) — `tests/tui/test_app_end_to_end.py`
- **.test_three_task_starts_appear_in_tree()** (7 connections) — `tests/tui/test_live_refresh.py`
- **.test_tick_refreshes_widgets_after_event()** (7 connections) — `tests/tui/test_live_refresh.py`
- **.compose()** (6 connections) — `src/ansible_aom/tui/screens/main.py`
- **._update_elapsed_from_start()** (6 connections) — `src/ansible_aom/tui/screens/main.py`
- *... and 121 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (57 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (20 shared connections)
- [Session Replay Round Trip](Session_Replay_Round_Trip.md) (15 shared connections)
- [Inventory Auto Detection](Inventory_Auto_Detection.md) (14 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (14 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (12 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (11 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (10 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (10 shared connections)
- [View Mode Selection](View_Mode_Selection.md) (7 shared connections)
- [Terminal Display Manager](Terminal_Display_Manager.md) (5 shared connections)
- [KeyContext Enum](KeyContext_Enum.md) (5 shared connections)

## Source Files

- `src/ansible_aom/tui/app.py`
- `src/ansible_aom/tui/screens/main.py`
- `src/ansible_aom/tui/widgets/task_tree.py`
- `tests/tui/test_app_end_to_end.py`
- `tests/tui/test_live_refresh.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_interactive_prompt.py`

## Audit Trail

- EXTRACTED: 345 (47%)
- INFERRED: 390 (53%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*