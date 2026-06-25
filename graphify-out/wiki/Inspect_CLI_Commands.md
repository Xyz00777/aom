# Inspect CLI Commands

> 60 nodes · cohesion 0.05

## Key Concepts

- **load_session()** (25 connections) — `src/ansible_aom/session/store.py`
- **find_latest_session()** (10 connections) — `src/ansible_aom/session/store.py`
- **cli.py** (9 connections) — `src/ansible_aom/inspect/cli.py`
- **store.py** (8 connections) — `src/ansible_aom/session/store.py`
- **cleanup_old_sessions()** (8 connections) — `src/ansible_aom/session/store.py`
- **inspect_debug()** (7 connections) — `src/ansible_aom/inspect/cli.py`
- **inspect_text()** (7 connections) — `src/ansible_aom/inspect/cli.py`
- **main()** (7 connections) — `src/ansible_aom/inspect/cli.py`
- **TestSessionRotation** (7 connections) — `tests/integration/test_session.py`
- **inspect_tui()** (6 connections) — `src/ansible_aom/inspect/cli.py`
- **TestCorruptedSessionHandling** (6 connections) — `tests/integration/test_session.py`
- **TestInspectShow** (6 connections) — `tests/integration/test_session.py`
- **inspect_prune()** (5 connections) — `src/ansible_aom/inspect/cli.py`
- **.test_inspect_shows_malformed_count()** (5 connections) — `tests/integration/test_session.py`
- **TestOutputFormats** (5 connections) — `tests/integration/test_session.py`
- **test_session_helpers.py** (5 connections) — `tests/unit/test_session_helpers.py`
- **_build_parser()** (4 connections) — `src/ansible_aom/inspect/cli.py`
- **.test_malformed_json_skipped_with_warning()** (4 connections) — `tests/integration/test_session.py`
- **.test_truncated_jsonl_handled_gracefully()** (4 connections) — `tests/integration/test_session.py`
- **.test_load_nonexistent_session_returns_none()** (4 connections) — `tests/integration/test_session.py`
- **.test_load_session_includes_events()** (4 connections) — `tests/integration/test_session.py`
- **.test_load_session_returns_meta()** (4 connections) — `tests/integration/test_session.py`
- **.test_json_output_format()** (4 connections) — `tests/integration/test_session.py`
- **.test_jsonl_output_format()** (4 connections) — `tests/integration/test_session.py`
- **.test_cleanup_keeps_max_count()** (4 connections) — `tests/integration/test_session.py`
- *... and 35 more nodes in this community*

## Relationships

- [[Run Config Key Normalization]] (24 shared connections)
- [[Session Recording Tests]] (10 shared connections)
- [[Three-Pane Inspect App]] (3 shared connections)
- [[Inspect Session List]] (2 shared connections)
- [[Session List View]] (2 shared connections)
- [[Session Diagnostics Writing]] (2 shared connections)
- [[Replay CLI Subcommand]] (1 shared connections)
- [[Inspect Debug Diagnostics]] (1 shared connections)
- [[Inspect Text Golden Tests]] (1 shared connections)
- [[Session Summary Creation]] (1 shared connections)
- [[Run History Mining]] (1 shared connections)
- [[UUIDv7 Session Generation]] (1 shared connections)

## Source Files

- `src/ansible_aom/inspect/cli.py`
- `src/ansible_aom/session/store.py`
- `tests/integration/test_session.py`
- `tests/unit/test_session_helpers.py`

## Audit Trail

- EXTRACTED: 157 (72%)
- INFERRED: 61 (28%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*