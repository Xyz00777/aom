# CLI TUI Launch Path

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestTuiLaunchPath** (5 connections) — `tests/unit/test_cli_tui_launch.py`
- **test_cli_tui_launch.py** (3 connections) — `tests/unit/test_cli_tui_launch.py`
- **TestCompactModePathUnchanged** (3 connections) — `tests/unit/test_cli_tui_launch.py`
- **.test_tui_mode_propagates_app_exit_code()** (2 connections) — `tests/unit/test_cli_tui_launch.py`
- **.test_tui_mode_returns_1_when_exit_code_missing()** (2 connections) — `tests/unit/test_cli_tui_launch.py`
- **Tests for the CLI's --tui launch path (roadmap #9 wiring).  For ``--tui`` mode,** (1 connections) — `tests/unit/test_cli_tui_launch.py`
- **--tui uses app.run() and skips the legacy run_playbook call.** (1 connections) — `tests/unit/test_cli_tui_launch.py`
- **app.exit_code → main()'s return value.** (1 connections) — `tests/unit/test_cli_tui_launch.py`
- **A quit-before-completion run has exit_code=None; cli surfaces 1.** (1 connections) — `tests/unit/test_cli_tui_launch.py`
- **The compact path must keep calling run_playbook directly.** (1 connections) — `tests/unit/test_cli_tui_launch.py`
- **.test_compact_mode_still_calls_run_playbook()** (1 connections) — `tests/unit/test_cli_tui_launch.py`
- **.test_tui_mode_calls_app_run_not_run_playbook_directly()** (1 connections) — `tests/unit/test_cli_tui_launch.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `tests/unit/test_cli_tui_launch.py`

## Audit Trail

- EXTRACTED: 22 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*