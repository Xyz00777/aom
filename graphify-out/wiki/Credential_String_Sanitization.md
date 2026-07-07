# Credential String Sanitization

> 15 nodes · cohesion 0.08

## Key Concepts

- **sanitize_string()** (20 connections) — `src/ansible_aom/core/redaction.py`
- **TestURLCredentialSanitization** (6 connections) — `tests/unit/test_redaction.py`
- **TestCLICredentialSanitization** (5 connections) — `tests/unit/test_redaction.py`
- **.test_cli_credentials_redacted()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_variant_formats()** (5 connections) — `tests/unit/test_redaction.py`
- **TestConfigCustomPatterns** (5 connections) — `tests/unit/test_redaction.py`
- **.test_custom_pattern_redacts_matching_strings()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_multiple_custom_patterns()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_sanitize_string_function()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_url_credentials_redacted()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_url_encoded_password()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_url_without_credentials_unchanged()** (5 connections) — `tests/unit/test_redaction.py`
- **test_cli_credentials_are_stripped()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_url_credentials_are_stripped()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **Decide whether a dict KEY should be redacted by Layers 1+2.      Order of checks** (2 connections) — `src/ansible_aom/core/redaction.py`

## Relationships

- [[Secret Redaction Configuration]] (17 shared connections)
- [[Four-Layer Redaction System]] (3 shared connections)
- [[Property Based Tests]] (2 shared connections)

## Source Files

- `src/ansible_aom/core/redaction.py`
- `tests/unit/test_properties_redaction.py`
- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 58 (69%)
- INFERRED: 26 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*