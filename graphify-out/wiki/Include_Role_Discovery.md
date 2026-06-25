# Include Role Discovery

> 173 nodes · cohesion 0.02

## Key Concepts

- **IncludeCacheEntry** (39 connections) — `src/ansible_aom/core/models.py`
- **includes.py** (26 connections) — `src/ansible_aom/core/includes.py`
- **graft_include_children()** (19 connections) — `src/ansible_aom/core/includes.py`
- **TestGraftIncludeChildren** (19 connections) — `tests/unit/test_include_cache.py`
- **RoleCacheEntry** (16 connections) — `src/ansible_aom/core/models.py`
- **resolve_includes_from_playbook()** (15 connections) — `src/ansible_aom/core/includes.py`
- **parse_include_tasks_file()** (14 connections) — `src/ansible_aom/core/includes.py`
- **TestParseIncludeTasksFile** (14 connections) — `tests/unit/test_include_cache.py`
- **TestResolveIncludesFromPlaybook** (14 connections) — `tests/unit/test_include_cache.py`
- **_discover_role()** (13 connections) — `src/ansible_aom/core/includes.py`
- **TestDiscoverRole** (13 connections) — `tests/unit/test_include_cache.py`
- **Static pre-expansion of include_tasks (Plan A)** (12 connections) — `.sisyphus/plans/include-tasks-pre-expansion.md`
- **test_include_cache.py** (12 connections) — `tests/unit/test_include_cache.py`
- **TestParseRoleTasks** (12 connections) — `tests/unit/test_include_cache.py`
- **_discover_include()** (11 connections) — `src/ansible_aom/core/includes.py`
- **discover_include_with_runtime_path()** (11 connections) — `src/ansible_aom/core/includes.py`
- **_graft_section_dfs()** (11 connections) — `src/ansible_aom/core/includes.py`
- **parse_role_tasks()** (11 connections) — `src/ansible_aom/core/includes.py`
- **resolve_role_relative_includes()** (11 connections) — `src/ansible_aom/core/includes.py`
- **TestCacheEntryProperties** (11 connections) — `tests/unit/test_include_cache.py`
- **TestDiscoverInclude** (11 connections) — `tests/unit/test_include_cache.py`
- **_make_play()** (10 connections) — `tests/unit/test_include_cache.py`
- **TestDiscoverIncludeWithRuntimePath** (10 connections) — `tests/unit/test_include_cache.py`
- **_load_task_list()** (9 connections) — `src/ansible_aom/core/includes.py`
- **_walk_documents_for_includes()** (9 connections) — `src/ansible_aom/core/includes.py`
- *... and 148 more nodes in this community*

## Relationships

- [[Run Config Key Normalization]] (58 shared connections)
- [[Run State Summary Panel]] (23 shared connections)
- [[Task Definition Live Refresh]] (18 shared connections)
- [[Play Definition Tree Population]] (13 shared connections)
- [[Role Group Task Models]] (5 shared connections)
- [[Parallel Pre-flight Runner]] (3 shared connections)
- [[Total Task Counting]] (3 shared connections)
- [[Dynamic Include Expansion]] (3 shared connections)
- [[Run History Mining]] (2 shared connections)
- [[Runtime Event Handlers]] (2 shared connections)
- [[Tree Truncation Utilities]] (2 shared connections)
- [[Role Inference Indexes]] (2 shared connections)

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

- EXTRACTED: 571 (75%)
- INFERRED: 188 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*