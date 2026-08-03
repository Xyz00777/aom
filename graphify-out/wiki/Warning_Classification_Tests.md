# Warning Classification Tests

> 43 nodes · cohesion 0.12

## Key Concepts

- **renderer.py** (106 connections) — `src/ansible_aom/compact/renderer.py`
- **RunProgress** (27 connections) — `src/ansible_aom/core/estimate.py`
- **test_estimate.py** (20 connections) — `tests/unit/test_estimate.py`
- **_est()** (19 connections) — `tests/unit/test_estimate.py`
- **_BoundedSet** (16 connections) — `src/ansible_aom/compact/renderer.py`
- **project_remaining()** (16 connections) — `src/ansible_aom/core/estimate.py`
- **RunEstimate** (12 connections) — `src/ansible_aom/core/estimate.py`
- **.__init__()** (10 connections) — `src/ansible_aom/compact/renderer.py`
- **add_completed()** (10 connections) — `src/ansible_aom/core/estimate.py`
- **add_in_flight()** (10 connections) — `src/ansible_aom/core/estimate.py`
- **estimate.py** (8 connections) — `src/ansible_aom/core/estimate.py`
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
- *... and 18 more nodes in this community*

## Relationships

- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (14 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (10 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (8 shared connections)
- [._render_status_panel](_render_status_panel.md) (7 shared connections)
- [Renderer Event Protocol](Renderer_Event_Protocol.md) (6 shared connections)
- [Session List View](Session_List_View.md) (6 shared connections)
- [Replay Frame Signatures](Replay_Frame_Signatures.md) (4 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (3 shared connections)
- [UUIDv7 Session Generation](UUIDv7_Session_Generation.md) (3 shared connections)
- [test_password.py](test_password.py.md) (3 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (3 shared connections)
- [Status Icon Unicode Mapping](Status_Icon_Unicode_Mapping.md) (3 shared connections)

## Source Files

- `src/ansible_aom/compact/renderer.py`
- `src/ansible_aom/core/estimate.py`
- `tests/unit/test_estimate.py`

## Audit Trail

- EXTRACTED: 249 (74%)
- INFERRED: 89 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*