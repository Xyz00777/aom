# Rerun Host Set Composition

> 14 nodes · cohesion 0.32

## Key Concepts

- **_compose_host_set()** (13 connections) — `src/ansible_aom/rerun/cli.py`
- **test_rerun_cli.py** (11 connections) — `tests/unit/test_rerun_cli.py`
- **TestComposeHostSet** (8 connections) — `tests/unit/test_rerun_cli.py`
- **_session_dict()** (7 connections) — `tests/unit/test_rerun_cli.py`
- **._events()** (6 connections) — `tests/unit/test_rerun_cli.py`
- **.test_unreachable_flag_includes_failed_and_unreachable()** (5 connections) — `tests/unit/test_rerun_cli.py`
- **.test_changes_only_returns_changed_hosts()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_combined_flags_union()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_default_no_flag_returns_failed_only()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_failed_flag_returns_failed_hosts()** (4 connections) — `tests/unit/test_rerun_cli.py`
- **.test_no_matching_hosts_returns_empty()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **Combine the requested host categories into a single set.      Semantics (from th** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Unit tests for the aom rerun subcommand.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **--unreachable is a strict superset of --failed (per spec).** (1 connections) — `tests/unit/test_rerun_cli.py`

## Relationships

- [[Rerun CLI Entry]] (2 shared connections)
- [[Host Collection Helpers]] (2 shared connections)
- [[Inspect Session List]] (2 shared connections)
- [[Rerun Main Function]] (2 shared connections)
- [[Failed Host Collection]] (1 shared connections)
- [[Build Rerun Command]] (1 shared connections)
- [[Rerun Confirmation Prompt]] (1 shared connections)
- [[Rerun CLI Parser]] (1 shared connections)
- [[Ansible Args Validation]] (1 shared connections)

## Source Files

- `src/ansible_aom/rerun/cli.py`
- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 56 (78%)
- INFERRED: 16 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*