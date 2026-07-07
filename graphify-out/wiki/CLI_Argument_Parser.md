# CLI Argument Parser

> 53 nodes · cohesion 0.03

## Key Concepts

- **create_parser()** (83 connections) — `src/ansible_aom/cli.py`
- **TestHideStateFlag** (29 connections) — `tests/unit/test_cli.py`
- **TestFormatFlag** (17 connections) — `tests/unit/test_cli.py`
- **TestNoRecordParserFlag** (5 connections) — `tests/unit/test_no_record.py`
- **.test_hide_state_rejects_unknown_in_comma_separated()** (4 connections) — `tests/unit/test_cli.py`
- **.test_inventory_flag_passed_through()** (3 connections) — `tests/unit/test_cli.py`
- **.test_limit_flag_passed_through()** (3 connections) — `tests/unit/test_cli.py`
- **.test_unknown_args_passed_through()** (3 connections) — `tests/unit/test_cli.py`
- **.test_playbook_argument_accepted()** (3 connections) — `tests/unit/test_cli.py`
- **.test_playbook_positional_argument_required()** (3 connections) — `tests/unit/test_cli.py`
- **.test_create_parser_has_playbook_positional_arg()** (3 connections) — `tests/unit/test_cli.py`
- **.test_create_parser_returns_argparse_parser()** (3 connections) — `tests/unit/test_cli.py`
- **.test_format_flag_does_not_appear_in_ansible_args()** (3 connections) — `tests/unit/test_cli.py`
- **.test_help_displays_usage()** (3 connections) — `tests/unit/test_cli.py`
- **.test_help_shows_flags()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_accepts_single_value()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_all_valid_values()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_case_insensitive_all_upper()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_case_insensitive_dedup()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_case_insensitive_mixed()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_case_insensitive_ok()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_comma_separated()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_default_is_empty()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_does_not_appear_in_ansible_args()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_error_includes_choices()** (3 connections) — `tests/unit/test_cli.py`
- *... and 28 more nodes in this community*

## Relationships

- [[CLI Interface Tests]] (21 shared connections)
- [[Run State Completion Recap]] (6 shared connections)
- [[AOM TUI Application]] (3 shared connections)
- [[CLI Main Entry Point]] (2 shared connections)
- [[Compact Renderer Implementation]] (2 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[JSON Renderer]] (2 shared connections)
- [[Replay CLI Subcommand]] (1 shared connections)
- [[Shell Completion Helpers]] (1 shared connections)
- [[No Record Flag]] (1 shared connections)

## Source Files

- `src/ansible_aom/cli.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_no_record.py`

## Audit Trail

- EXTRACTED: 126 (48%)
- INFERRED: 138 (52%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*