# Per-Task Overhead Analysis

> 64 nodes · cohesion 0.06

## Key Concepts

- **analyze_overhead()** (20 connections) — `src/ansible_aom/core/overhead.py`
- **OverheadStats** (19 connections) — `src/ansible_aom/core/overhead.py`
- **format_overhead_section()** (14 connections) — `src/ansible_aom/inspect/formatters.py`
- **test_overhead.py** (14 connections) — `tests/unit/test_overhead.py`
- **_runner_ok()** (12 connections) — `tests/unit/test_overhead.py`
- **_task_start()** (11 connections) — `tests/unit/test_overhead.py`
- **_stats()** (10 connections) — `tests/unit/test_overhead_display.py`
- **.test_all_runner_result_types_count()** (8 connections) — `tests/unit/test_overhead.py`
- **TestFullStats** (7 connections) — `tests/unit/test_overhead_display.py`
- **.test_overhead_share_clamped_to_one()** (7 connections) — `tests/unit/test_overhead.py`
- **test_overhead_display.py** (6 connections) — `tests/unit/test_overhead_display.py`
- **TestEmptyAndDegenerate** (6 connections) — `tests/unit/test_overhead.py`
- **TestWallClockAndShare** (6 connections) — `tests/unit/test_overhead.py`
- **.test_overhead_share_is_ratio()** (6 connections) — `tests/unit/test_overhead.py`
- **.test_wall_clock_from_start_and_stats()** (6 connections) — `tests/unit/test_overhead.py`
- **overhead.py** (5 connections) — `src/ansible_aom/core/overhead.py`
- **_parse_iso8601()** (5 connections) — `src/ansible_aom/core/overhead.py`
- **TestFormatting** (5 connections) — `tests/unit/test_overhead_display.py`
- **_playbook_start()** (5 connections) — `tests/unit/test_overhead.py`
- **.test_floor_is_p25_of_durations()** (5 connections) — `tests/unit/test_overhead.py`
- **.test_insufficient_samples()** (5 connections) — `tests/unit/test_overhead.py`
- **.test_skips_negative_durations()** (5 connections) — `tests/unit/test_overhead.py`
- **.test_estimated_overhead_uses_distinct_task_count()** (5 connections) — `tests/unit/test_overhead.py`
- **formatters.py** (4 connections) — `src/ansible_aom/inspect/formatters.py`
- **_stats()** (4 connections) — `tests/unit/test_overhead.py`
- *... and 39 more nodes in this community*

## Relationships

- [[Playbook Event Parsing]] (1 shared connections)
- [[Inspect Debug Diagnostics]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/overhead.py`
- `src/ansible_aom/inspect/formatters.py`
- `tests/unit/test_overhead.py`
- `tests/unit/test_overhead_display.py`

## Audit Trail

- EXTRACTED: 222 (76%)
- INFERRED: 70 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*