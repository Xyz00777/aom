# PreParseResult Assembly

> 10 nodes · cohesion 0.24

## Key Concepts

- **discover_include_with_runtime_path()** (11 connections) — `src/ansible_aom/core/includes.py`
- **TestDiscoverIncludeWithRuntimePath** (9 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_include_with_runtime_path_missing_file()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_include_with_runtime_path_no_line_number()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_include_with_runtime_path_strips_line_number()** (5 connections) — `tests/unit/test_include_cache.py`
- **Discover an include from the runtime ``task.path`` JSONL field.      The ``task.** (1 connections) — `src/ansible_aom/core/includes.py`
- **Unit tests for discover_include_with_runtime_path().** (1 connections) — `tests/unit/test_include_cache.py`
- **task.path format 'file.yml:2' extracts 'file.yml'.** (1 connections) — `tests/unit/test_include_cache.py`
- **Path without line number works unchanged.** (1 connections) — `tests/unit/test_include_cache.py`
- **Missing file returns None even with runtime path format.** (1 connections) — `tests/unit/test_include_cache.py`

## Relationships

- [RunState](RunState.md) (6 shared connections)
- [IncludeCacheEntry](IncludeCacheEntry.md) (3 shared connections)
- [Path](Path.md) (3 shared connections)
- [_discover_role](_discover_role.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [TaskDefinition](TaskDefinition.md) (1 shared connections)
- [PlayDefinition](PlayDefinition.md) (1 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (1 shared connections)
- [TestGraftIncludeChildren](TestGraftIncludeChildren.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/includes.py`
- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 33 (82%)
- INFERRED: 7 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*