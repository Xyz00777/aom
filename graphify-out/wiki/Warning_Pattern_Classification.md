# Warning Pattern Classification

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestWarningClassification** (13 connections) — `tests/unit/test_warnings.py`
- **.test_deprecated_feature_classification()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_deprecation_warning_classification()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_regular_warning_classification()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_warning_with_deprecation_in_message_body()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_whitespace_before_bracket()** (3 connections) — `tests/unit/test_warnings.py`
- **TC-498, TC-499, TC-500: Warning pattern classification.** (1 connections) — `tests/unit/test_warnings.py`
- **TC-498: [DEPRECATION WARNING]: classified as WarningType.DEPRECATION.** (1 connections) — `tests/unit/test_warnings.py`
- **TC-499: [DEPRECATED]: classified as WarningType.DEPRECATION.** (1 connections) — `tests/unit/test_warnings.py`
- **TC-500: [WARNING]: classified as WarningType.WARNING.** (1 connections) — `tests/unit/test_warnings.py`
- **TC-500: [WARNING]: with 'deprecation' word in body is still WARNING type.** (1 connections) — `tests/unit/test_warnings.py`
- **TC-498: Whitespace before [DEPRECATION WARNING]: still matches.** (1 connections) — `tests/unit/test_warnings.py`

## Relationships

- [[PTY Stream Parser]] (6 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Warnings Display Config]] (1 shared connections)
- [[App Configuration Settings]] (1 shared connections)
- [[Status Bar Warning Panels]] (1 shared connections)
- [[Warning Classification Tests]] (1 shared connections)

## Source Files

- `tests/unit/test_warnings.py`

## Audit Trail

- EXTRACTED: 23 (68%)
- INFERRED: 11 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*