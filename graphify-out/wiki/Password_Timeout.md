# Password Timeout

> 14 nodes · cohesion 0.14

## Key Concepts

- **TestWarningPatternsEdgeCases** (14 connections) — `tests/unit/test_warnings.py`
- **.test_empty_line_not_warning()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_json_line_not_treated_as_warning()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_mixed_warning_types()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_multiple_deprecation_warnings()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_non_warning_plaintext_added_to_plaintext_lines()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_warning_in_pre_run_prompts_phase_not_captured()** (3 connections) — `tests/unit/test_warnings.py`
- **Edge cases for warning pattern matching.** (1 connections) — `tests/unit/test_warnings.py`
- **Multiple [DEPRECATION WARNING]: lines are all classified correctly.** (1 connections) — `tests/unit/test_warnings.py`
- **Mixed WARNING and DEPRECATION lines classified correctly.** (1 connections) — `tests/unit/test_warnings.py`
- **Warnings before EXECUTION phase may not be captured.** (1 connections) — `tests/unit/test_warnings.py`
- **JSONL lines are not treated as warnings even if they contain warning text.** (1 connections) — `tests/unit/test_warnings.py`
- **Empty lines are not treated as warnings.** (1 connections) — `tests/unit/test_warnings.py`
- **Non-warning plaintext lines go to plaintext_lines, not warnings.** (1 connections) — `tests/unit/test_warnings.py`

## Relationships

- [Run State Completion Recap](Run_State_Completion_Recap.md) (7 shared connections)
- [Run State Summary Panel](Run_State_Summary_Panel.md) (2 shared connections)
- [AOM TUI Application](AOM_TUI_Application.md) (2 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)

## Source Files

- `tests/unit/test_warnings.py`

## Audit Trail

- EXTRACTED: 27 (69%)
- INFERRED: 12 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*