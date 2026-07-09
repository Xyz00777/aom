# Warning Classification Tests

> 37 nodes · cohesion 0.14

## Key Concepts

- **RunProgress** (26 connections) — `src/ansible_aom/core/estimate.py`
- **test_estimate.py** (19 connections) — `tests/unit/test_estimate.py`
- **_est()** (19 connections) — `tests/unit/test_estimate.py`
- **project_remaining()** (15 connections) — `src/ansible_aom/core/estimate.py`
- **RunEstimate** (11 connections) — `src/ansible_aom/core/estimate.py`
- **add_completed()** (9 connections) — `src/ansible_aom/core/estimate.py`
- **add_in_flight()** (9 connections) — `src/ansible_aom/core/estimate.py`
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
- **test_warmup_min_tasks_gate()** (4 connections) — `tests/unit/test_estimate.py`
- **test_work_pace_clamped_high()** (4 connections) — `tests/unit/test_estimate.py`
- **test_work_pace_clamped_low()** (4 connections) — `tests/unit/test_estimate.py`
- **test_work_pace_defaults_to_one_before_any_variable_completes()** (4 connections) — `tests/unit/test_estimate.py`
- **.set_prior_run()** (3 connections) — `src/ansible_aom/compact/renderer.py`
- *... and 12 more nodes in this community*

## Relationships

- [Inspect Debug Diagnostics](Inspect_Debug_Diagnostics.md) (4 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (3 shared connections)
- [Community 560](Community_560.md) (2 shared connections)
- [Crash Recovery Panels](Crash_Recovery_Panels.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/renderer.py`
- `src/ansible_aom/core/estimate.py`
- `tests/unit/test_estimate.py`

## Audit Trail

- EXTRACTED: 121 (62%)
- INFERRED: 75 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*