# Status Bar Widget

> 25 nodes · cohesion 0.14

## Key Concepts

- **find_latest_session()** (11 connections) — `src/ansible_aom/session/store.py`
- **cli.py** (9 connections) — `src/ansible_aom/inspect/cli.py`
- **inspect_debug()** (7 connections) — `src/ansible_aom/inspect/cli.py`
- **inspect_text()** (7 connections) — `src/ansible_aom/inspect/cli.py`
- **main()** (7 connections) — `src/ansible_aom/inspect/cli.py`
- **inspect_tui()** (6 connections) — `src/ansible_aom/inspect/cli.py`
- **test_session_helpers.py** (6 connections) — `tests/unit/test_session_helpers.py`
- **inspect_prune()** (5 connections) — `src/ansible_aom/inspect/cli.py`
- **Path** (5 connections)
- **_build_parser()** (4 connections) — `src/ansible_aom/inspect/cli.py`
- **Path** (4 connections)
- **test_find_latest_returns_newest()** (4 connections) — `tests/unit/test_session_helpers.py`
- **_default_state_dir()** (3 connections) — `src/ansible_aom/inspect/cli.py`
- **test_find_latest_returns_none_when_dir_missing()** (3 connections) — `tests/unit/test_session_helpers.py`
- **test_find_latest_returns_none_when_empty()** (3 connections) — `tests/unit/test_session_helpers.py`
- **_write_session()** (3 connections) — `tests/unit/test_session_helpers.py`
- **_stdout_is_tty()** (2 connections) — `src/ansible_aom/inspect/cli.py`
- **ArgumentParser** (1 connections)
- **Inspect CLI commands for AOM (rebuilt).  The CLI exposes three invocations:  * `** (1 connections) — `src/ansible_aom/inspect/cli.py`
- **Print the most-recent session as plain text. Return exit code.      When ``play_** (1 connections) — `src/ansible_aom/inspect/cli.py`
- **Launch the TUI inspector. Returns the TUI's exit code.** (1 connections) — `src/ansible_aom/inspect/cli.py`
- **Remove sessions older than ``days`` days.** (1 connections) — `src/ansible_aom/inspect/cli.py`
- **Print the diagnostics.json contents for ``session_id`` (or latest).      ``as_js** (1 connections) — `src/ansible_aom/inspect/cli.py`
- **Return the session_id of the most-recently-started session, or None.      Reuses** (1 connections) — `src/ansible_aom/session/store.py`
- **Unit tests for core.session helper functions.** (1 connections) — `tests/unit/test_session_helpers.py`

## Relationships

- [Total Task Counting](Total_Task_Counting.md) (2 shared connections)
- [Loop Item Line Tests](Loop_Item_Line_Tests.md) (2 shared connections)
- [Rerun CLI Parser](Rerun_CLI_Parser.md) (1 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (1 shared connections)
- [ASCII Status Icon Fallback](ASCII_Status_Icon_Fallback.md) (1 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (1 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (1 shared connections)
- [Event Source Adapters](Event_Source_Adapters.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `src/ansible_aom/inspect/cli.py`
- `src/ansible_aom/session/store.py`
- `tests/unit/test_session_helpers.py`

## Audit Trail

- EXTRACTED: 78 (80%)
- INFERRED: 19 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*