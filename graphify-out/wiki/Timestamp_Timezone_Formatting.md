# Timestamp Timezone Formatting

> 38 nodes · cohesion 0.05

## Key Concepts

- **test_redaction.py** (26 connections) — `tests/unit/test_redaction.py`
- **TestPASSWORDMatch** (5 connections) — `tests/unit/test_redaction.py`
- **TestAnsiblePasswordFields** (4 connections) — `tests/unit/test_redaction.py`
- **TestGenericSecretFields** (4 connections) — `tests/unit/test_redaction.py`
- **TestRedactionInCompactDisplay** (4 connections) — `tests/unit/test_redaction.py`
- **.test_password_shows_asterisks_in_log()** (4 connections) — `tests/unit/test_redaction.py`
- **TestRedactionInInspectOutput** (4 connections) — `tests/unit/test_redaction.py`
- **.test_inspect_shows_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **TestRedactionInJSONOutput** (4 connections) — `tests/unit/test_redaction.py`
- **.test_json_output_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **TestRedactionInSessionArtifacts** (4 connections) — `tests/unit/test_redaction.py`
- **.test_artifact_file_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **TestRedactionInTUIDisplay** (4 connections) — `tests/unit/test_redaction.py`
- **.test_all_panels_show_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **default_config()** (3 connections) — `tests/unit/test_redaction.py`
- **.test_ansible_fields_redacted()** (2 connections) — `tests/unit/test_redaction.py`
- **.test_generic_secret_fields_redacted()** (2 connections) — `tests/unit/test_redaction.py`
- **.test_false_positives_handled()** (2 connections) — `tests/unit/test_redaction.py`
- **.test_matches_password_variants()** (2 connections) — `tests/unit/test_redaction.py`
- **Comprehensive unit tests for password/secret redaction.  This module tests the 4** (1 connections) — `tests/unit/test_redaction.py`
- **Tests for TC-155: PASSWORD_MATCH regex pattern matching.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-155: Regex matches known password field name variants.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-155 edge case: Fields containing 'pass' that match regex but aren't passwords** (1 connections) — `tests/unit/test_redaction.py`
- **Tests for TC-156: ANSIBLE_PASSWORD_FIELDS set.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-156: All Ansible connection password fields are redacted.** (1 connections) — `tests/unit/test_redaction.py`
- *... and 13 more nodes in this community*

## Relationships

- [Warnings Display Config](Warnings_Display_Config.md) (12 shared connections)
- [Run State Summary Panel](Run_State_Summary_Panel.md) (8 shared connections)
- [Rerun Round Trip Tests](Rerun_Round_Trip_Tests.md) (5 shared connections)
- [TUI Tree View Tests](TUI_Tree_View_Tests.md) (5 shared connections)
- [Status Bar Elements](Status_Bar_Elements.md) (3 shared connections)
- [Community 572](Community_572.md) (1 shared connections)
- [Community 463](Community_463.md) (1 shared connections)

## Source Files

- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 96 (88%)
- INFERRED: 13 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*