# format_age

> 22 nodes · cohesion 0.13

## Key Concepts

- **format_age()** (10 connections) — `src/ansible_aom/core/duration.py`
- **test_duration.py** (10 connections) — `tests/unit/test_duration.py`
- **duration.py** (9 connections) — `src/ansible_aom/core/duration.py`
- **format_duration_compact()** (8 connections) — `src/ansible_aom/core/duration.py`
- **format_duration_decimal()** (4 connections) — `src/ansible_aom/core/duration.py`
- **test_format_age_clamps_future_to_zero()** (3 connections) — `tests/unit/test_duration.py`
- **format_elapsed_hms()** (2 connections) — `src/ansible_aom/core/duration.py`
- **datetime** (2 connections)
- **test_format_age_days()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_age_hours()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_age_minutes()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_age_seconds()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_duration_hours_pads_minutes()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_duration_minutes_pads_seconds()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_duration_seconds()** (2 connections) — `tests/unit/test_duration.py`
- **Pure formatters for durations and relative ages.  These functions are used where** (1 connections) — `src/ansible_aom/core/duration.py`
- **Render a duration as the most compact human form ("42s", "1m23s", "1h05m").** (1 connections) — `src/ansible_aom/core/duration.py`
- **Render a duration keeping one decimal place under a minute ("0.4s", "12.3s").** (1 connections) — `src/ansible_aom/core/duration.py`
- **Render an elapsed time as ``M:SS`` (under an hour) or ``H:MM:SS``.      Used by** (1 connections) — `src/ansible_aom/core/duration.py`
- **Render an absolute UTC ``end_time`` as a relative ``"Xs/m/h/d ago"`` string.** (1 connections) — `src/ansible_aom/core/duration.py`
- **Unit tests for the pure duration / age formatters in core.duration.** (1 connections) — `tests/unit/test_duration.py`
- **Clock skew shouldn't produce '-Ns ago'.** (1 connections) — `tests/unit/test_duration.py`

## Relationships

- [renderer.py](renderer.py.md) (5 shared connections)
- [format_preflight_summary](format_preflight_summary.md) (2 shared connections)
- [format_status_bar](format_status_bar.md) (1 shared connections)
- [._emit_event_log](_emit_event_log.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/duration.py`
- `tests/unit/test_duration.py`

## Audit Trail

- EXTRACTED: 69 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*