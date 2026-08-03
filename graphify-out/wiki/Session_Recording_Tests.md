# Session Recording Tests

> 54 nodes · cohesion 0.06

## Key Concepts

- **Event** (11 connections)
- **test_concurrent_inspect.py** (8 connections) — `tests/integration/test_concurrent_inspect.py`
- **.test_aom_inspect_during_active_writer()** (8 connections) — `tests/integration/test_concurrent_inspect.py`
- **.test_load_session_during_active_writer_does_not_raise()** (8 connections) — `tests/integration/test_concurrent_inspect.py`
- **TestRunStateOwnership** (8 connections) — `tests/tui/test_app_end_to_end.py`
- **test_app_end_to_end.py** (7 connections) — `tests/tui/test_app_end_to_end.py`
- **Path** (6 connections)
- **_read_snapshot()** (6 connections) — `tests/integration/test_concurrent_inspect.py`
- **_writer_thread()** (6 connections) — `tests/integration/test_concurrent_inspect.py`
- **TestAOMAppConstruction** (6 connections) — `tests/tui/test_app_end_to_end.py`
- **TestWarningsAndLogsRoutedToState** (6 connections) — `tests/tui/test_app_end_to_end.py`
- **MonkeyPatch** (6 connections)
- **Path** (6 connections)
- **_build_session()** (5 connections) — `tests/integration/test_concurrent_inspect.py`
- **TestAOMAppInteractivePromptDuringRun** (5 connections) — `tests/tui/test_app_end_to_end.py`
- **TestWorkerKickoff** (5 connections) — `tests/tui/test_app_end_to_end.py`
- **_run_aom_inspect()** (4 connections) — `tests/integration/test_concurrent_inspect.py`
- **.test_handle_interactive_prompt_returns_answer_from_worker()** (4 connections) — `tests/tui/test_app_end_to_end.py`
- **.test_worker_invokes_run_playbook()** (4 connections) — `tests/tui/test_app_end_to_end.py`
- **.test_add_warning_from_worker_lands_on_status_bar()** (4 connections) — `tests/tui/test_live_refresh.py`
- **.test_completion_nonzero_marks_title_with_cross()** (4 connections) — `tests/tui/test_live_refresh.py`
- **.test_completion_zero_marks_title_with_check()** (4 connections) — `tests/tui/test_live_refresh.py`
- **.test_three_task_starts_appear_in_tree()** (4 connections) — `tests/tui/test_live_refresh.py`
- **.test_tick_drains_pending_log_lines()** (4 connections) — `tests/tui/test_live_refresh.py`
- **.test_tick_refreshes_widgets_after_event()** (4 connections) — `tests/tui/test_live_refresh.py`
- *... and 29 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (12 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (6 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Include Role Discovery](Include_Role_Discovery.md) (1 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)

## Source Files

- `tests/integration/test_concurrent_inspect.py`
- `tests/tui/test_app_end_to_end.py`
- `tests/tui/test_live_refresh.py`

## Audit Trail

- EXTRACTED: 148 (82%)
- INFERRED: 33 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*