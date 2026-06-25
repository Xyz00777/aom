# Rerun Main Function

> 12 nodes · cohesion 0.20

## Key Concepts

- **TestMain** (7 connections) — `tests/unit/test_rerun_cli.py`
- **_write_session_with_failure()** (6 connections) — `tests/unit/test_rerun_cli.py`
- **.test_runs_with_correct_command()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_missing_ansible_args_returns_2()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_no_hosts_to_rerun_returns_nonzero()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_no_session_id_uses_latest()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_user_declines_returns_zero_without_running()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_unknown_session_returns_nonzero()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **Helper: write a session with one failed host (web2).** (1 connections) — `tests/unit/test_rerun_cli.py`
- **Happy path: --yes --failed → run_playbook called with --limit web2.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **A session with no failures and --failed → nothing to do, exit 1.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **Old session without ansible_args field → exit 2.** (1 connections) — `tests/unit/test_rerun_cli.py`

## Relationships

- [[Run Config Key Normalization]] (7 shared connections)
- [[Rerun Host Set Composition]] (2 shared connections)

## Source Files

- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 35 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*