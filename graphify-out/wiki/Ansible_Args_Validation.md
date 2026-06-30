# Ansible Args Validation

> 10 nodes · cohesion 0.29

## Key Concepts

- **_require_ansible_args()** (8 connections) — `src/ansible_aom/rerun/cli.py`
- **TestRequireAnsibleArgs** (6 connections) — `tests/unit/test_rerun_cli.py`
- **.test_none_value_treated_as_missing()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_session_with_empty_args_returns_empty_list()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_missing_field_error_message_explains_schema()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_missing_field_raises_with_clear_error()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_session_with_args_returns_them()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **Return the recorded ``ansible_args`` or refuse with a clear error.      Sessions** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **An explicit [] is valid — the user originally ran `aom site.yml`.** (1 connections) — `tests/unit/test_rerun_cli.py`
- **A null value (rare, but possible if hand-edited) is also missing.** (1 connections) — `tests/unit/test_rerun_cli.py`

## Relationships

- [[Rerun CLI Entry]] (2 shared connections)
- [[Rerun Host Set Composition]] (1 shared connections)

## Source Files

- `src/ansible_aom/rerun/cli.py`
- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 19 (66%)
- INFERRED: 10 (34%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*