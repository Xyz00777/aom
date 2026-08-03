# PTY Stream Parser

> 81 nodes · cohesion 0.03

## Key Concepts

- **create_parser()** (84 connections) — `src/ansible_aom/cli.py`
- **TestNoRedactFlag** (17 connections) — `tests/unit/test_cli.py`
- **TestConfigPathFlag** (14 connections) — `tests/unit/test_cli.py`
- **TestCaptureVerboseFlag** (13 connections) — `tests/unit/test_cli.py`
- **TestCaptureSetupFlag** (12 connections) — `tests/unit/test_cli.py`
- **TestHideDeprecationsFlag** (12 connections) — `tests/unit/test_cli.py`
- **TestHideWarningsFlag** (12 connections) — `tests/unit/test_cli.py`
- **.test_config_path_is_visible_to_config_layer_argv_lookup()** (4 connections) — `tests/unit/test_cli.py`
- **.test_inventory_flag_passed_through()** (3 connections) — `tests/unit/test_cli.py`
- **.test_limit_flag_passed_through()** (3 connections) — `tests/unit/test_cli.py`
- **.test_unknown_args_passed_through()** (3 connections) — `tests/unit/test_cli.py`
- **.test_playbook_argument_accepted()** (3 connections) — `tests/unit/test_cli.py`
- **.test_playbook_positional_argument_required()** (3 connections) — `tests/unit/test_cli.py`
- **.test_create_parser_has_playbook_positional_arg()** (3 connections) — `tests/unit/test_cli.py`
- **.test_create_parser_returns_argparse_parser()** (3 connections) — `tests/unit/test_cli.py`
- **.test_help_displays_usage()** (3 connections) — `tests/unit/test_cli.py`
- **.test_help_shows_flags()** (3 connections) — `tests/unit/test_cli.py`
- **.test_tui_flag_defaults_false()** (3 connections) — `tests/unit/test_cli.py`
- **.test_tui_flag_exists()** (3 connections) — `tests/unit/test_cli.py`
- **.test_tui_flag_works_at_start()** (3 connections) — `tests/unit/test_cli.py`
- **.test_all_flags_compose_with_each_other()** (3 connections) — `tests/unit/test_cli.py`
- **.test_yes_unchanged_from_task_5_1()** (3 connections) — `tests/unit/test_cli.py`
- **.test_short_v_does_not_set_aom_verbose()** (3 connections) — `tests/unit/test_cli.py`
- **.test_verbose_flag_defaults_false()** (3 connections) — `tests/unit/test_cli.py`
- **.test_verbose_flag_exists()** (3 connections) — `tests/unit/test_cli.py`
- *... and 56 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (43 shared connections)
- [.test_hide_state_does_not_appear_in_ansible_args](test_hide_state_does_not_appear_in_ansible_args.md) (19 shared connections)
- [.test_yes_help_text_mentions_yes](test_yes_help_text_mentions_yes.md) (6 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (6 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (6 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (6 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (6 shared connections)
- [Invalid Key Handling](Invalid_Key_Handling.md) (5 shared connections)
- [First Ctrl-C Cancellation](First_Ctrl-C_Cancellation.md) (3 shared connections)
- [Narrow Terminal View](Narrow_Terminal_View.md) (3 shared connections)
- [WarningType Enum](WarningType_Enum.md) (2 shared connections)
- [TestNoRecordParserFlag](TestNoRecordParserFlag.md) (2 shared connections)

## Source Files

- `src/ansible_aom/cli.py`
- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 139 (46%)
- INFERRED: 163 (54%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*