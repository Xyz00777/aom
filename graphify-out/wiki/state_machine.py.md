# state_machine.py

> 11 nodes · cohesion 0.24

## Key Concepts

- **state_machine.py** (7 connections) — `src/ansible_aom/core/state_machine.py`
- **test_parser_recap_cap.py** (7 connections) — `tests/unit/test_parser_recap_cap.py`
- **_recap_line()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **test_recap_lines_capped_at_max_log_lines()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **test_recap_lines_keeps_most_recent_when_capped()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **test_recap_lines_pin_against_constant_drift()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **Memory bounds constants for AOM.  This module previously also housed an ``Execut** (1 connections) — `src/ansible_aom/core/state_machine.py`
- **R13 — cap ``PtyStreamParser._recap_lines`` at ``MAX_LOG_LINES``.  R13 spec: the** (1 connections) — `tests/unit/test_parser_recap_cap.py`
- **R13: recap_lines must not exceed MAX_LOG_LINES.** (1 connections) — `tests/unit/test_parser_recap_cap.py`
- **R13: the retained tail must be the most-recent lines.      Same reasoning as R2'** (1 connections) — `tests/unit/test_parser_recap_cap.py`
- **R13: pin the cap value at MAX_LOG_LINES (=50000).** (1 connections) — `tests/unit/test_parser_recap_cap.py`

## Relationships

- [PtyStreamParser](PtyStreamParser.md) (3 shared connections)
- [StreamPhase](StreamPhase.md) (2 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [JSONL Event Parsing](JSONL_Event_Parsing.md) (1 shared connections)
- [test_run_state_memory_bounds.py](test_run_state_memory_bounds.py.md) (1 shared connections)
- [test_run_state_set_caps.py](test_run_state_set_caps.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/state_machine.py`
- `tests/unit/test_parser_recap_cap.py`

## Audit Trail

- EXTRACTED: 35 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*