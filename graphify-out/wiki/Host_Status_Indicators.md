# Host Status Indicators

> 18 nodes · cohesion 0.20

## Key Concepts

- **merge_limit_args()** (18 connections) — `src/ansible_aom/cli.py`
- **TestMergeLimitArgs** (16 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_comma_value_combined_with_single_value()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_does_not_dedupe_intentionally()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_equals_form_merged()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_merged_flag_lives_at_first_limit_position()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_mixed_short_and_long_uses_first_form()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_no_limit_args_unchanged()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_preserves_surrounding_args()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_single_long_equals_form_unchanged()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_single_long_limit_unchanged()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_single_short_limit_unchanged()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_three_flags_merged()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_trailing_lone_short_flag_is_left_alone()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_trailing_lone_short_flag_with_one_preceding_pair()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_two_long_flags_merged()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **.test_two_short_flags_merged()** (2 connections) — `tests/unit/test_cli_limit_merge.py`
- **Collapse repeated ``-l`` / ``--limit`` flags into a single comma-joined one.** (1 connections) — `src/ansible_aom/cli.py`

## Relationships

- [First Ctrl-C Cancellation](First_Ctrl-C_Cancellation.md) (3 shared connections)

## Source Files

- `src/ansible_aom/cli.py`
- `tests/unit/test_cli_limit_merge.py`

## Audit Trail

- EXTRACTED: 35 (54%)
- INFERRED: 30 (46%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*