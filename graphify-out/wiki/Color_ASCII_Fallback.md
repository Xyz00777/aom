# Color ASCII Fallback

> 60 nodes · cohesion 0.07

## Key Concepts

- **RunProgress** (25 connections) — `src/ansible_aom/core/estimate.py`
- **test_estimate.py** (19 connections) — `tests/unit/test_estimate.py`
- **_est()** (19 connections) — `tests/unit/test_estimate.py`
- **project_remaining()** (15 connections) — `src/ansible_aom/core/estimate.py`
- **TestColorEnabled** (11 connections) — `tests/compact/test_status_bar_colors.py`
- **test_ascii_fallback.py** (10 connections) — `tests/compact/test_ascii_fallback.py`
- **RunEstimate** (10 connections) — `src/ansible_aom/core/estimate.py`
- **add_completed()** (9 connections) — `src/ansible_aom/core/estimate.py`
- **add_in_flight()** (9 connections) — `src/ansible_aom/core/estimate.py`
- **.__init__()** (8 connections) — `src/ansible_aom/compact/renderer.py`
- **is_unicode_terminal()** (7 connections) — `src/ansible_aom/core/icons.py`
- **_color_enabled()** (6 connections) — `src/ansible_aom/compact/format.py`
- **estimate.py** (6 connections) — `src/ansible_aom/core/estimate.py`
- **test_add_completed_buckets_by_prior_result()** (4 connections) — `tests/unit/test_estimate.py`
- **test_add_completed_fixed_task_does_not_touch_var_actual()** (4 connections) — `tests/unit/test_estimate.py`
- **test_add_completed_ignores_unmatched_path()** (4 connections) — `tests/unit/test_estimate.py`
- **test_add_in_flight_caps_credit_at_prior_but_not_actual()** (4 connections) — `tests/unit/test_estimate.py`
- **test_add_in_flight_credits_variable_bucket_and_actual()** (4 connections) — `tests/unit/test_estimate.py`
- **test_add_in_flight_fixed_task_credits_floor_only()** (4 connections) — `tests/unit/test_estimate.py`
- **test_fast_rerun_keeps_floor_but_collapses_variable()** (4 connections) — `tests/unit/test_estimate.py`
- **test_fixed_floor_projected_unscaled()** (4 connections) — `tests/unit/test_estimate.py`
- **test_no_prior_returns_none()** (4 connections) — `tests/unit/test_estimate.py`
- **test_remaining_never_negative()** (4 connections) — `tests/unit/test_estimate.py`
- **test_variable_remainder_scaled_by_work_pace()** (4 connections) — `tests/unit/test_estimate.py`
- **test_warmup_fraction_gate()** (4 connections) — `tests/unit/test_estimate.py`
- *... and 35 more nodes in this community*

## Relationships

- [[Compact Renderer Implementation]] (6 shared connections)
- [[Run State Completion Recap]] (3 shared connections)
- [[Panel Refresh Snapshot]] (2 shared connections)
- [[Compact Renderer Formatters]] (1 shared connections)
- [[Terminal Display Manager]] (1 shared connections)
- [[Heartbeat Liveness Tracker]] (1 shared connections)
- [[Hide State Normalization]] (1 shared connections)
- [[Role Group Task Models]] (1 shared connections)
- [[Run State Summary Panel]] (1 shared connections)
- [[Status Bar Color Tests]] (1 shared connections)
- [[Event Log Emission]] (1 shared connections)
- [[Compact Display Module Layout]] (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`
- `src/ansible_aom/core/estimate.py`
- `src/ansible_aom/core/icons.py`
- `tests/compact/test_ascii_fallback.py`
- `tests/compact/test_status_bar_colors.py`
- `tests/unit/test_estimate.py`

## Audit Trail

- EXTRACTED: 161 (61%)
- INFERRED: 101 (39%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*