# Inspect TUI Widget Data

> 57 nodes · cohesion 0.05

## Key Concepts

- **RedactionConfig** (24 connections)
- **should_redact()** (14 connections) — `src/ansible_aom/core/redaction.py`
- **test_redaction_layer4.py** (10 connections) — `tests/unit/test_redaction_layer4.py`
- **TestLayer2UserConfig** (8 connections) — `tests/unit/test_redaction_layer4.py`
- **TestRecurseByKeyNotValue** (8 connections) — `tests/unit/test_redaction_layer4.py`
- **redaction.py** (7 connections) — `src/ansible_aom/core/redaction.py`
- **TestLayer1ExactMatchKeys** (7 connections) — `tests/unit/test_redaction_layer4.py`
- **TestWhitelistStillWorks** (7 connections) — `tests/unit/test_redaction_layer4.py`
- **TestInvocationsLayer4StaysConsistent** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_exact_match_does_not_catch_suffix_or_prefix()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_exact_match_is_case_insensitive_on_lookup()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_qc002_exact_match_keys_redacted()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_custom_fields_extends_exact_match()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_custom_key_patterns_invalid_regex_skipped()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_custom_key_patterns_matches_suffix()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_custom_key_patterns_matches_token_suffix()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_layer2_does_not_rediscover_exact_match_keys()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_dict_recursion_redacts_nested_exact_match_keys()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_list_recursion_redacts_dict_items()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_recursion_depth_bounded()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_secret_in_value_under_safe_key_not_redacted()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_value_substring_password_not_redacted()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_config_whitelist_extends_defaults()** (4 connections) — `tests/unit/test_redaction_layer4.py`
- **default_config()** (3 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_invocation_module_args_uses_layer1()** (3 connections) — `tests/unit/test_redaction_layer4.py`
- *... and 32 more nodes in this community*

## Relationships

- [TUI Tree View Tests](TUI_Tree_View_Tests.md) (12 shared connections)
- [Rerun Round Trip Tests](Rerun_Round_Trip_Tests.md) (5 shared connections)
- [Status Bar Elements](Status_Bar_Elements.md) (5 shared connections)
- [Run State Summary Panel](Run_State_Summary_Panel.md) (5 shared connections)
- [Community 463](Community_463.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/redaction.py`
- `tests/unit/test_redaction_layer4.py`

## Audit Trail

- EXTRACTED: 161 (84%)
- INFERRED: 31 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*