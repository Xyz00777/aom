# Ansible Posix Availability

> 20 nodes · cohesion 0.16

## Key Concepts

- **session_id_completer()** (15 connections) — `src/ansible_aom/completion.py`
- **TestSessionIdCompleter** (7 connections) — `tests/unit/test_completion.py`
- **Path** (6 connections)
- **_build_parser()** (5 connections) — `src/ansible_aom/drivers/replay.py`
- **.test_default_state_dir_is_local_state_aom_sessions()** (5 connections) — `tests/unit/test_completion.py`
- **completion.py** (4 connections) — `src/ansible_aom/completion.py`
- **_default_state_dir()** (4 connections) — `src/ansible_aom/completion.py`
- **.test_empty_state_dir_returns_empty()** (3 connections) — `tests/unit/test_completion.py`
- **.test_filters_by_prefix()** (3 connections) — `tests/unit/test_completion.py`
- **.test_ignores_files()** (3 connections) — `tests/unit/test_completion.py`
- **.test_missing_state_dir_returns_empty()** (3 connections) — `tests/unit/test_completion.py`
- **.test_returns_session_dir_names()** (3 connections) — `tests/unit/test_completion.py`
- **Path** (2 connections)
- **Any** (1 connections)
- **Shell-completion helpers for the AOM CLI (F5).  Two responsibilities:  1. ``sess** (1 connections) — `src/ansible_aom/completion.py`
- **Resolve the default sessions directory.      Mirrors the literal used by ``inspe** (1 connections) — `src/ansible_aom/completion.py`
- **Return session IDs under ``state_dir`` whose names start with ``prefix``.      T** (1 connections) — `src/ansible_aom/completion.py`
- **ArgumentParser** (1 connections)
- **Build the ``aom replay`` argument parser.      Factored out of :func:`cli_main`** (1 connections) — `src/ansible_aom/drivers/replay.py`
- **When state_dir is not supplied the completer derives it from $HOME.** (1 connections) — `tests/unit/test_completion.py`

## Relationships

- [json.py](json.py.md) (2 shared connections)
- [test_completion.py](test_completion.py.md) (2 shared connections)
- [completion_snippet](completion_snippet.md) (1 shared connections)
- [load_session](load_session.md) (1 shared connections)
- [Shell Completion Helpers](Shell_Completion_Helpers.md) (1 shared connections)
- [cli_main](cli_main.md) (1 shared connections)

## Source Files

- `src/ansible_aom/completion.py`
- `src/ansible_aom/drivers/replay.py`
- `tests/unit/test_completion.py`

## Audit Trail

- EXTRACTED: 55 (79%)
- INFERRED: 15 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*