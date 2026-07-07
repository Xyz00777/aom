# Four-Layer Redaction System

> 19 nodes · cohesion 0.07

## Key Concepts

- **redact_dict()** (18 connections) — `src/ansible_aom/core/redaction.py`
- **should_redact()** (15 connections) — `src/ansible_aom/core/redaction.py`
- **redaction.py** (7 connections) — `src/ansible_aom/core/redaction.py`
- **TestRecursiveRedaction** (7 connections) — `tests/unit/test_redaction.py`
- **_redact_list()** (6 connections) — `src/ansible_aom/core/redaction.py`
- **.test_custom_fields_redacted()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_custom_whitelist_not_redacted()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_empty_dict_list_handling()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_max_depth_truncation()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_nested_dict_redaction()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_nested_list_with_dicts()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_redact_dict_function()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_should_redact_function()** (5 connections) — `tests/unit/test_redaction.py`
- **.test_default_whitelist_fields_not_redacted()** (5 connections) — `tests/unit/test_redaction.py`
- **TestConfigCustomFields** (4 connections) — `tests/unit/test_redaction.py`
- **TestConfigCustomWhitelist** (4 connections) — `tests/unit/test_redaction.py`
- **Layered secret redaction system (QC-002 rewrite, Phase 2 / Task 2.1).  This modu** (1 connections) — `src/ansible_aom/core/redaction.py`
- **Tests for TC-158: Recursive dict/list redaction.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-158: Exact-match secret keys at any depth are redacted.          QC-002 note:** (1 connections) — `tests/unit/test_redaction.py`

## Relationships

- [[Secret Redaction Configuration]] (25 shared connections)
- [[Credential String Sanitization]] (3 shared connections)

## Source Files

- `src/ansible_aom/core/redaction.py`
- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 77 (71%)
- INFERRED: 32 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*