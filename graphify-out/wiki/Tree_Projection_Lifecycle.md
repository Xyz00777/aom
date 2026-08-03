# Tree Projection Lifecycle

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestDiscoverInclude** (10 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_include_missing_file()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_include_successful()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_include_with_parent_role()** (5 connections) — `tests/unit/test_include_cache.py`
- **Unit tests for _discover_include().** (1 connections) — `tests/unit/test_include_cache.py`
- **Successful include file parsing creates and returns a cache entry.** (1 connections) — `tests/unit/test_include_cache.py`
- **Missing include file returns None.** (1 connections) — `tests/unit/test_include_cache.py`
- **Parent role is recorded in the cache entry.** (1 connections) — `tests/unit/test_include_cache.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (5 shared connections)
- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (4 shared connections)
- [Log Panel Search](Log_Panel_Search.md) (4 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (1 shared connections)
- [WarningEntry Dataclass](WarningEntry_Dataclass.md) (1 shared connections)

## Source Files

- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 19 (66%)
- INFERRED: 10 (34%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*