# TestHostRunState

> 24 nodes · cohesion 0.08

## Key Concepts

- **TestHostRunState** (22 connections) — `tests/unit/test_models.py`
- **.test_host_run_state_all_fields()** (3 connections) — `tests/unit/test_models.py`
- **.test_host_run_state_changed_defaults_false()** (3 connections) — `tests/unit/test_models.py`
- **.test_host_run_state_message_defaults_empty()** (3 connections) — `tests/unit/test_models.py`
- **.test_host_run_state_required_fields()** (3 connections) — `tests/unit/test_models.py`
- **.test_host_run_state_status_can_be_changed()** (3 connections) — `tests/unit/test_models.py`
- **.test_host_run_state_status_transition_to_changed()** (3 connections) — `tests/unit/test_models.py`
- **.test_host_run_state_status_transition_to_failed()** (3 connections) — `tests/unit/test_models.py`
- **.test_host_run_state_status_transition_to_ok()** (3 connections) — `tests/unit/test_models.py`
- **.test_host_run_state_status_transition_to_skipped()** (3 connections) — `tests/unit/test_models.py`
- **.test_host_run_state_status_transition_to_unreachable()** (3 connections) — `tests/unit/test_models.py`
- **.test_host_run_state_timestamps_default_none()** (3 connections) — `tests/unit/test_models.py`
- **Tests for HostRunState dataclass - TC-187, TC-188.** (1 connections) — `tests/unit/test_models.py`
- **TC-187: HostRunState with required fields.** (1 connections) — `tests/unit/test_models.py`
- **TC-187: HostRunState with all fields.** (1 connections) — `tests/unit/test_models.py`
- **TC-187: changed defaults to False.** (1 connections) — `tests/unit/test_models.py`
- **TC-187: message defaults to empty string.** (1 connections) — `tests/unit/test_models.py`
- **TC-187: timestamps default to None.** (1 connections) — `tests/unit/test_models.py`
- **TC-188: HostRunState status is mutable.** (1 connections) — `tests/unit/test_models.py`
- **TC-188: Status transition to OK.** (1 connections) — `tests/unit/test_models.py`
- **TC-188: Status transition to CHANGED.** (1 connections) — `tests/unit/test_models.py`
- **TC-188: Status transition to FAILED.** (1 connections) — `tests/unit/test_models.py`
- **TC-188: Status transition to UNREACHABLE.** (1 connections) — `tests/unit/test_models.py`
- **TC-188: Status transition to SKIPPED.** (1 connections) — `tests/unit/test_models.py`

## Relationships

- [HostRunState](HostRunState.md) (15 shared connections)
- [TaskDefinition](TaskDefinition.md) (3 shared connections)
- [WarningType](WarningType.md) (1 shared connections)
- [WarningEntry](WarningEntry.md) (1 shared connections)
- [PlayDefinition](PlayDefinition.md) (1 shared connections)

## Source Files

- `tests/unit/test_models.py`

## Audit Trail

- EXTRACTED: 58 (87%)
- INFERRED: 9 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*