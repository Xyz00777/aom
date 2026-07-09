# State Transition Validation

> 25 nodes · cohesion 0.11

## Key Concepts

- **cli.py** (15 connections) — `src/ansible_aom/cli.py`
- **main()** (12 connections) — `src/ansible_aom/cli.py`
- **detect_duplicate_playbook()** (8 connections) — `src/ansible_aom/cli.py`
- **test_cli_duplicate_playbook.py** (7 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **_run_compact()** (5 connections) — `src/ansible_aom/cli.py`
- **_run_tui()** (5 connections) — `src/ansible_aom/cli.py`
- **_confirm_no_redact()** (3 connections) — `src/ansible_aom/cli.py`
- **test_detect_duplicate_playbook_distinguishes_different_files()** (3 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_detect_duplicate_playbook_handles_path_normalisation()** (3 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_cli_limit_merge.py** (3 connections) — `tests/unit/test_cli_limit_merge.py`
- **__main__.py** (2 connections) — `src/ansible_aom/__main__.py`
- **test_detect_duplicate_playbook_finds_exact_repeat()** (2 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_detect_duplicate_playbook_handles_empty_args()** (2 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_detect_duplicate_playbook_returns_false_when_no_repeat()** (2 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **CLI entry point for AOM.  This module provides the main command-line interface f** (1 connections) — `src/ansible_aom/cli.py`
- **Validate ``--no-redact`` per QC-003 (Q4=B: confirm prompt).      Returns ``(proc** (1 connections) — `src/ansible_aom/cli.py`
- **True if `playbook` appears (path-normalised) in `ansible_args`.      Catches the** (1 connections) — `src/ansible_aom/cli.py`
- **Spawn the streaming renderer (compact ANSI or end-of-run JSON) via a LiveDriver.** (1 connections) — `src/ansible_aom/cli.py`
- **Launch the Textual TUI driven by a LiveDriver.      AOMApp owns its own event lo** (1 connections) — `src/ansible_aom/cli.py`
- **Main CLI entry point.      Returns:         Exit code (0 for success, non-zero f** (1 connections) — `src/ansible_aom/cli.py`
- **Entry point for running AOM as a module: python -m ansible_aom.** (1 connections) — `src/ansible_aom/__main__.py`
- **Tests for duplicate-playbook argument detection.  When the user types `aom site.** (1 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **Multiple distinct .yml files are a legitimate ansible-playbook invocation.** (1 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **./site.yml and site.yml refer to the same file — flag the duplicate.** (1 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **Tests for merging repeated ``-l`` / ``--limit`` flags.  ansible-playbook stores** (1 connections) — `tests/unit/test_cli_limit_merge.py`

## Relationships

- [Session ID Completion](Session_ID_Completion.md) (4 shared connections)
- [Debug Diagnostics Summary](Debug_Diagnostics_Summary.md) (3 shared connections)
- [Host Status Indicators](Host_Status_Indicators.md) (3 shared connections)
- [PTY Stream Parser](PTY_Stream_Parser.md) (2 shared connections)
- [First Ctrl-C Cancellation](First_Ctrl-C_Cancellation.md) (1 shared connections)
- [Community 501](Community_501.md) (1 shared connections)
- [Community 502](Community_502.md) (1 shared connections)
- [Preflight Summary Rendering](Preflight_Summary_Rendering.md) (1 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/__main__.py`
- `src/ansible_aom/cli.py`
- `tests/unit/test_cli_duplicate_playbook.py`
- `tests/unit/test_cli_limit_merge.py`

## Audit Trail

- EXTRACTED: 66 (80%)
- INFERRED: 17 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*