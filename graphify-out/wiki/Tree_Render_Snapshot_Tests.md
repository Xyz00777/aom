# Tree Render Snapshot Tests

> 20 nodes · cohesion 0.10

## Key Concepts

- **TestRunState** (21 connections) — `tests/unit/test_models.py`
- **.test_run_state_plays_dict_key_is_play_id()** (4 connections) — `tests/unit/test_models.py`
- **.test_run_state_plays_dict_value_is_play_run_state()** (4 connections) — `tests/unit/test_models.py`
- **.test_run_state_all_fields()** (3 connections) — `tests/unit/test_models.py`
- **.test_run_state_definitions_defaults_empty_list()** (3 connections) — `tests/unit/test_models.py`
- **.test_run_state_plays_defaults_empty_dict()** (3 connections) — `tests/unit/test_models.py`
- **.test_run_state_required_field_playbook()** (3 connections) — `tests/unit/test_models.py`
- **.test_run_state_single_instance_per_playbook()** (3 connections) — `tests/unit/test_models.py`
- **.test_run_state_status_defaults_pending()** (3 connections) — `tests/unit/test_models.py`
- **.test_run_state_timestamps_default_none()** (3 connections) — `tests/unit/test_models.py`
- **Tests for RunState dataclass - TC-194, TC-195, TC-196.** (1 connections) — `tests/unit/test_models.py`
- **TC-194: RunState requires playbook field.** (1 connections) — `tests/unit/test_models.py`
- **TC-194: RunState with all fields.** (1 connections) — `tests/unit/test_models.py`
- **TC-194: plays defaults to empty dict.** (1 connections) — `tests/unit/test_models.py`
- **TC-195: definitions defaults to empty list.** (1 connections) — `tests/unit/test_models.py`
- **TC-194: status defaults to PENDING.** (1 connections) — `tests/unit/test_models.py`
- **TC-194: timestamps default to None.** (1 connections) — `tests/unit/test_models.py`
- **TC-196: plays dict uses play UUID/id string as key.** (1 connections) — `tests/unit/test_models.py`
- **TC-196: plays dict value is PlayRunState.** (1 connections) — `tests/unit/test_models.py`
- **TC-194 edge case: One RunState instance per playbook run.** (1 connections) — `tests/unit/test_models.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (13 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (5 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (2 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [Check Mode Chip](Check_Mode_Chip.md) (1 shared connections)

## Source Files

- `tests/unit/test_models.py`

## Audit Trail

- EXTRACTED: 40 (67%)
- INFERRED: 20 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*