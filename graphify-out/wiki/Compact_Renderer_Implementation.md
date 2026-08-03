# Compact Renderer Implementation

> 28 nodes · cohesion 0.07

## Key Concepts

- **TestTaskDefinition** (24 connections) — `tests/unit/test_models.py`
- **.test_task_definition_all_fields_types()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_children_can_contain_dynamic_tasks()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_children_defaults_empty_list()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_is_dynamic_defaults_false()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_is_dynamic_explicit_true()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_path_can_be_set()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_path_defaults_none()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_required_fields()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_role_can_be_none()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_task_order_minus_one_for_dynamic()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_task_order_non_negative_for_static()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_uuid_can_be_set()** (3 connections) — `tests/unit/test_models.py`
- **.test_task_definition_uuid_defaults_none()** (3 connections) — `tests/unit/test_models.py`
- **Tests for TaskDefinition dataclass - TC-174 to TC-179.** (1 connections) — `tests/unit/test_models.py`
- **TC-174: TaskDefinition with all required fields.** (1 connections) — `tests/unit/test_models.py`
- **TC-175: is_dynamic defaults to False for static tasks.** (1 connections) — `tests/unit/test_models.py`
- **TC-175: is_dynamic can be set to True for dynamic tasks.** (1 connections) — `tests/unit/test_models.py`
- **TC-176: UUID defaults to None before JSONL matching.** (1 connections) — `tests/unit/test_models.py`
- **TC-176: UUID can be set after JSONL matching.** (1 connections) — `tests/unit/test_models.py`
- **TC-177: path defaults to None before JSONL matching.** (1 connections) — `tests/unit/test_models.py`
- **TC-177: path can be set with file:line format.** (1 connections) — `tests/unit/test_models.py`
- **TC-178: children defaults to empty list.** (1 connections) — `tests/unit/test_models.py`
- **TC-178: children can contain TaskDefinition objects.** (1 connections) — `tests/unit/test_models.py`
- **TC-179: task_order is -1 for dynamic tasks.** (1 connections) — `tests/unit/test_models.py`
- *... and 3 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (16 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (3 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (2 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [Check Mode Chip](Check_Mode_Chip.md) (1 shared connections)

## Source Files

- `tests/unit/test_models.py`

## Audit Trail

- EXTRACTED: 55 (71%)
- INFERRED: 22 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*