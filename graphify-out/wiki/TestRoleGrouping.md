# TestRoleGrouping

> 18 nodes · cohesion 0.14

## Key Concepts

- **TestRoleGrouping** (21 connections) — `tests/unit/test_parser.py`
- **group_roles()** (11 connections) — `src/ansible_aom/core/parser.py`
- **.test_five_same_role_tasks_creates_group()** (5 connections) — `tests/unit/test_parser.py`
- **.test_role_group_at_end_of_list()** (5 connections) — `tests/unit/test_parser.py`
- **.test_four_same_role_tasks_no_grouping()** (4 connections) — `tests/unit/test_parser.py`
- **.test_mixed_roles_no_grouping()** (4 connections) — `tests/unit/test_parser.py`
- **.test_multiple_role_groups()** (4 connections) — `tests/unit/test_parser.py`
- **.test_role_group_name_format()** (4 connections) — `tests/unit/test_parser.py`
- **.test_role_group_with_mixed_none_role()** (4 connections) — `tests/unit/test_parser.py`
- **Group consecutive same-role tasks (5 or more) into RoleGroupDefinition.      Arg** (1 connections) — `src/ansible_aom/core/parser.py`
- **TC-122, TC-123: Role grouping logic.** (1 connections) — `tests/unit/test_parser.py`
- **TC-122: 5+ consecutive same-role tasks are grouped.** (1 connections) — `tests/unit/test_parser.py`
- **TC-122: 4 same-role tasks NOT grouped (threshold is 5).** (1 connections) — `tests/unit/test_parser.py`
- **TC-122: Mixed roles do not create groups.** (1 connections) — `tests/unit/test_parser.py`
- **TC-123, TC-181: RoleGroup name property format.** (1 connections) — `tests/unit/test_parser.py`
- **Tasks without role (None) do not interrupt role grouping.** (1 connections) — `tests/unit/test_parser.py`
- **Multiple role groups in sequence.** (1 connections) — `tests/unit/test_parser.py`
- **Role group can be at end of task list.** (1 connections) — `tests/unit/test_parser.py`

## Relationships

- [TaskDefinition](TaskDefinition.md) (13 shared connections)
- [HostRunState](HostRunState.md) (4 shared connections)
- [WarningType](WarningType.md) (3 shared connections)
- [StreamPhase](StreamPhase.md) (2 shared connections)
- [IncludeCacheEntry](IncludeCacheEntry.md) (1 shared connections)
- [assemble_definitions](assemble_definitions.md) (1 shared connections)
- [PlayDefinition](PlayDefinition.md) (1 shared connections)
- [JsonLineStream](JsonLineStream.md) (1 shared connections)
- [PtyStreamParser](PtyStreamParser.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 53 (75%)
- INFERRED: 18 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*