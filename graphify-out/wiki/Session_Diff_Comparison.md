# Session Diff Comparison

> 9 nodes · cohesion 0.31

## Key Concepts

- **test_parser_recap_cap.py** (7 connections) — `tests/unit/test_parser_recap_cap.py`
- **_recap_line()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **test_recap_lines_capped_at_max_log_lines()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **test_recap_lines_keeps_most_recent_when_capped()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **test_recap_lines_pin_against_constant_drift()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **R13 — cap ``PtyStreamParser._recap_lines`` at ``MAX_LOG_LINES``.  R13 spec: the** (1 connections) — `tests/unit/test_parser_recap_cap.py`
- **R13: recap_lines must not exceed MAX_LOG_LINES.** (1 connections) — `tests/unit/test_parser_recap_cap.py`
- **R13: the retained tail must be the most-recent lines.      Same reasoning as R2'** (1 connections) — `tests/unit/test_parser_recap_cap.py`
- **R13: pin the cap value at MAX_LOG_LINES (=50000).** (1 connections) — `tests/unit/test_parser_recap_cap.py`

## Relationships

- [Run State Completion Recap](Run_State_Completion_Recap.md) (3 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [TUI Screens Module](TUI_Screens_Module.md) (1 shared connections)

## Source Files

- `tests/unit/test_parser_recap_cap.py`

## Audit Trail

- EXTRACTED: 24 (89%)
- INFERRED: 3 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*