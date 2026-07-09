# Multi-Play Cross Counters

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestDiscoverRole** (11 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_role_case_insensitive_cache_key()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_role_dedup()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_role_missing_role()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_role_strips_whitespace()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_discover_role_successful()** (5 connections) — `tests/unit/test_include_cache.py`
- **Unit tests for _discover_role().** (1 connections) — `tests/unit/test_include_cache.py`
- **Successful role parsing creates and returns a RoleCacheEntry.** (1 connections) — `tests/unit/test_include_cache.py`
- **Second call returns the cached role entry.** (1 connections) — `tests/unit/test_include_cache.py`
- **Missing role directory returns None.** (1 connections) — `tests/unit/test_include_cache.py`
- **Role name is lowercased and stripped for the cache key.** (1 connections) — `tests/unit/test_include_cache.py`
- **Role name whitespace is stripped for cache key normalisation.          _discover** (1 connections) — `tests/unit/test_include_cache.py`

## Relationships

- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (5 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (5 shared connections)
- [Log Panel Search](Log_Panel_Search.md) (5 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (2 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (1 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (1 shared connections)
- [WarningEntry Dataclass](WarningEntry_Dataclass.md) (1 shared connections)

## Source Files

- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 28 (67%)
- INFERRED: 14 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*