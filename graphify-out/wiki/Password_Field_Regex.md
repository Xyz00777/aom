# Password Field Regex

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestPASSWORDMatch** (5 connections) — `tests/unit/test_redaction.py`
- **.test_false_positives_handled()** (2 connections) — `tests/unit/test_redaction.py`
- **.test_matches_password_variants()** (2 connections) — `tests/unit/test_redaction.py`
- **Tests for TC-155: PASSWORD_MATCH regex pattern matching.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-155: Regex matches known password field name variants.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-155 edge case: Fields containing 'pass' that match regex but aren't passwords** (1 connections) — `tests/unit/test_redaction.py`

## Relationships

- [[Secret Redaction Configuration]] (2 shared connections)

## Source Files

- `tests/unit/test_redaction.py`

## Audit Trail

- EXTRACTED: 11 (92%)
- INFERRED: 1 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*