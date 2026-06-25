# Terminal Display Manager

> 44 nodes · cohesion 0.06

## Key Concepts

- **Display** (73 connections) — `src/ansible_aom/compact/display.py`
- **TestDegradedModeEntry** (9 connections) — `tests/compact/test_small_terminal.py`
- **TestDegradedModeFallthrough** (7 connections) — `tests/compact/test_small_terminal.py`
- **TestSynchronizedOutput** (5 connections) — `tests/compact/test_display_ansi.py`
- **.test_terminal_cleanup_on_exit()** (4 connections) — `tests/integration/test_compact_renderer.py`
- **.test_non_tty_update_emits_no_ansi()** (3 connections) — `tests/compact/test_display_ansi.py`
- **.test_force_size_at_threshold_does_not_degrade()** (3 connections) — `tests/compact/test_small_terminal.py`
- **.test_non_tty_is_never_degraded()** (3 connections) — `tests/compact/test_small_terminal.py`
- **.test_stop_in_degraded_mode_is_a_noop()** (3 connections) — `tests/compact/test_small_terminal.py`
- **.test_non_tty_display_print_log_uses_stdout()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_non_tty_display_start_is_noop()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_non_tty_display_update_is_noop()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_non_tty_line_per_status()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_non_tty_no_continuous_elapsed_time()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_throttled_refresh_rate_max_four_per_second()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.__init__()** (2 connections) — `src/ansible_aom/compact/display.py`
- **.start()** (2 connections) — `src/ansible_aom/compact/display.py`
- **.test_update_wraps_content_in_dec_2026_sync()** (2 connections) — `tests/compact/test_display_ansi.py`
- **.test_force_size_below_threshold_enters_degraded_mode()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_force_size_below_threshold_prints_one_line_warning()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_force_size_just_below_cols_threshold_degrades()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_force_size_just_below_rows_threshold_degrades()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_clear_in_degraded_mode_is_a_noop()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_print_log_in_degraded_mode_emits_plain_text()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_update_in_degraded_mode_emits_no_dec_frame()** (2 connections) — `tests/compact/test_small_terminal.py`
- *... and 19 more nodes in this community*

## Relationships

- [[Compact Renderer Integration Tests]] (25 shared connections)
- [[Compact Display Logic]] (7 shared connections)
- [[Small Terminal Handling]] (6 shared connections)
- [[ANSI Rewind Correctness]] (5 shared connections)
- [[Terminal Resize Handling]] (5 shared connections)
- [[Compact Renderer Implementation]] (2 shared connections)
- [[Color ASCII Fallback]] (1 shared connections)
- [[Dirty Flag Throttle]] (1 shared connections)
- [[Terminal Row Counting]] (1 shared connections)
- [[Display Helper Class]] (1 shared connections)
- [[Run State Completion Recap]] (1 shared connections)
- [[Host Status Indicators]] (1 shared connections)

## Source Files

- `src/ansible_aom/compact/display.py`
- `tests/compact/test_display_ansi.py`
- `tests/compact/test_small_terminal.py`
- `tests/integration/test_compact_renderer.py`

## Audit Trail

- EXTRACTED: 83 (50%)
- INFERRED: 84 (50%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*