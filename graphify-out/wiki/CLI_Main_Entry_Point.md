# CLI Main Entry Point

> 34 nodes · cohesion 0.07

## Key Concepts

- **cli.py** (14 connections) — `src/ansible_aom/cli.py`
- **LiveDriver** (14 connections) — `src/ansible_aom/drivers/live.py`
- **main()** (10 connections) — `src/ansible_aom/cli.py`
- **detect_duplicate_playbook()** (8 connections) — `src/ansible_aom/cli.py`
- **test_cli_duplicate_playbook.py** (7 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **_run_compact()** (5 connections) — `src/ansible_aom/cli.py`
- **_run_tui()** (5 connections) — `src/ansible_aom/cli.py`
- **_HideStateAction** (4 connections) — `src/ansible_aom/cli.py`
- **.__call__()** (4 connections) — `src/ansible_aom/cli.py`
- **._run_playbook_worker()** (3 connections) — `src/ansible_aom/tui/app.py`
- **test_detect_duplicate_playbook_distinguishes_different_files()** (3 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_detect_duplicate_playbook_handles_path_normalisation()** (3 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_cli_limit_merge.py** (3 connections) — `tests/unit/test_cli_limit_merge.py`
- **test_live_driver_satisfies_event_source()** (3 connections) — `tests/unit/test_event_source.py`
- **__main__.py** (2 connections) — `src/ansible_aom/__main__.py`
- **live.py** (2 connections) — `src/ansible_aom/drivers/live.py`
- **.__init__()** (2 connections) — `src/ansible_aom/drivers/live.py`
- **test_detect_duplicate_playbook_finds_exact_repeat()** (2 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_detect_duplicate_playbook_handles_empty_args()** (2 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_detect_duplicate_playbook_returns_false_when_no_repeat()** (2 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **CLI entry point for AOM.  This module provides the main command-line interface f** (1 connections) — `src/ansible_aom/cli.py`
- **Spawn the streaming renderer (compact ANSI or end-of-run JSON) via a LiveDriver.** (1 connections) — `src/ansible_aom/cli.py`
- **True if `playbook` appears (path-normalised) in `ansible_args`.      Catches the** (1 connections) — `src/ansible_aom/cli.py`
- **Entry point for running AOM as a module: python -m ansible_aom.** (1 connections) — `src/ansible_aom/__main__.py`
- **.ansible_args()** (1 connections) — `src/ansible_aom/drivers/live.py`
- *... and 9 more nodes in this community*

## Relationships

- [[Inventory Auto Detection]] (4 shared connections)
- [[AOM TUI Application]] (4 shared connections)
- [[Limit Args Merging]] (3 shared connections)
- [[Session Replay Driver]] (3 shared connections)
- [[CLI Argument Parser]] (2 shared connections)
- [[Replay CLI Subcommand]] (1 shared connections)
- [[Source Hash Version]] (1 shared connections)
- [[Shell Completion Helpers]] (1 shared connections)
- [[Renderer Factory Function]] (1 shared connections)
- [[Renderer Event Protocol]] (1 shared connections)
- [[Run Config Key Normalization]] (1 shared connections)

## Source Files

- `src/ansible_aom/__main__.py`
- `src/ansible_aom/cli.py`
- `src/ansible_aom/drivers/live.py`
- `src/ansible_aom/tui/app.py`
- `tests/unit/test_cli_duplicate_playbook.py`
- `tests/unit/test_cli_limit_merge.py`
- `tests/unit/test_event_source.py`

## Audit Trail

- EXTRACTED: 94 (84%)
- INFERRED: 18 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*