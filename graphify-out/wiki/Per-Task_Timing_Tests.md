# Per-Task Timing Tests

> 18 nodes · cohesion 0.20

## Key Concepts

- **_fresh_display()** (10 connections) — `tests/compact/test_log_flush_batching.py`
- **test_log_flush_batching.py** (9 connections) — `tests/compact/test_log_flush_batching.py`
- **_pin_window_closed()** (9 connections) — `tests/compact/test_log_flush_batching.py`
- **TestLeadingEdgeFlush** (8 connections) — `tests/compact/test_log_flush_batching.py`
- **TestDrainOnOtherFrames** (6 connections) — `tests/compact/test_log_flush_batching.py`
- **TestRendererTickFlushes** (4 connections) — `tests/compact/test_log_flush_batching.py`
- **.test_shrink_to_degraded_does_not_lose_pending_logs()** (3 connections) — `tests/compact/test_log_flush_batching.py`
- **.test_stop_drains_pending_logs()** (3 connections) — `tests/compact/test_log_flush_batching.py`
- **.test_update_drains_pending_logs_above_new_status()** (3 connections) — `tests/compact/test_log_flush_batching.py`
- **.test_buffered_lines_flush_together_in_one_frame()** (3 connections) — `tests/compact/test_log_flush_batching.py`
- **.test_flush_logs_drains_buffer()** (3 connections) — `tests/compact/test_log_flush_batching.py`
- **.test_lines_within_window_are_buffered_not_written()** (3 connections) — `tests/compact/test_log_flush_batching.py`
- **.test_tick_drains_pending_display_logs()** (3 connections) — `tests/compact/test_log_flush_batching.py`
- **.test_first_log_line_of_burst_renders_immediately()** (2 connections) — `tests/compact/test_log_flush_batching.py`
- **.test_flush_logs_is_noop_when_buffer_empty()** (2 connections) — `tests/compact/test_log_flush_batching.py`
- **Cross-event log batching — cap frame rate during event storms.  Per-event batchi** (1 connections) — `tests/compact/test_log_flush_batching.py`
- **The quiet-period tick is the backstop flush: the last lines of         a burst m** (1 connections) — `tests/compact/test_log_flush_batching.py`
- **Force 'a flush just happened' so subsequent print_log calls buffer.** (1 connections) — `tests/compact/test_log_flush_batching.py`

## Relationships

- [Display](Display.md) (6 shared connections)
- [CompactRenderer](CompactRenderer.md) (4 shared connections)
- [IO](IO.md) (2 shared connections)

## Source Files

- `tests/compact/test_log_flush_batching.py`

## Audit Trail

- EXTRACTED: 67 (91%)
- INFERRED: 7 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*