# Log Filter Helpers

> 11 nodes · cohesion 0.24

## Key Concepts

- **build_verbose_lines()** (9 connections) — `src/ansible_aom/core/inspect_model.py`
- **test_inspect_model_verbose.py** (4 connections) — `tests/unit/test_inspect_model_verbose.py`
- **_connection_ids_by_task_host()** (3 connections) — `src/ansible_aom/core/inspect_model.py`
- **_connection_task_ids()** (3 connections) — `src/ansible_aom/core/inspect_model.py`
- **_session_with_verbose_events()** (3 connections) — `tests/unit/test_inspect_model_verbose.py`
- **test_build_verbose_lines_filters_by_scope()** (3 connections) — `tests/unit/test_inspect_model_verbose.py`
- **test_build_verbose_lines_ignores_unmatched_play_task_lines()** (3 connections) — `tests/unit/test_inspect_model_verbose.py`
- **Return the connection id for each (task_id, host) pair.** (1 connections) — `src/ansible_aom/core/inspect_model.py`
- **Return ``connection_id -> task_id`` mappings from connection events.** (1 connections) — `src/ansible_aom/core/inspect_model.py`
- **Build the verbose-panel body for one session and focus scope.      Scope rules a** (1 connections) — `src/ansible_aom/core/inspect_model.py`
- **Unit tests for verbose-panel session filtering.** (1 connections) — `tests/unit/test_inspect_model_verbose.py`

## Relationships

- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (4 shared connections)
- [ASCII Status Icon Fallback](ASCII_Status_Icon_Fallback.md) (1 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `tests/unit/test_inspect_model_verbose.py`

## Audit Trail

- EXTRACTED: 26 (81%)
- INFERRED: 6 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*