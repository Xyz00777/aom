# create_parser

> 54 nodes · cohesion 0.04

## Key Concepts

- **create_parser()** (81 connections) — `src/ansible_aom/cli.py`
- **.test_inventory_flag_passed_through()** (3 connections) — `tests/unit/test_cli.py`
- **.test_playbook_positional_argument_required()** (3 connections) — `tests/unit/test_cli.py`
- **.test_create_parser_has_playbook_positional_arg()** (3 connections) — `tests/unit/test_cli.py`
- **.test_create_parser_returns_argparse_parser()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_accepts_single_value()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_all_valid_values()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_case_insensitive_all_upper()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_case_insensitive_mixed()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_comma_separated()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_does_not_appear_in_ansible_args()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_is_repeatable()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_mixed_append_and_comma()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_rejects_unknown_in_comma_separated()** (3 connections) — `tests/unit/test_cli.py`
- **.test_yes_unchanged_from_task_5_1()** (3 connections) — `tests/unit/test_cli.py`
- **.test_verbose_flag_defaults_false()** (3 connections) — `tests/unit/test_cli.py`
- **.test_verbose_flag_exists()** (3 connections) — `tests/unit/test_cli.py`
- **.test_yes_flag_defaults_false()** (3 connections) — `tests/unit/test_cli.py`
- **.test_yes_help_text_mentions_yes()** (3 connections) — `tests/unit/test_cli.py`
- **.test_create_parser_calls_argcomplete_autocomplete()** (2 connections) — `tests/unit/test_cli.py`
- **.test_capture_setup_defaults_false()** (2 connections) — `tests/unit/test_cli.py`
- **.test_capture_setup_does_not_leak_to_ansible_args()** (2 connections) — `tests/unit/test_cli.py`
- **.test_capture_setup_long_form()** (2 connections) — `tests/unit/test_cli.py`
- **.test_help_text_documents_install_completion()** (2 connections) — `tests/unit/test_cli.py`
- **.test_hide_deprecations_defaults_false()** (2 connections) — `tests/unit/test_cli.py`
- *... and 29 more nodes in this community*

## Relationships

- [HostRunState](HostRunState.md) (34 shared connections)
- [TestConfigPathFlag](TestConfigPathFlag.md) (5 shared connections)
- [TestFormatFlag](TestFormatFlag.md) (5 shared connections)
- [TestCaptureVerboseFlag](TestCaptureVerboseFlag.md) (4 shared connections)
- [TestNoRedactFlag](TestNoRedactFlag.md) (4 shared connections)
- [WarningType Enum](WarningType_Enum.md) (2 shared connections)
- [unit/test_no_record.py](unit-test_no_record.py.md) (2 shared connections)
- [ansible_aom/cli.py](ansible_aom-cli.py.md) (1 shared connections)
- [load_session](load_session.md) (1 shared connections)
- [.test_limit_flag_passed_through](test_limit_flag_passed_through.md) (1 shared connections)
- [.test_unknown_args_passed_through](test_unknown_args_passed_through.md) (1 shared connections)
- [.test_playbook_argument_accepted](test_playbook_argument_accepted.md) (1 shared connections)

## Source Files

- `src/ansible_aom/cli.py`
- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 76 (41%)
- INFERRED: 110 (59%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*