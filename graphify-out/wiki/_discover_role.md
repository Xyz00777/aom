# _discover_role

> 40 nodes · cohesion 0.06

## Key Concepts

- **_discover_role()** (14 connections) — `src/ansible_aom/core/includes.py`
- **parse_include_tasks_file()** (13 connections) — `src/ansible_aom/core/includes.py`
- **TestParseIncludeTasksFile** (13 connections) — `tests/unit/test_include_cache.py`
- **_discover_include()** (11 connections) — `src/ansible_aom/core/includes.py`
- **parse_role_tasks()** (11 connections) — `src/ansible_aom/core/includes.py`
- **TestDiscoverRole** (11 connections) — `tests/unit/test_include_cache.py`
- **_load_task_list()** (9 connections) — `src/ansible_aom/core/includes.py`
- **_find_nested_role_includes()** (5 connections) — `src/ansible_aom/core/includes.py`
- **.test_discover_role_case_insensitive_cache_key()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_role_dedup()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_role_missing_role()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_role_strips_whitespace()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_role_successful()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_empty_list()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_jinja2_template()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_malformed_yaml()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_missing_file()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_non_list()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_skips_tasks_without_name()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_valid()** (4 connections) — `tests/unit/test_include_cache.py`
- **Read ``role_dir/tasks/main.yml`` and return the list of task names.      ``role** (1 connections) — `src/ansible_aom/core/includes.py`
- **Return names of roles included from this role's ``tasks/main.yml``.      Walks t** (1 connections) — `src/ansible_aom/core/includes.py`
- **Resolve and parse an ``include_tasks`` file, caching the result.      The file p** (1 connections) — `src/ansible_aom/core/includes.py`
- **Resolve a role's ``tasks/main.yml``, caching the result.      The role directory** (1 connections) — `src/ansible_aom/core/includes.py`
- **Read a YAML task-list file and return the top-level list (across documents).** (1 connections) — `src/ansible_aom/core/includes.py`
- *... and 15 more nodes in this community*

## Relationships

- [Path](Path.md) (21 shared connections)
- [IncludeCacheEntry](IncludeCacheEntry.md) (19 shared connections)
- [RunState](RunState.md) (7 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (3 shared connections)
- [strip_role_prefix](strip_role_prefix.md) (2 shared connections)
- [TaskDefinition](TaskDefinition.md) (2 shared connections)
- [PlayDefinition](PlayDefinition.md) (2 shared connections)
- [TestGraftIncludeChildren](TestGraftIncludeChildren.md) (2 shared connections)
- [PreParseResult Assembly](PreParseResult_Assembly.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/includes.py`
- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 147 (92%)
- INFERRED: 13 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*