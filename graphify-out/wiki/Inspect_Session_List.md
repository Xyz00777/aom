# Inspect Session List

> 18 nodes · cohesion 0.12

## Key Concepts

- **list_sessions()** (15 connections) — `src/ansible_aom/session/store.py`
- **_resolve_session_id()** (12 connections) — `src/ansible_aom/rerun/cli.py`
- **TestInspectList** (8 connections) — `tests/integration/test_session.py`
- **_make_session()** (8 connections) — `tests/unit/test_rerun_cli.py`
- **TestResolveSessionId** (7 connections) — `tests/unit/test_rerun_cli.py`
- **.test_list_sessions_empty()** (5 connections) — `tests/integration/test_session.py`
- **.test_list_sessions_includes_status()** (5 connections) — `tests/integration/test_session.py`
- **.test_list_sessions_returns_all_sessions()** (5 connections) — `tests/integration/test_session.py`
- **.test_list_sessions_shows_8_char_uuid_prefix()** (5 connections) — `tests/integration/test_session.py`
- **.test_list_sessions_sorted_by_time()** (5 connections) — `tests/integration/test_session.py`
- **.test_ambiguous_short_id_raises()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_explicit_full_id_returned_as_is()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_explicit_short_id_resolved_to_full()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_omitted_returns_most_recent()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_unknown_id_raises()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_no_sessions_at_all_raises()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **Resolve an explicit session ID, short prefix, or "most recent" intent.      Mirr** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Helper: create a session directory with a minimal meta.json.** (1 connections) — `tests/unit/test_rerun_cli.py`

## Relationships

- [[Run Config Key Normalization]] (14 shared connections)
- [[Session Recording Tests]] (2 shared connections)
- [[Rerun CLI Entry]] (2 shared connections)
- [[Inspect CLI Commands]] (2 shared connections)
- [[Rerun Host Set Composition]] (2 shared connections)
- [[Playbook Event Parsing]] (1 shared connections)
- [[Session List View]] (1 shared connections)

## Source Files

- `src/ansible_aom/rerun/cli.py`
- `src/ansible_aom/session/store.py`
- `tests/integration/test_session.py`
- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 72 (72%)
- INFERRED: 28 (28%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*