# TestRuntimeRoleTaskCount

> 17 nodes · cohesion 0.15

## Key Concepts

- **TestRuntimeRoleTaskCount** (12 connections) — `tests/unit/test_runtime_role_task_count.py`
- **._state_with_dynamic_role()** (7 connections) — `tests/unit/test_runtime_role_task_count.py`
- **.test_no_double_counting_preflight_and_runtime()** (7 connections) — `tests/unit/test_runtime_role_task_count.py`
- **.test_task_name_with_colon_not_misidentified_as_role()** (6 connections) — `tests/unit/test_runtime_role_task_count.py`
- **test_runtime_role_task_count.py** (5 connections) — `tests/unit/test_runtime_role_task_count.py`
- **_td()** (5 connections) — `tests/unit/test_runtime_role_task_count.py`
- **.test_dynamic_role_with_no_preflight_shows_runtime_count()** (5 connections) — `tests/unit/test_runtime_role_task_count.py`
- **.test_dynamic_role_shows_task_count_in_label()** (4 connections) — `tests/unit/test_runtime_role_task_count.py`
- **.test_dynamic_role_task_appears_under_role_header()** (4 connections) — `tests/unit/test_runtime_role_task_count.py`
- **Regression tests for role_total_tasks counting runtime-only tasks.  When a role** (1 connections) — `tests/unit/test_runtime_role_task_count.py`
- **A role loaded via include_role must show its runtime task count         in the r** (1 connections) — `tests/unit/test_runtime_role_task_count.py`
- **Runtime podman tasks should appear as children of the podman         role header** (1 connections) — `tests/unit/test_runtime_role_task_count.py`
- **When a role has tasks in BOTH preflight and runtime (same task         resolved** (1 connections) — `tests/unit/test_runtime_role_task_count.py`
- **A task name containing ' : ' that is NOT a role prefix must not         be assig** (1 connections) — `tests/unit/test_runtime_role_task_count.py`
- **Pure runtime role (no preflight tasks at all) must still show         the correc** (1 connections) — `tests/unit/test_runtime_role_task_count.py`
- **role_total_tasks must include tasks from runtime that aren't in     the prefligh** (1 connections) — `tests/unit/test_runtime_role_task_count.py`
- **Preflight has no podman tasks. At runtime, podman tasks appear         via inclu** (1 connections) — `tests/unit/test_runtime_role_task_count.py`

## Relationships

- [PlayDefinition](PlayDefinition.md) (5 shared connections)
- [.from_run_state](from_run_state.md) (5 shared connections)
- [TaskDefinition](TaskDefinition.md) (4 shared connections)
- [RunState](RunState.md) (4 shared connections)
- [HostRunState](HostRunState.md) (2 shared connections)
- [tree.py](tree.py.md) (1 shared connections)

## Source Files

- `tests/unit/test_runtime_role_task_count.py`

## Audit Trail

- EXTRACTED: 59 (94%)
- INFERRED: 4 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*