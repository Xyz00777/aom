# Credential String Sanitization

> 28 nodes · cohesion 0.08

## Key Concepts

- **sanitize_string()** (15 connections) — `src/ansible_aom/core/redaction.py`
- **TestURLCredentialSanitization** (6 connections) — `tests/unit/test_redaction.py`
- **TestCLICredentialSanitization** (5 connections) — `tests/unit/test_redaction.py`
- **TestConfigCustomPatterns** (5 connections) — `tests/unit/test_redaction.py`
- **.test_cli_credentials_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_variant_formats()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_custom_pattern_redacts_matching_strings()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_multiple_custom_patterns()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_sanitize_string_function()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_url_credentials_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_url_encoded_password()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_url_without_credentials_unchanged()** (4 connections) — `tests/unit/test_redaction.py`
- **test_cli_credentials_are_stripped()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_url_credentials_are_stripped()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **Sanitize credentials in a single string using Layer 3 patterns.      Applies pat** (1 connections) — `src/ansible_aom/core/redaction.py`
- **URL of form scheme://user:SECRET@host/ has SECRET removed by sanitize_string.** (1 connections) — `tests/unit/test_properties_redaction.py`
- **CLI flag of form --password=SECRET has SECRET removed by sanitize_string.** (1 connections) — `tests/unit/test_properties_redaction.py`
- **Tests for TC-160: URL credential sanitization.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-160: URL credentials are sanitized.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-160 edge case: URL-encoded passwords.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-160 edge: URLs without credentials remain unchanged.** (1 connections) — `tests/unit/test_redaction.py`
- **Tests for TC-161: CLI argument credential sanitization.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-161: CLI credentials are sanitized.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-161 edge case: Variant CLI formats.** (1 connections) — `tests/unit/test_redaction.py`
- **Tests for TC-173: Config custom_patterns for string sanitization.** (1 connections) — `tests/unit/test_redaction.py`
- *... and 3 more nodes in this community*

## Relationships

- [[Secret Redaction Configuration]] (17 shared connections)
- [[Four-Layer Redaction System]] (2 shared connections)
- [[Property Based Tests]] (2 shared connections)

## Source Files

- `src/ansible_aom/core/redaction.py`
- `tests/unit/test_properties_redaction.py`
- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 60 (72%)
- INFERRED: 23 (28%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*