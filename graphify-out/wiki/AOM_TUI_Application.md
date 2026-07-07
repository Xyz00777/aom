# AOM TUI Application

> 68 nodes · cohesion 0.03

## Key Concepts

- **AOMApp** (166 connections) — `src/ansible_aom/tui/app.py`
- **TestDirtyCounter** (16 connections) — `tests/tui/test_live_refresh.py`
- **TestRunStateOwnership** (9 connections) — `tests/tui/test_app_end_to_end.py`
- **TestAOMAppInteractivePrompt** (9 connections) — `tests/unit/test_interactive_prompt.py`
- **TestAOMAppConstruction** (7 connections) — `tests/tui/test_app_end_to_end.py`
- **.test_handle_interactive_prompt_returns_answer_from_worker()** (7 connections) — `tests/tui/test_app_end_to_end.py`
- **TestWarningsAndLogsRoutedToState** (7 connections) — `tests/tui/test_app_end_to_end.py`
- **.test_worker_invokes_run_playbook()** (7 connections) — `tests/tui/test_app_end_to_end.py`
- **test_app_end_to_end.py** (6 connections) — `tests/tui/test_app_end_to_end.py`
- **TestAOMAppInteractivePromptDuringRun** (6 connections) — `tests/tui/test_app_end_to_end.py`
- **TestWorkerKickoff** (6 connections) — `tests/tui/test_app_end_to_end.py`
- **TestNoRecordTUIPlumbing** (6 connections) — `tests/unit/test_no_record.py`
- **.start()** (3 connections) — `src/ansible_aom/tui/app.py`
- **.update_state()** (3 connections) — `src/ansible_aom/tui/app.py`
- **.test_app_defaults_when_no_args()** (3 connections) — `tests/tui/test_app_end_to_end.py`
- **.test_set_definitions_stored_on_app()** (3 connections) — `tests/tui/test_app_end_to_end.py`
- **.test_set_definitions_increments_dirty()** (3 connections) — `tests/tui/test_live_refresh.py`
- **.test_writes_prompt_to_stdout_not_input_arg()** (3 connections) — `tests/unit/test_interactive_prompt.py`
- **app.py** (2 connections) — `src/ansible_aom/tui/app.py`
- **.action_toggle_debug()** (2 connections) — `src/ansible_aom/tui/app.py`
- **.handle_interactive_prompt()** (2 connections) — `src/ansible_aom/tui/app.py`
- **.handle_password_prompt()** (2 connections) — `src/ansible_aom/tui/app.py`
- **.note_pty_bytes()** (2 connections) — `src/ansible_aom/tui/app.py`
- **.note_subprocess_active()** (2 connections) — `src/ansible_aom/tui/app.py`
- **._refresh_widgets()** (2 connections) — `src/ansible_aom/tui/app.py`
- *... and 43 more nodes in this community*

## Relationships

- [[CLI Interface Tests]] (17 shared connections)
- [[Task Definition Live Refresh]] (10 shared connections)
- [[Play Definition Tree Population]] (9 shared connections)
- [[Inventory Auto Detection]] (8 shared connections)
- [[Run State Completion Recap]] (5 shared connections)
- [[CLI Main Entry Point]] (4 shared connections)
- [[Renderer Protocol Methods]] (4 shared connections)
- [[Main TUI Screen]] (3 shared connections)
- [[CLI Argument Parser]] (3 shared connections)
- [[Interactive Prompt Protocol]] (3 shared connections)
- [[No Record Flag]] (3 shared connections)
- [[Prior Run Totals Injection]] (3 shared connections)

## Source Files

- `src/ansible_aom/tui/app.py`
- `tests/tui/test_app_end_to_end.py`
- `tests/tui/test_live_refresh.py`
- `tests/unit/test_interactive_prompt.py`
- `tests/unit/test_no_record.py`

## Audit Trail

- EXTRACTED: 165 (47%)
- INFERRED: 184 (53%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*