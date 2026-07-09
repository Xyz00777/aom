# Log Panel Search

> 29 nodes · cohesion 0.10

## Key Concepts

- **Path** (43 connections)
- **TestParseIncludeTasksFile** (13 connections) — `tests/unit/test_include_cache.py`
- **_discover_include()** (11 connections) — `src/ansible_aom/core/includes.py`
- **TestDiscoverInclude** (10 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_include_dedup()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_include_missing_file()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_include_successful()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_include_with_parent_role()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_empty_list()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_jinja2_template()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_malformed_yaml()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_missing_file()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_non_list()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_skips_tasks_without_name()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_parse_include_tasks_file_valid()** (4 connections) — `tests/unit/test_include_cache.py`
- **Resolve and parse an ``include_tasks`` file, caching the result.      The file p** (1 connections) — `src/ansible_aom/core/includes.py`
- **Empty YAML list returns empty list.** (1 connections) — `tests/unit/test_include_cache.py`
- **Unit tests for _discover_include().** (1 connections) — `tests/unit/test_include_cache.py`
- **Successful include file parsing creates and returns a cache entry.** (1 connections) — `tests/unit/test_include_cache.py`
- **Second call returns the cached entry without re-parsing.** (1 connections) — `tests/unit/test_include_cache.py`
- **Missing include file returns None.** (1 connections) — `tests/unit/test_include_cache.py`
- **Parent role is recorded in the cache entry.** (1 connections) — `tests/unit/test_include_cache.py`
- **Unit tests for parse_include_tasks_file().** (1 connections) — `tests/unit/test_include_cache.py`
- **Valid YAML task list returns all task names.** (1 connections) — `tests/unit/test_include_cache.py`
- **Jinja2 template names are preserved verbatim.** (1 connections) — `tests/unit/test_include_cache.py`
- *... and 4 more nodes in this community*

## Relationships

- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (10 shared connections)
- [WarningEntry Dataclass](WarningEntry_Dataclass.md) (9 shared connections)
- [Free Strategy Task Header](Free_Strategy_Task_Header.md) (7 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (5 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (5 shared connections)
- [Multi-Play Cross Counters](Multi-Play_Cross_Counters.md) (5 shared connections)
- [JSONL Parse Failure Handling](JSONL_Parse_Failure_Handling.md) (5 shared connections)
- [Exit Code From State](Exit_Code_From_State.md) (5 shared connections)
- [PreParseResult Assembly](PreParseResult_Assembly.md) (4 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (2 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)

## Source Files

- `src/ansible_aom/core/includes.py`
- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 112 (81%)
- INFERRED: 27 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*