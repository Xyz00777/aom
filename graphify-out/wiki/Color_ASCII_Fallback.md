# Color ASCII Fallback

> 82 nodes · cohesion 0.05

## Key Concepts

- **OverheadStats** (20 connections) — `src/ansible_aom/core/overhead.py`
- **analyze_overhead()** (19 connections) — `src/ansible_aom/core/overhead.py`
- **test_inspect_debug.py** (17 connections) — `tests/unit/test_inspect_debug.py`
- **test_overhead.py** (15 connections) — `tests/unit/test_overhead.py`
- **format_overhead_section()** (14 connections) — `src/ansible_aom/inspect/formatters.py`
- **_runner_ok()** (12 connections) — `tests/unit/test_overhead.py`
- **_task_start()** (11 connections) — `tests/unit/test_overhead.py`
- **_stats()** (10 connections) — `tests/unit/test_overhead_display.py`
- **formatters.py** (9 connections) — `src/ansible_aom/inspect/formatters.py`
- **format_diagnostics_section()** (8 connections) — `src/ansible_aom/inspect/formatters.py`
- **test_overhead_display.py** (8 connections) — `tests/unit/test_overhead_display.py`
- **.test_all_runner_result_types_count()** (8 connections) — `tests/unit/test_overhead.py`
- **Path** (7 connections)
- **_write_session()** (7 connections) — `tests/unit/test_inspect_debug.py`
- **TestFullStats** (7 connections) — `tests/unit/test_overhead_display.py`
- **.test_overhead_share_clamped_to_one()** (7 connections) — `tests/unit/test_overhead.py`
- **TestEmptyAndDegenerate** (6 connections) — `tests/unit/test_overhead.py`
- **TestWallClockAndShare** (6 connections) — `tests/unit/test_overhead.py`
- **.test_overhead_share_is_ratio()** (6 connections) — `tests/unit/test_overhead.py`
- **.test_wall_clock_from_start_and_stats()** (6 connections) — `tests/unit/test_overhead.py`
- **TestFormatting** (5 connections) — `tests/unit/test_overhead_display.py`
- **_playbook_start()** (5 connections) — `tests/unit/test_overhead.py`
- **.test_floor_is_p25_of_durations()** (5 connections) — `tests/unit/test_overhead.py`
- **.test_insufficient_samples()** (5 connections) — `tests/unit/test_overhead.py`
- **.test_skips_negative_durations()** (5 connections) — `tests/unit/test_overhead.py`
- *... and 57 more nodes in this community*

## Relationships

- [json.py](json.py.md) (10 shared connections)
- [load_session](load_session.md) (4 shared connections)
- [core/__init__.py](core-__init__.py.md) (1 shared connections)
- [IO](IO.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/overhead.py`
- `src/ansible_aom/inspect/formatters.py`
- `tests/unit/test_inspect_debug.py`
- `tests/unit/test_overhead.py`
- `tests/unit/test_overhead_display.py`

## Audit Trail

- EXTRACTED: 339 (94%)
- INFERRED: 21 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*