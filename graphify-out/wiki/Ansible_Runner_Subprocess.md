# Ansible Runner Subprocess

> 37 nodes · cohesion 0.08

## Key Concepts

- **_row_count()** (20 connections) — `src/ansible_aom/compact/display.py`
- **test_row_count.py** (17 connections) — `tests/compact/test_row_count.py`
- **display.py** (11 connections) — `src/ansible_aom/compact/display.py`
- **._write_frame()** (9 connections) — `src/ansible_aom/compact/display.py`
- **.print_log()** (7 connections) — `src/ansible_aom/compact/display.py`
- **_terminal_width()** (5 connections) — `src/ansible_aom/compact/display.py`
- **.flush_logs()** (3 connections) — `src/ansible_aom/compact/display.py`
- **test_display_update_records_wrapped_row_count()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_ansi_long_line_still_wraps_correctly()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_blank_lines_count_as_one_row_each()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_exact_width_one_row()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_multiline_with_one_wrapping_line()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_narrow_terminal_short_text_wraps()** (3 connections) — `tests/compact/test_row_count.py`
- **test_row_count_trailing_newline_does_not_add_row()** (3 connections) — `tests/compact/test_row_count.py`
- **check_terminal_size()** (2 connections) — `src/ansible_aom/compact/display.py`
- **One synchronized frame: pending logs, then the status block.** (2 connections) — `src/ansible_aom/compact/display.py`
- **test_row_count_double_width_wraps_to_two_rows()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_empty_string_zero_rows()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_just_over_double_width_three_rows()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_one_over_width_wraps_to_two_rows()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_short_line_one_row()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_two_lines_two_rows()** (2 connections) — `tests/compact/test_row_count.py`
- **test_row_count_two_lines_with_trailing_newline()** (2 connections) — `tests/compact/test_row_count.py`
- **Display logic for compact mode — nom-style fixed-bottom status panel.  Renders d** (1 connections) — `src/ansible_aom/compact/display.py`
- **Queue a log line for printing above the status block.          Leading-edge batc** (1 connections) — `src/ansible_aom/compact/display.py`
- *... and 12 more nodes in this community*

## Relationships

- [Ctrl-C Race Handling](Ctrl-C_Race_Handling.md) (7 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (5 shared connections)
- [Renderer Event Protocol](Renderer_Event_Protocol.md) (2 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (1 shared connections)
- [Config Loading Screen](Config_Loading_Screen.md) (1 shared connections)
- [Per-Task Timing Tests](Per-Task_Timing_Tests.md) (1 shared connections)
- [Monochrome Terminal Fallback](Monochrome_Terminal_Fallback.md) (1 shared connections)
- [Frame Parameter Handling](Frame_Parameter_Handling.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/display.py`
- `tests/compact/test_row_count.py`

## Audit Trail

- EXTRACTED: 98 (78%)
- INFERRED: 27 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*