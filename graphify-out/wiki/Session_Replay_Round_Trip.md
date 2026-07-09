# Session Replay Round Trip

> 42 nodes · cohesion 0.09

## Key Concepts

- **RerunDialog** (27 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **test_rerun_screen.py** (11 connections) — `tests/tui/test_rerun_screen.py`
- **Path** (11 connections)
- **_write_session()** (10 connections) — `tests/tui/test_rerun_screen.py`
- **TestRerunDialogContent** (9 connections) — `tests/tui/test_rerun_screen.py`
- **_write_events()** (9 connections) — `tests/tui/test_rerun_screen.py`
- **TestRerunDialogStructure** (8 connections) — `tests/tui/test_rerun_screen.py`
- **_render_dialog_text()** (7 connections) — `tests/tui/test_rerun_screen.py`
- **.test_handles_empty_host_set()** (7 connections) — `tests/tui/test_rerun_screen.py`
- **.test_shows_failed_hosts()** (7 connections) — `tests/tui/test_rerun_screen.py`
- **.test_shows_planned_command()** (7 connections) — `tests/tui/test_rerun_screen.py`
- **.test_shows_unreachable_hosts()** (7 connections) — `tests/tui/test_rerun_screen.py`
- **TestRerunDialogDismissValues** (6 connections) — `tests/tui/test_rerun_screen.py`
- **.test_cancel_returns_false()** (6 connections) — `tests/tui/test_rerun_screen.py`
- **.test_confirm_returns_true()** (6 connections) — `tests/tui/test_rerun_screen.py`
- **TestRerunDialogPlanBuilder** (6 connections) — `tests/tui/test_rerun_screen.py`
- **.test_handles_no_sessions()** (5 connections) — `tests/tui/test_rerun_screen.py`
- **TestRerunDialogLineCount** (5 connections) — `tests/tui/test_rerun_screen.py`
- **.test_uses_session_store()** (4 connections) — `tests/tui/test_rerun_screen.py`
- **.action_rerun_with_modified_args()** (3 connections) — `src/ansible_aom/tui/app.py`
- **.action_rerun_with_same_args()** (3 connections) — `src/ansible_aom/tui/app.py`
- **.action_confirm()** (2 connections) — `src/ansible_aom/tui/screens/rerun.py`
- **.test_rerun_module_is_substantive()** (2 connections) — `tests/tui/test_rerun_screen.py`
- **.test_rerun_dialog_is_modal_screen()** (2 connections) — `tests/tui/test_rerun_screen.py`
- **Open the rerun dialog pre-set to failed hosts.          Active only after the pl** (1 connections) — `src/ansible_aom/tui/app.py`
- *... and 17 more nodes in this community*

## Relationships

- [Session Recording Tests](Session_Recording_Tests.md) (15 shared connections)
- [Crash Recovery Auto-Save](Crash_Recovery_Auto-Save.md) (5 shared connections)
- [Event Source Adapters](Event_Source_Adapters.md) (3 shared connections)
- [Frame Parameter Handling](Frame_Parameter_Handling.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Loop Item Line Tests](Loop_Item_Line_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/tui/app.py`
- `src/ansible_aom/tui/screens/rerun.py`
- `tests/tui/test_rerun_screen.py`

## Audit Trail

- EXTRACTED: 144 (77%)
- INFERRED: 44 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*