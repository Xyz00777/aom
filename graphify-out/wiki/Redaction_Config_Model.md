# Redaction Config Model

> 17 nodes · cohesion 0.12

## Key Concepts

- **TestRedactionConfig** (14 connections) — `tests/unit/test_config.py`
- **.test_redaction_config_all_fields_independent()** (3 connections) — `tests/unit/test_config.py`
- **.test_redaction_config_custom_fields()** (3 connections) — `tests/unit/test_config.py`
- **.test_redaction_config_custom_fields_is_list()** (3 connections) — `tests/unit/test_config.py`
- **.test_redaction_config_custom_patterns()** (3 connections) — `tests/unit/test_config.py`
- **.test_redaction_config_custom_patterns_is_list()** (3 connections) — `tests/unit/test_config.py`
- **.test_redaction_config_custom_whitelist()** (3 connections) — `tests/unit/test_config.py`
- **.test_redaction_config_default_whitelist_empty()** (3 connections) — `tests/unit/test_config.py`
- **.test_redaction_config_whitelist_is_list()** (2 connections) — `tests/unit/test_config.py`
- **Each RedactionConfig instance has independent lists.** (1 connections) — `tests/unit/test_config.py`
- **custom_fields is a list.** (1 connections) — `tests/unit/test_config.py`
- **custom_patterns is a list of dicts.** (1 connections) — `tests/unit/test_config.py`
- **Tests for RedactionConfig model - TC-170, TC-312, TC-313, TC-314.** (1 connections) — `tests/unit/test_config.py`
- **TC-170: RedactionConfig whitelist defaults to empty list.** (1 connections) — `tests/unit/test_config.py`
- **TC-312: RedactionConfig can have custom whitelist.** (1 connections) — `tests/unit/test_config.py`
- **TC-313: RedactionConfig can have custom_fields.** (1 connections) — `tests/unit/test_config.py`
- **TC-314: RedactionConfig can have custom_patterns.** (1 connections) — `tests/unit/test_config.py`

## Relationships

- [[Secret Redaction Configuration]] (9 shared connections)
- [[Status Bar Warning Panels]] (1 shared connections)
- [[Warnings Display Config]] (1 shared connections)
- [[App Configuration Settings]] (1 shared connections)
- [[App Config Model Tests]] (1 shared connections)

## Source Files

- `tests/unit/test_config.py`

## Audit Trail

- EXTRACTED: 33 (73%)
- INFERRED: 12 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*