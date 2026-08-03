# _build_rerun_command

> 15 nodes · cohesion 0.18

## Key Concepts

- **_build_rerun_command()** (10 connections) — `src/ansible_aom/rerun/cli.py`
- **TestBuildRerunCommand** (7 connections) — `tests/unit/test_rerun_cli.py`
- **_strip_limit_args()** (3 connections) — `src/ansible_aom/rerun/cli.py`
- **.test_empty_host_set_raises()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_overrides_existing_limit_flag()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_overrides_limit_equals_form()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_overrides_short_l_flag()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_appends_limit_to_original_args()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_single_host_limit()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **Drop any pre-existing ``--limit`` / ``-l`` from the args list.      Handles thre** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Construct the (playbook, ansible_args) pair to spawn for the rerun.      The ses** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **A pre-existing --limit in the original args is dropped in favour of ours.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **``-l`` is the short form of ``--limit``; treat it the same.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **``--limit=hosts`` (single arg) is also dropped.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **No hosts → no rerun. Caller is expected to surface this earlier.** (1 connections) — `tests/unit/test_rerun_cli.py`

## Relationships

- [load_session](load_session.md) (3 shared connections)
- [KeyAction TypedDict](KeyAction_TypedDict.md) (1 shared connections)

## Source Files

- `src/ansible_aom/rerun/cli.py`
- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 42 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*