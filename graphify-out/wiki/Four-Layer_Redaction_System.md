# Four-Layer Redaction System

> 32 nodes · cohesion 0.07

## Key Concepts

- **redact_dict()** (16 connections) — `src/ansible_aom/core/redaction.py`
- **TestRecursiveRedaction** (7 connections) — `tests/unit/test_redaction.py`
- **redaction.py** (6 connections) — `src/ansible_aom/core/redaction.py`
- **_redact_list()** (5 connections) — `src/ansible_aom/core/redaction.py`
- **should_redact()** (5 connections) — `src/ansible_aom/core/redaction.py`
- **TestConfigCustomFields** (4 connections) — `tests/unit/test_redaction.py`
- **.test_custom_fields_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **TestConfigCustomWhitelist** (4 connections) — `tests/unit/test_redaction.py`
- **.test_custom_whitelist_not_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_empty_dict_list_handling()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_max_depth_truncation()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_nested_dict_redaction()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_nested_list_with_dicts()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_redact_dict_function()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_should_redact_function()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_default_whitelist_fields_not_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **4-layer secret redaction system for Ansible output.  This module implements the** (1 connections) — `src/ansible_aom/core/redaction.py`
- **Recursively redact a dict (Layer 2). Returns a new dict.      Args:         data** (1 connections) — `src/ansible_aom/core/redaction.py`
- **Redact items within a list, recursing on dict items.      Args:         lst: Lis** (1 connections) — `src/ansible_aom/core/redaction.py`
- **Return True if field should be redacted.      A field should be redacted if:** (1 connections) — `src/ansible_aom/core/redaction.py`
- **Tests for TC-158: Recursive dict/list redaction.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-158: Password fields at any depth are redacted.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-158: Password fields in list items are redacted.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-158 edge case: Max depth (10) truncation.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-158 edge: Empty dicts and lists handled correctly.** (1 connections) — `tests/unit/test_redaction.py`
- *... and 7 more nodes in this community*

## Relationships

- [[Secret Redaction Configuration]] (25 shared connections)
- [[Credential String Sanitization]] (2 shared connections)

## Source Files

- `src/ansible_aom/core/redaction.py`
- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 76 (77%)
- INFERRED: 23 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*