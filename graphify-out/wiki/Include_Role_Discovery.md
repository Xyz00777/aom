# Include Role Discovery

> 170 nodes · cohesion 0.02

## Key Concepts

- **IncludeCacheEntry** (44 connections) — `src/ansible_aom/core/models.py`
- **includes.py** (25 connections) — `src/ansible_aom/core/includes.py`
- **graft_include_children()** (20 connections) — `src/ansible_aom/core/includes.py`
- **RoleCacheEntry** (19 connections) — `src/ansible_aom/core/models.py`
- **TestGraftIncludeChildren** (18 connections) — `tests/unit/test_include_cache.py`
- **resolve_includes_from_playbook()** (16 connections) — `src/ansible_aom/core/includes.py`
- **_discover_role()** (15 connections) — `src/ansible_aom/core/includes.py`
- **parse_include_tasks_file()** (15 connections) — `src/ansible_aom/core/includes.py`
- **TestParseIncludeTasksFile** (13 connections) — `tests/unit/test_include_cache.py`
- **TestResolveIncludesFromPlaybook** (13 connections) — `tests/unit/test_include_cache.py`
- **_discover_include()** (12 connections) — `src/ansible_aom/core/includes.py`
- **_graft_section_dfs()** (12 connections) — `src/ansible_aom/core/includes.py`
- **parse_role_tasks()** (12 connections) — `src/ansible_aom/core/includes.py`
- **resolve_role_relative_includes()** (12 connections) — `src/ansible_aom/core/includes.py`
- **Static pre-expansion of include_tasks (Plan A)** (12 connections) — `.sisyphus/plans/include-tasks-pre-expansion.md`
- **TestDiscoverRole** (12 connections) — `tests/unit/test_include_cache.py`
- **discover_include_with_runtime_path()** (11 connections) — `src/ansible_aom/core/includes.py`
- **test_include_cache.py** (11 connections) — `tests/unit/test_include_cache.py`
- **TestParseRoleTasks** (11 connections) — `tests/unit/test_include_cache.py`
- **_load_task_list()** (10 connections) — `src/ansible_aom/core/includes.py`
- **_walk_documents_for_includes()** (10 connections) — `src/ansible_aom/core/includes.py`
- **_make_play()** (10 connections) — `tests/unit/test_include_cache.py`
- **TestCacheEntryProperties** (10 connections) — `tests/unit/test_include_cache.py`
- **TestDiscoverInclude** (10 connections) — `tests/unit/test_include_cache.py`
- **_graft_imported_playbook()** (9 connections) — `src/ansible_aom/core/includes.py`
- *... and 145 more nodes in this community*

## Relationships

- [[Run Config Key Normalization]] (58 shared connections)
- [[Task Definition Live Refresh]] (18 shared connections)
- [[Play Definition Tree Population]] (13 shared connections)
- [[Role Group Task Models]] (6 shared connections)
- [[Parallel Pre-flight Runner]] (3 shared connections)
- [[Total Task Counting]] (3 shared connections)
- [[Dynamic Include Expansion]] (3 shared connections)
- [[Tree Truncation Utilities]] (2 shared connections)
- [[Role Inference Indexes]] (2 shared connections)
- [[Role Chain Extraction]] (1 shared connections)
- [[PTY Stream Parser]] (1 shared connections)

## Source Files

- `.sisyphus/plans/include-tasks-pre-expansion.md`
- `.sisyphus/test-fixtures/imported_tasks.yml`
- `.sisyphus/test-fixtures/included_tasks.yml`
- `.sisyphus/test-fixtures/with_import.yml`
- `.sisyphus/test-fixtures/with_include.yml`
- `.sisyphus/test-fixtures/with_role.yml`
- `src/ansible_aom/core/includes.py`
- `src/ansible_aom/core/models.py`
- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 579 (75%)
- INFERRED: 189 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*