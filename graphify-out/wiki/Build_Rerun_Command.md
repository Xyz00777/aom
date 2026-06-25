# Build Rerun Command

> 11 nodes · cohesion 0.18

## Key Concepts

- **TestBuildRerunCommand** (7 connections) — `tests/unit/test_rerun_cli.py`
- **.test_empty_host_set_raises()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_overrides_existing_limit_flag()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_overrides_limit_equals_form()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_overrides_short_l_flag()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **A pre-existing --limit in the original args is dropped in favour of ours.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **``-l`` is the short form of ``--limit``; treat it the same.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **``--limit=hosts`` (single arg) is also dropped.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **No hosts → no rerun. Caller is expected to surface this earlier.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **.test_appends_limit_to_original_args()** (1 connections) — `tests/unit/test_rerun_cli.py`
- **.test_single_host_limit()** (1 connections) — `tests/unit/test_rerun_cli.py`

## Relationships

- [[Rerun Host Set Composition]] (1 shared connections)

## Source Files

- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 21 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*