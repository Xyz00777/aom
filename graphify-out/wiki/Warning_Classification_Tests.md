# Warning Classification Tests

> 30 nodes · cohesion 0.07

## Key Concepts

- **TestWarningPatternsEdgeCases** (14 connections) — `tests/unit/test_warnings.py`
- **test_warnings.py** (11 connections) — `tests/unit/test_warnings.py`
- **TestWarningEntrySourceField** (11 connections) — `tests/unit/test_warnings.py`
- **TestWarningEntryTimestamp** (10 connections) — `tests/unit/test_warnings.py`
- **.test_source_field_can_be_set()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_source_field_controller_for_pty_warnings()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_source_field_empty_string_default()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_timestamp_captured_on_creation()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_timestamp_is_datetime_or_none()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_empty_line_not_warning()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_json_line_not_treated_as_warning()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_mixed_warning_types()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_multiple_deprecation_warnings()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_non_warning_plaintext_added_to_plaintext_lines()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_warning_in_pre_run_prompts_phase_not_captured()** (3 connections) — `tests/unit/test_warnings.py`
- **Unit tests for warning classification and filtering (v1.8).  Covers TEST_SPECIFI** (1 connections) — `tests/unit/test_warnings.py`
- **TC-502: WarningEntry source field for PTY stream.** (1 connections) — `tests/unit/test_warnings.py`
- **TC-502: WarningEntry from PtyStreamParser has source='controller'.** (1 connections) — `tests/unit/test_warnings.py`
- **TC-502: WarningEntry source defaults to empty string if not provided.** (1 connections) — `tests/unit/test_warnings.py`
- **TC-502: WarningEntry source can be explicitly set.** (1 connections) — `tests/unit/test_warnings.py`
- **TC-503: WarningEntry timestamp from PTY stream.** (1 connections) — `tests/unit/test_warnings.py`
- **TC-503: WarningEntry captures timestamp when created.** (1 connections) — `tests/unit/test_warnings.py`
- **TC-503: Timestamp is either datetime or None.** (1 connections) — `tests/unit/test_warnings.py`
- **Edge cases for warning pattern matching.** (1 connections) — `tests/unit/test_warnings.py`
- **Multiple [DEPRECATION WARNING]: lines are all classified correctly.** (1 connections) — `tests/unit/test_warnings.py`
- *... and 5 more nodes in this community*

## Relationships

- [[PTY Stream Parser]] (12 shared connections)
- [[Role Group Task Models]] (6 shared connections)
- [[Status Bar Warning Panels]] (5 shared connections)
- [[Warnings Display Config]] (4 shared connections)
- [[App Configuration Settings]] (4 shared connections)
- [[Run History Mining]] (1 shared connections)
- [[Parser Warnings List]] (1 shared connections)
- [[Warning Pattern Classification]] (1 shared connections)
- [[WarningEntry Dataclass]] (1 shared connections)
- [[WarningType Enum]] (1 shared connections)

## Source Files

- `tests/unit/test_warnings.py`

## Audit Trail

- EXTRACTED: 65 (69%)
- INFERRED: 29 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*