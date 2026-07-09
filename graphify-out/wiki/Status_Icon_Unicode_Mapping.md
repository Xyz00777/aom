# Status Icon Unicode Mapping

> 39 nodes · cohesion 0.08

## Key Concepts

- **HeartbeatTracker** (27 connections) — `src/ansible_aom/core/heartbeat.py`
- **test_heartbeat.py** (22 connections) — `tests/unit/test_heartbeat.py`
- **heartbeat.py** (3 connections) — `src/ansible_aom/core/heartbeat.py`
- **test_cpu_active_too_long_ago_does_not_promote_to_live()** (3 connections) — `tests/unit/test_heartbeat.py`
- **test_cpu_active_too_long_ago_does_not_rescue_from_stuck()** (3 connections) — `tests/unit/test_heartbeat.py`
- **test_cpu_activity_keeps_state_working_past_stuck_threshold()** (3 connections) — `tests/unit/test_heartbeat.py`
- **test_cpu_activity_promotes_state_to_live_during_silent_window()** (3 connections) — `tests/unit/test_heartbeat.py`
- **test_inactive_cpu_sample_does_not_promote_to_live()** (3 connections) — `tests/unit/test_heartbeat.py`
- **test_live_immediately_after_first_bytes()** (3 connections) — `tests/unit/test_heartbeat.py`
- **test_liveness_state_reason_field_defaults()** (3 connections) — `tests/unit/test_heartbeat.py`
- **test_reason_cpu_for_stuck_window_rescue()** (3 connections) — `tests/unit/test_heartbeat.py`
- **test_reason_silent_when_working_via_byte_age_only()** (3 connections) — `tests/unit/test_heartbeat.py`
- **test_silent_task_after_initial_byte_progresses_through_levels()** (3 connections) — `tests/unit/test_heartbeat.py`
- **test_stuck_when_bytes_old_and_no_cpu_activity()** (3 connections) — `tests/unit/test_heartbeat.py`
- **test_working_state_via_byte_age_alone()** (3 connections) — `tests/unit/test_heartbeat.py`
- **.state()** (2 connections) — `src/ansible_aom/core/heartbeat.py`
- **test_age_seconds_truncates_toward_zero()** (2 connections) — `tests/unit/test_heartbeat.py`
- **test_live_window_uses_configured_threshold()** (2 connections) — `tests/unit/test_heartbeat.py`
- **test_liveness_state_is_frozen_dataclass()** (2 connections) — `tests/unit/test_heartbeat.py`
- **test_new_bytes_return_tracker_to_live_after_stuck()** (2 connections) — `tests/unit/test_heartbeat.py`
- **test_reason_cpu_when_promoted_from_working_to_live()** (2 connections) — `tests/unit/test_heartbeat.py`
- **test_reason_pty_for_recent_bytes()** (2 connections) — `tests/unit/test_heartbeat.py`
- **test_reason_stuck_when_no_signals_at_all()** (2 connections) — `tests/unit/test_heartbeat.py`
- **test_state_is_none_before_any_bytes_observed()** (2 connections) — `tests/unit/test_heartbeat.py`
- **test_stuck_when_only_inactive_cpu_samples_received()** (2 connections) — `tests/unit/test_heartbeat.py`
- *... and 14 more nodes in this community*

## Relationships

- [Renderer Event Protocol](Renderer_Event_Protocol.md) (7 shared connections)
- [Inspect Debug Diagnostics](Inspect_Debug_Diagnostics.md) (2 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/heartbeat.py`
- `tests/unit/test_heartbeat.py`

## Audit Trail

- EXTRACTED: 76 (62%)
- INFERRED: 46 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*