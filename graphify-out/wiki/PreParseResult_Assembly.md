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

- [CLI Interface Tests](CLI_Interface_Tests.md) (6 shared connections)
- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (4 shared connections)
- [Log Panel Search](Log_Panel_Search.md) (3 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (2 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (1 shared connections)
- [WarningEntry Dataclass](WarningEntry_Dataclass.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/includes.py`
- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 25 (62%)
- INFERRED: 15 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*