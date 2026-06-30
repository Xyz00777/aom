# Per-Task Timing Tests

> 32 nodes · cohesion 0.16

## Key Concepts

- **_renderer()** (18 connections) — `tests/compact/test_per_task_timing.py`
- **_logged()** (15 connections) — `tests/compact/test_per_task_timing.py`
- **_task_start()** (12 connections) — `tests/compact/test_per_task_timing.py`
- **test_per_task_timing.py** (10 connections) — `tests/compact/test_per_task_timing.py`
- **_runner_ok()** (9 connections) — `tests/compact/test_per_task_timing.py`
- **TestPreviousTaskSummary** (9 connections) — `tests/compact/test_per_task_timing.py`
- **TestInlineDuration** (8 connections) — `tests/compact/test_per_task_timing.py`
- **.test_summary_drops_duration_for_single_host_task()** (6 connections) — `tests/compact/test_per_task_timing.py`
- **.test_summary_emitted_on_stats_for_final_task()** (6 connections) — `tests/compact/test_per_task_timing.py`
- **.test_summary_keeps_duration_for_multi_host_task()** (6 connections) — `tests/compact/test_per_task_timing.py`
- **TestFormatDuration** (5 connections) — `tests/compact/test_per_task_timing.py`
- **.test_changed_line_carries_duration()** (5 connections) — `tests/compact/test_per_task_timing.py`
- **.test_failed_line_carries_duration_before_msg()** (5 connections) — `tests/compact/test_per_task_timing.py`
- **.test_long_duration_renders_compact()** (5 connections) — `tests/compact/test_per_task_timing.py`
- **.test_ok_line_carries_seconds_duration()** (5 connections) — `tests/compact/test_per_task_timing.py`
- **.test_unknown_task_uuid_drops_duration_suffix()** (5 connections) — `tests/compact/test_per_task_timing.py`
- **.test_no_summary_when_no_prior_task()** (5 connections) — `tests/compact/test_per_task_timing.py`
- **.test_summary_contains_task_duration_when_no_per_host_duration()** (5 connections) — `tests/compact/test_per_task_timing.py`
- **.test_summary_line_lands_before_next_task_header()** (5 connections) — `tests/compact/test_per_task_timing.py`
- **.test_missing_timestamp_drops_duration_suffix()** (4 connections) — `tests/compact/test_per_task_timing.py`
- **.test_summary_contains_cumulative()** (3 connections) — `tests/compact/test_per_task_timing.py`
- **_runner_failed()** (2 connections) — `tests/compact/test_per_task_timing.py`
- **_stats()** (2 connections) — `tests/compact/test_per_task_timing.py`
- **.test_hour_range()** (2 connections) — `tests/compact/test_per_task_timing.py`
- **.test_minute_range()** (2 connections) — `tests/compact/test_per_task_timing.py`
- *... and 7 more nodes in this community*

## Relationships

- [[Compact Renderer Implementation]] (5 shared connections)

## Source Files

- `tests/compact/test_per_task_timing.py`

## Audit Trail

- EXTRACTED: 164 (98%)
- INFERRED: 3 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*