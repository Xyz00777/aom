# JSONL Parse Failure Handling

> 12 nodes · cohesion 0.17

## Key Concepts

- **resolve_role_relative_includes()** (11 connections) — `src/ansible_aom/core/includes.py`
- **.test_jinja_templated_include_path_is_skipped()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_role_relative_include_resolution()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_role_scan_missing_role_is_silent()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_role_scan_only_named_roles()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_role_scan_unparseable_role_logs_warning_once()** (4 connections) — `tests/unit/test_include_cache.py`
- **Scan a specific set of roles' ``tasks/main.yml`` for ``include_tasks``.      Onl** (1 connections) — `src/ansible_aom/core/includes.py`
- **TC-094b: include_tasks inside a role resolves relative to the role dir.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094c: include_tasks: '{{ var }}.yml' does not populate cache.** (1 connections) — `tests/unit/test_include_cache.py`
- **Only roles listed in role_names are scanned — unreferenced roles are skipped.** (1 connections) — `tests/unit/test_include_cache.py`
- **A role listed in role_names but absent on disk does not log at WARNING/DEBUG.** (1 connections) — `tests/unit/test_include_cache.py`
- **A role with YAML PyYAML can't parse logs one WARNING, no exception.** (1 connections) — `tests/unit/test_include_cache.py`

## Relationships

- [Log Panel Search](Log_Panel_Search.md) (5 shared connections)
- [WarningEntry Dataclass](WarningEntry_Dataclass.md) (5 shared connections)
- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (3 shared connections)
- [State Machine Module](State_Machine_Module.md) (1 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/includes.py`
- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 26 (70%)
- INFERRED: 11 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*