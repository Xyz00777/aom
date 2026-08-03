# Config Loading Screen

> 15 nodes · cohesion 0.13

## Key Concepts

- **TestRewindCorrectness** (6 connections) — `tests/compact/test_display_ansi.py`
- **test_display_ansi.py** (5 connections) — `tests/compact/test_display_ansi.py`
- **TestSynchronizedOutput** (5 connections) — `tests/compact/test_display_ansi.py`
- **.test_multi_row_rewind_moves_up_rows_minus_one()** (3 connections) — `tests/compact/test_display_ansi.py`
- **.test_print_log_does_not_erase_line_above_single_row_status()** (3 connections) — `tests/compact/test_display_ansi.py`
- **.test_single_row_rewind_uses_carriage_return_not_F()** (3 connections) — `tests/compact/test_display_ansi.py`
- **.test_non_tty_update_emits_no_ansi()** (3 connections) — `tests/compact/test_display_ansi.py`
- **.test_update_wraps_content_in_dec_2026_sync()** (2 connections) — `tests/compact/test_display_ansi.py`
- **Tests for nom-style ANSI rendering in compact mode.  These tests pin the new-spe** (1 connections) — `tests/compact/test_display_ansi.py`
- **The flow that triggered the bug: status, then print_log.** (1 connections) — `tests/compact/test_display_ansi.py`
- **Each Display.update() in TTY mode emits a single DEC 2026 frame.** (1 connections) — `tests/compact/test_display_ansi.py`
- **is_tty=False is the pipe/CI fallback (PQ6): never emit positioning.** (1 connections) — `tests/compact/test_display_ansi.py`
- **The status-block rewind must land on the start of the block, not above it.** (1 connections) — `tests/compact/test_display_ansi.py`
- **For a 1-row status, rewind is a carriage return, not cursor-up.** (1 connections) — `tests/compact/test_display_ansi.py`
- **For an N-row status, cursor is on the last row, so we rewind N-1 lines.** (1 connections) — `tests/compact/test_display_ansi.py`

## Relationships

- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (7 shared connections)
- [Ansible Runner Subprocess](Ansible_Runner_Subprocess.md) (1 shared connections)
- [Frame Parameter Handling](Frame_Parameter_Handling.md) (1 shared connections)

## Source Files

- `tests/compact/test_display_ansi.py`

## Audit Trail

- EXTRACTED: 35 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*