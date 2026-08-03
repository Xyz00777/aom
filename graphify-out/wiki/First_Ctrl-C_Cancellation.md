# First Ctrl-C Cancellation

> 32 nodes · cohesion 0.07

## Key Concepts

- **ansible_aom/cli.py** (26 connections) — `src/ansible_aom/cli.py`
- **main()** (18 connections) — `src/ansible_aom/cli.py`
- **source_hash()** (7 connections) — `src/ansible_aom/__init__.py`
- **_run_compact()** (6 connections) — `src/ansible_aom/cli.py`
- **ansible_aom/__init__.py** (5 connections) — `src/ansible_aom/__init__.py`
- **test_publication_docs.py** (5 connections) — `tests/unit/test_publication_docs.py`
- **_compute_source_hash()** (4 connections) — `src/ansible_aom/__init__.py`
- **_confirm_no_redact()** (3 connections) — `src/ansible_aom/cli.py`
- **set_debug()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **__main__.py** (3 connections) — `src/ansible_aom/__main__.py`
- **test_cli_limit_merge.py** (3 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_cli_version_includes_source_hash()** (3 connections) — `tests/unit/test_cli.py`
- **.test_source_hash_changes_when_source_changes()** (3 connections) — `tests/unit/test_cli.py`
- **.test_source_hash_is_short_stable_hex()** (3 connections) — `tests/unit/test_cli.py`
- **test_current_specification_and_help_when_reading_runtime_guidance()** (2 connections) — `tests/unit/test_publication_docs.py`
- **OutputFormat** (1 connections)
- **CLI entry point for AOM.  This module provides the main command-line interface f** (1 connections) — `src/ansible_aom/cli.py`
- **Validate ``--no-redact`` per QC-003 (Q4=B: confirm prompt).      Returns ``(proc** (1 connections) — `src/ansible_aom/cli.py`
- **Spawn the streaming renderer (compact ANSI or end-of-run JSON) via a LiveDriver.** (1 connections) — `src/ansible_aom/cli.py`
- **Main CLI entry point.      Returns:         Exit code (0 for success, non-zero f** (1 connections) — `src/ansible_aom/cli.py`
- **Enable/disable debug mode programmatically.      Called by cli.py when the --ver** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **AOM (Ansible Output Monitor) - nom-style terminal interface for ansible-playbook** (1 connections) — `src/ansible_aom/__init__.py`
- **Short stable hash of every .py source file under the package.      Companion to** (1 connections) — `src/ansible_aom/__init__.py`
- **Public wrapper for ``_compute_source_hash``. Cached on first call.** (1 connections) — `src/ansible_aom/__init__.py`
- **Entry point for running AOM as a module: python -m ansible_aom.** (1 connections) — `src/ansible_aom/__main__.py`
- *... and 7 more nodes in this community*

## Relationships

- [Session ID Completion](Session_ID_Completion.md) (4 shared connections)
- [PTY Stream Parser](PTY_Stream_Parser.md) (3 shared connections)
- [State Transition Validation](State_Transition_Validation.md) (3 shared connections)
- [Host Status Indicators](Host_Status_Indicators.md) (3 shared connections)
- [Loop Item Stream Tests](Loop_Item_Stream_Tests.md) (3 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (3 shared connections)
- [Version String Parsing](Version_String_Parsing.md) (2 shared connections)
- [Auto Version Bump Hook](Auto_Version_Bump_Hook.md) (2 shared connections)
- [Debug Diagnostics Summary](Debug_Diagnostics_Summary.md) (2 shared connections)
- [State Machine Happy Path](State_Machine_Happy_Path.md) (2 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (2 shared connections)
- [Preflight Summary Rendering](Preflight_Summary_Rendering.md) (2 shared connections)

## Source Files

- `src/ansible_aom/__init__.py`
- `src/ansible_aom/__main__.py`
- `src/ansible_aom/cli.py`
- `src/ansible_aom/core/diagnostics.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_cli_limit_merge.py`
- `tests/unit/test_publication_docs.py`

## Audit Trail

- EXTRACTED: 99 (89%)
- INFERRED: 12 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*