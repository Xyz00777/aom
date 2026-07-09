# Exit Code Constants

> 12 nodes · cohesion 0.27

## Key Concepts

- **_confirm()** (11 connections) — `src/ansible_aom/rerun/cli.py`
- **TestConfirm** (9 connections) — `tests/unit/test_rerun_cli.py`
- **.test_default_yes_on_empty_input()** (3 connections) — `tests/unit/test_rerun_cli.py`
- **.test_anything_else_rejected()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_n_rejected()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_no_rejected()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_warning_includes_idempotency_language()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_y_accepted()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_yes_accepted()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **.test_yes_flag_skips_prompt_and_returns_true()** (2 connections) — `tests/unit/test_rerun_cli.py`
- **Print the rerun plan + warning, then ask for Y/n confirmation.      Always print** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Bare Enter (empty string) accepts the default Y.** (1 connections) — `tests/unit/test_rerun_cli.py`

## Relationships

- [Shell Completion Helpers](Shell_Completion_Helpers.md) (2 shared connections)
- [KeyAction TypedDict](KeyAction_TypedDict.md) (1 shared connections)

## Source Files

- `src/ansible_aom/rerun/cli.py`
- `tests/unit/test_rerun_cli.py`

## Audit Trail

- EXTRACTED: 23 (59%)
- INFERRED: 16 (41%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*