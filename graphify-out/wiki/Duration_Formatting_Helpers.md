# Duration Formatting Helpers

> 17 nodes · cohesion 0.17

## Key Concepts

- **test_duration.py** (10 connections) — `tests/unit/test_duration.py`
- **format_age()** (9 connections) — `src/ansible_aom/core/duration.py`
- **format_duration_compact()** (7 connections) — `src/ansible_aom/core/duration.py`
- **duration.py** (4 connections) — `src/ansible_aom/core/duration.py`
- **test_format_age_clamps_future_to_zero()** (3 connections) — `tests/unit/test_duration.py`
- **test_format_age_days()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_age_hours()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_age_minutes()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_age_seconds()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_duration_hours_pads_minutes()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_duration_minutes_pads_seconds()** (2 connections) — `tests/unit/test_duration.py`
- **test_format_duration_seconds()** (2 connections) — `tests/unit/test_duration.py`
- **Pure formatters for durations and relative ages.  These functions are used where** (1 connections) — `src/ansible_aom/core/duration.py`
- **Render a duration as the most compact human form ("42s", "1m23s", "1h05m").** (1 connections) — `src/ansible_aom/core/duration.py`
- **Render an absolute UTC ``end_time`` as a relative ``"Xs/m/h/d ago"`` string.** (1 connections) — `src/ansible_aom/core/duration.py`
- **Unit tests for the pure duration / age formatters in core.duration.** (1 connections) — `tests/unit/test_duration.py`
- **Clock skew shouldn't produce '-Ns ago'.** (1 connections) — `tests/unit/test_duration.py`

## Relationships

- [[Run History Mining]] (3 shared connections)
- [[Preflight Summary Rendering]] (2 shared connections)
- [[Compact Renderer Formatters]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/duration.py`
- `tests/unit/test_duration.py`

## Audit Trail

- EXTRACTED: 33 (63%)
- INFERRED: 19 (37%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*