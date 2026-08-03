# TestGraftIncludeChildren

> 26 nodes · cohesion 0.11

## Key Concepts

- **TestGraftIncludeChildren** (18 connections) — `tests/unit/test_include_cache.py`
- **test_include_cache.py** (13 connections) — `tests/unit/test_include_cache.py`
- **_make_play()** (10 connections) — `tests/unit/test_include_cache.py`
- **_include_stub()** (8 connections) — `tests/unit/test_include_cache.py`
- **.test_block_with_include_preserves_location()** (8 connections) — `tests/unit/test_include_cache.py`
- **.test_static_include_grafts_children_into_stub()** (8 connections) — `tests/unit/test_include_cache.py`
- **.test_graft_only_targets_include_stubs()** (7 connections) — `tests/unit/test_include_cache.py`
- **.test_graft_unknown_path_leaves_stub_alone()** (7 connections) — `tests/unit/test_include_cache.py`
- **.test_nested_includes_graft_transitively()** (7 connections) — `tests/unit/test_include_cache.py`
- **._write_playbook()** (7 connections) — `tests/unit/test_include_cache.py`
- **.test_jinja_templated_include_path_is_skipped()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_role_scan_only_named_roles()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_role_scan_unparseable_role_logs_warning_once()** (4 connections) — `tests/unit/test_include_cache.py`
- **Unit tests for include/role file parsing and caching.  Covers all public functio** (1 connections) — `tests/unit/test_include_cache.py`
- **Build a single-play PlayDefinition wrapping *tasks*.** (1 connections) — `tests/unit/test_include_cache.py`
- **Build an include_tasks stub TaskDefinition like --list-tasks produces.      Real** (1 connections) — `tests/unit/test_include_cache.py`
- **Unit tests for graft_include_children() — TC-094a through TC-094e.** (1 connections) — `tests/unit/test_include_cache.py`
- **Write a one-task playbook that includes *include_target* and return its path.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094a: A literal include_tasks stub gains children from cache.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094c: include_tasks: '{{ var }}.yml' does not populate cache.** (1 connections) — `tests/unit/test_include_cache.py`
- **Only roles listed in role_names are scanned — unreferenced roles are skipped.** (1 connections) — `tests/unit/test_include_cache.py`
- **A role with YAML PyYAML can't parse logs one WARNING, no exception.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094d: include A includes B includes C → children at depth 2 and 3.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094e: block: [include_tasks: foo.yml, ...] grafts under block task.** (1 connections) — `tests/unit/test_include_cache.py`
- **If cache has no entry for an include, the stub stays empty.** (1 connections) — `tests/unit/test_include_cache.py`
- *... and 1 more nodes in this community*

## Relationships

- [IncludeCacheEntry](IncludeCacheEntry.md) (17 shared connections)
- [Path](Path.md) (14 shared connections)
- [TaskDefinition](TaskDefinition.md) (5 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (2 shared connections)
- [_discover_role](_discover_role.md) (2 shared connections)
- [PlayDefinition](PlayDefinition.md) (2 shared connections)
- [HostRunState](HostRunState.md) (1 shared connections)
- [PreParseResult Assembly](PreParseResult_Assembly.md) (1 shared connections)

## Source Files

- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 114 (97%)
- INFERRED: 4 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*