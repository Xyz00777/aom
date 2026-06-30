# Rerun CLI Parser

> 12 nodes · cohesion 0.29

## Key Concepts

- **_create_parser()** (14 connections) — `src/ansible_aom/rerun/cli.py`
- **TestCreateParser** (10 connections) — `tests/unit/test_rerun_cli.py`
- **.test_state_dir_override()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_changes_only_flag()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_combined()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_failed_flag()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_no_args()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_session_id_positional()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_unreachable_flag()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_yes_long_form()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_yes_short_form()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **Build the argparse parser for ``aom rerun``.      Split out from ``main`` so tes** (1 connections) — `src/ansible_aom/rerun/cli.py`

## Relationships

- [[Rerun CLI Entry]] (2 shared connections)
- [[Replay CLI Subcommand]] (1 shared connections)
- [[Shell Completion Helpers]] (1 shared connections)
- [[Rerun Host Set Composition]] (1 shared connections)
- [[Run Config Key Normalization]] (1 shared connections)

## Source Files

- `src/ansible_aom/rerun/cli.py`
- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 25 (57%)
- INFERRED: 19 (43%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*