# IncludeCacheEntry

> 42 nodes · cohesion 0.10

## Key Concepts

- **IncludeCacheEntry** (47 connections) — `src/ansible_aom/core/models.py`
- **includes.py** (36 connections) — `src/ansible_aom/core/includes.py`
- **preflight.py** (22 connections) — `src/ansible_aom/ansible/preflight.py`
- **graft_include_children()** (19 connections) — `src/ansible_aom/core/includes.py`
- **Path** (15 connections)
- **resolve_includes_from_playbook()** (15 connections) — `src/ansible_aom/core/includes.py`
- **resolve_role_relative_includes()** (12 connections) — `src/ansible_aom/core/includes.py`
- **_graft_section_dfs()** (11 connections) — `src/ansible_aom/core/includes.py`
- **_walk_documents_for_includes()** (9 connections) — `src/ansible_aom/core/includes.py`
- **.test_graft_preserves_existing_children()** (9 connections) — `tests/unit/test_include_cache.py`
- **_graft_imported_playbook()** (8 connections) — `src/ansible_aom/core/includes.py`
- **_lookup_directive()** (8 connections) — `src/ansible_aom/core/includes.py`
- **_scan_tasks_for_includes_impl()** (8 connections) — `src/ansible_aom/core/includes.py`
- **_build_name_index()** (7 connections) — `src/ansible_aom/core/includes.py`
- **_scan_role_tasks_for_includes()** (7 connections) — `src/ansible_aom/core/includes.py`
- **_scan_tasks_for_includes()** (6 connections) — `src/ansible_aom/core/includes.py`
- **_collect_role_refs_from_tasks()** (5 connections) — `src/ansible_aom/core/includes.py`
- **_graft_children()** (5 connections) — `src/ansible_aom/core/includes.py`
- **_extract_role_name()** (4 connections) — `src/ansible_aom/core/includes.py`
- **_find_stub_by_role()** (4 connections) — `src/ansible_aom/core/includes.py`
- **_index_into()** (4 connections) — `src/ansible_aom/core/includes.py`
- **.task_count()** (2 connections) — `src/ansible_aom/core/models.py`
- **Pre-flight: parallel `--list-tasks` + `--list-hosts` orchestration.  This module** (1 connections) — `src/ansible_aom/ansible/preflight.py`
- **Pure read-only parsing of include/role files.  This module discovers and parses** (1 connections) — `src/ansible_aom/core/includes.py`
- **Walk a task list depth-first, caching every static ``include_tasks``.      Skips** (1 connections) — `src/ansible_aom/core/includes.py`
- *... and 17 more nodes in this community*

## Relationships

- [_discover_role](_discover_role.md) (19 shared connections)
- [TestGraftIncludeChildren](TestGraftIncludeChildren.md) (17 shared connections)
- [Path](Path.md) (14 shared connections)
- [TaskDefinition](TaskDefinition.md) (12 shared connections)
- [PlayDefinition](PlayDefinition.md) (11 shared connections)
- [run_preflight](run_preflight.md) (6 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (4 shared connections)
- [json.py](json.py.md) (4 shared connections)
- [HostRunState](HostRunState.md) (3 shared connections)
- [StreamPhase](StreamPhase.md) (3 shared connections)
- [WarningType](WarningType.md) (3 shared connections)
- [PreParseResult Assembly](PreParseResult_Assembly.md) (3 shared connections)

## Source Files

- `src/ansible_aom/ansible/preflight.py`
- `src/ansible_aom/core/includes.py`
- `src/ansible_aom/core/models.py`
- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 263 (93%)
- INFERRED: 20 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*