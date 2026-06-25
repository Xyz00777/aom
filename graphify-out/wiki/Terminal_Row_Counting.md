# Terminal Row Counting

> 27 nodes · cohesion 0.11

## Key Concepts

- **_row_count()** (18 connections) — `src/ansible_aom/compact/display.py`
- **test_row_count.py** (16 connections) — `tests/compact/test_row_count.py`
- **test_row_count_ignores_ansi_escape_sequences()** (4 connections) — `tests/compact/test_row_count.py`
- **test_display_update_records_wrapped_row_count()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_ansi_long_line_still_wraps_correctly()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_blank_lines_count_as_one_row_each()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_exact_width_one_row()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_multiline_with_one_wrapping_line()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_narrow_terminal_short_text_wraps()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_trailing_newline_does_not_add_row()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_double_width_wraps_to_two_rows()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_empty_string_zero_rows()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_just_over_double_width_three_rows()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_one_over_width_wraps_to_two_rows()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_short_line_one_row()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_two_lines_two_rows()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_two_lines_with_trailing_newline()** (2 connections) — `tests/compact/test_row_count.py`
- **How many terminal rows `text` occupies at the given terminal `width`.      Each** (1 connections) — `src/ansible_aom/compact/display.py`
- **Tests for width-aware row counting (roadmap #12).  `_row_count` decides how many** (1 connections) — `tests/compact/test_row_count.py`
- **ANSI codes are excluded from the wrap calculation; visible chars     are what co** (1 connections) — `tests/compact/test_row_count.py`
- **After update() in a narrow terminal, _status_rows reflects wrapped rows.      SI** (1 connections) — `tests/compact/test_row_count.py`
- **After 'abc\\n' the cursor sits on the next row but nothing is rendered there.** (1 connections) — `tests/compact/test_row_count.py`
- **A line exactly `width` chars long fits on one row (no wrap).** (1 connections) — `tests/compact/test_row_count.py`
- **First line wraps to 2 rows, second line takes 1 row → 3 total.** (1 connections) — `tests/compact/test_row_count.py`
- **A 50-char line in a 24-col terminal wraps to ceil(50/24) = 3 rows.** (1 connections) — `tests/compact/test_row_count.py`
- *... and 2 more nodes in this community*

## Relationships

- [[Compact Display Logic]] (3 shared connections)
- [[Terminal Display Manager]] (1 shared connections)
- [[Status Bar Liveness Tests]] (1 shared connections)

## Source Files

- `src/ansible_aom/compact/display.py`
- `tests/compact/test_row_count.py`

## Audit Trail

- EXTRACTED: 53 (64%)
- INFERRED: 30 (36%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*