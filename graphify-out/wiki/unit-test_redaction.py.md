# unit/test_redaction.py

> 38 nodes · cohesion 0.05

## Key Concepts

- **unit/test_redaction.py** (28 connections) — `tests/unit/test_redaction.py`
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

- [RedactionConfig](RedactionConfig.md) (13 shared connections)
- [AppConfig](AppConfig.md) (9 shared connections)
- [redact_dict](redact_dict.md) (5 shared connections)
- [redact_event](redact_event.md) (5 shared connections)
- [sanitize_string](sanitize_string.md) (3 shared connections)
- [TestRedactionAlwaysOn](TestRedactionAlwaysOn.md) (1 shared connections)
- [TestRedactionHelperFunctions](TestRedactionHelperFunctions.md) (1 shared connections)

## Source Files

- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 103 (93%)
- INFERRED: 8 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*