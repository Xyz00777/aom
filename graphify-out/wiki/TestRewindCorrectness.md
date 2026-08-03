# TestRewindCorrectness

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestRewindCorrectness** (6 connections) — `tests/compact/test_display_ansi.py`
- **.test_multi_row_rewind_moves_up_rows_minus_one()** (3 connections) — `tests/compact/test_display_ansi.py`
- **.test_print_log_does_not_erase_line_above_single_row_status()** (3 connections) — `tests/compact/test_display_ansi.py`
- **.test_single_row_rewind_uses_carriage_return_not_F()** (3 connections) — `tests/compact/test_display_ansi.py`
- **The flow that triggered the bug: status, then print_log.** (1 connections) — `tests/compact/test_display_ansi.py`
- **The status-block rewind must land on the start of the block, not above it.** (1 connections) — `tests/compact/test_display_ansi.py`
- **For a 1-row status, rewind is a carriage return, not cursor-up.** (1 connections) — `tests/compact/test_display_ansi.py`
- **For an N-row status, cursor is on the last row, so we rewind N-1 lines.** (1 connections) — `tests/compact/test_display_ansi.py`

## Relationships

- [Display](Display.md) (4 shared connections)
- [IO](IO.md) (1 shared connections)

## Source Files

- `tests/compact/test_display_ansi.py`

## Audit Trail

- EXTRACTED: 18 (95%)
- INFERRED: 1 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*