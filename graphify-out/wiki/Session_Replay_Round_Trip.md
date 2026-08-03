# Session Replay Round Trip

> 33 nodes · cohesion 0.11

## Key Concepts

- **test_rerun_screen.py** (11 connections) — `tests/tui/test_rerun_screen.py`
- **Path** (11 connections)
- **_write_session()** (10 connections) — `tests/tui/test_rerun_screen.py`
- **_write_events()** (9 connections) — `tests/tui/test_rerun_screen.py`
- **_render_dialog_text()** (7 connections) — `tests/tui/test_rerun_screen.py`
- **TestRerunDialogContent** (7 connections) — `tests/tui/test_rerun_screen.py`
- **TestRerunDialogStructure** (6 connections) — `tests/tui/test_rerun_screen.py`
- **.test_handles_empty_host_set()** (5 connections) — `tests/tui/test_rerun_screen.py`
- **.test_shows_failed_hosts()** (5 connections) — `tests/tui/test_rerun_screen.py`
- **.test_shows_planned_command()** (5 connections) — `tests/tui/test_rerun_screen.py`
- **.test_shows_unreachable_hosts()** (5 connections) — `tests/tui/test_rerun_screen.py`
- **TestRerunDialogDismissValues** (4 connections) — `tests/tui/test_rerun_screen.py`
- **.test_cancel_returns_false()** (4 connections) — `tests/tui/test_rerun_screen.py`
- **.test_confirm_returns_true()** (4 connections) — `tests/tui/test_rerun_screen.py`
- **TestRerunDialogPlanBuilder** (4 connections) — `tests/tui/test_rerun_screen.py`
- **.test_uses_session_store()** (4 connections) — `tests/tui/test_rerun_screen.py`
- **.test_handles_no_sessions()** (3 connections) — `tests/tui/test_rerun_screen.py`
- **TestRerunDialogLineCount** (3 connections) — `tests/tui/test_rerun_screen.py`
- **.test_rerun_module_is_substantive()** (2 connections) — `tests/tui/test_rerun_screen.py`
- **Unit tests for the TUI rerun dialog screen.  Tests cover the L2 rerun.py expansi** (1 connections) — `tests/tui/test_rerun_screen.py`
- **The dialog must return True on confirm, False on cancel.** (1 connections) — `tests/tui/test_rerun_screen.py`
- **Create a session directory with a minimal meta.json + events.jsonl.** (1 connections) — `tests/tui/test_rerun_screen.py`
- **RerunDialog should reuse the rerun/cli.py plan builder, not duplicate it.** (1 connections) — `tests/tui/test_rerun_screen.py`
- **The expansion must be substantive — not a stub.** (1 connections) — `tests/tui/test_rerun_screen.py`
- **Append events.jsonl to a session directory.** (1 connections) — `tests/tui/test_rerun_screen.py`
- *... and 8 more nodes in this community*

## Relationships

- [Frame Parameter Handling](Frame_Parameter_Handling.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (1 shared connections)

## Source Files

- `tests/tui/test_rerun_screen.py`

## Audit Trail

- EXTRACTED: 122 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*