# Compact Renderer Formatters

> 25 nodes · cohesion 0.16

## Key Concepts

- **Path** (15 connections)
- **_resolve_session_id()** (11 connections) — `src/ansible_aom/rerun/cli.py`
- **_make_session()** (8 connections) — `tests/unit/test_rerun_cli.py`
- **TestMain** (7 connections) — `tests/unit/test_rerun_cli.py`
- **TestResolveSessionId** (7 connections) — `tests/unit/test_rerun_cli.py`
- **_write_session_with_failure()** (6 connections) — `tests/unit/test_rerun_cli.py`
- **.test_runs_with_correct_command()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_ambiguous_short_id_raises()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_explicit_full_id_returned_as_is()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_explicit_short_id_resolved_to_full()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_omitted_returns_most_recent()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_unknown_id_raises()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_missing_ansible_args_returns_2()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_no_hosts_to_rerun_returns_nonzero()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_no_session_id_uses_latest()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_user_declines_returns_zero_without_running()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_no_sessions_at_all_raises()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_unknown_session_returns_nonzero()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **Path** (1 connections)
- **Resolve an explicit session ID, short prefix, or "most recent" intent.      Mirr** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Helper: create a session directory with a minimal meta.json.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **Helper: write a session with one failed host (web2).** (1 connections) — `tests/unit/test_rerun_cli.py`
- **Happy path: --yes --failed → run_playbook called with --limit web2.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **A session with no failures and --failed → nothing to do, exit 1.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **Old session without ansible_args field → exit 2.** (1 connections) — `tests/unit/test_rerun_cli.py`

## Relationships

- [KeyAction TypedDict](KeyAction_TypedDict.md) (4 shared connections)
- [load_session](load_session.md) (3 shared connections)
- [Shell Completion Helpers](Shell_Completion_Helpers.md) (1 shared connections)

## Source Files

- `src/ansible_aom/rerun/cli.py`
- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 102 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*