# TestRedactionHelperFunctions

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestRedactionHelperFunctions** (7 connections) — `tests/unit/test_redaction.py`
- **.test_redact_dict_function()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_redact_event_function()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_sanitize_string_function()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_should_redact_function()** (4 connections) — `tests/unit/test_redaction.py`
- **redact_dict() recursively redacts password fields.** (1 connections) — `tests/unit/test_redaction.py`
- **sanitize_string() removes credentials from strings.** (1 connections) — `tests/unit/test_redaction.py`
- **redact_event() applies all redaction layers to event.** (1 connections) — `tests/unit/test_redaction.py`
- **Tests for helper functions in redaction module.** (1 connections) — `tests/unit/test_redaction.py`
- **should_redact() correctly identifies redactable fields.          QC-002: only La** (1 connections) — `tests/unit/test_redaction.py`

## Relationships

- [RedactionConfig](RedactionConfig.md) (5 shared connections)
- [AppConfig](AppConfig.md) (1 shared connections)
- [unit/test_redaction.py](unit-test_redaction.py.md) (1 shared connections)
- [redact_dict](redact_dict.md) (1 shared connections)
- [redact_event](redact_event.md) (1 shared connections)
- [sanitize_string](sanitize_string.md) (1 shared connections)

## Source Files

- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 27 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*