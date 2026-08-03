# .test_hide_state_does_not_appear_in_ansible_args

> 40 nodes · cohesion 0.05

## Key Concepts

- **TestHideStateFlag** (28 connections) — `tests/unit/test_cli.py`
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
- **.test_hide_state_is_repeatable()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_mixed_append_and_comma()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_random_garbage_no_suggestion()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_rejects_unknown_in_comma_separated()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_rejects_unknown_value()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_single_comma_not_required()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_typo_error_preserves_original_token()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_typo_suggests_failed()** (3 connections) — `tests/unit/test_cli.py`
- **.test_hide_state_typo_suggests_skipped()** (3 connections) — `tests/unit/test_cli.py`
- **Tests for --hide-state flag.** (1 connections) — `tests/unit/test_cli.py`
- **No --hide-state flag → hide_state is None.** (1 connections) — `tests/unit/test_cli.py`
- **--hide-state ok sets hide_state=["ok"].** (1 connections) — `tests/unit/test_cli.py`
- **--hide-state can be specified multiple times.** (1 connections) — `tests/unit/test_cli.py`
- **Unknown state values are rejected by argparse.** (1 connections) — `tests/unit/test_cli.py`
- *... and 15 more nodes in this community*

## Relationships

- [PTY Stream Parser](PTY_Stream_Parser.md) (19 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (4 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (1 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 79 (75%)
- INFERRED: 26 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*