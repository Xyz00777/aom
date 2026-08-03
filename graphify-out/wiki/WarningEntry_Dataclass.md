# WarningEntry Dataclass

> 26 nodes · cohesion 0.12

## Key Concepts

- **TestGraftIncludeChildren** (18 connections) — `tests/unit/test_include_cache.py`
- **test_include_cache.py** (13 connections) — `tests/unit/test_include_cache.py`
- **_make_play()** (10 connections) — `tests/unit/test_include_cache.py`
- **.test_graft_preserves_existing_children()** (9 connections) — `tests/unit/test_include_cache.py`
- **_include_stub()** (8 connections) — `tests/unit/test_include_cache.py`
- **.test_block_with_include_preserves_location()** (8 connections) — `tests/unit/test_include_cache.py`
- **.test_static_include_grafts_children_into_stub()** (8 connections) — `tests/unit/test_include_cache.py`
- **.test_graft_only_targets_include_stubs()** (7 connections) — `tests/unit/test_include_cache.py`
- **.test_graft_unknown_path_leaves_stub_alone()** (7 connections) — `tests/unit/test_include_cache.py`
- **.test_nested_includes_graft_transitively()** (7 connections) — `tests/unit/test_include_cache.py`
- **._write_playbook()** (7 connections) — `tests/unit/test_include_cache.py`
- **.test_jinja_templated_include_path_is_skipped()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_role_scan_missing_role_is_silent()** (4 connections) — `tests/unit/test_include_cache.py`
- **Unit tests for include/role file parsing and caching.  Covers all public functio** (1 connections) — `tests/unit/test_include_cache.py`
- **Build a single-play PlayDefinition wrapping *tasks*.** (1 connections) — `tests/unit/test_include_cache.py`
- **Build an include_tasks stub TaskDefinition like --list-tasks produces.      Real** (1 connections) — `tests/unit/test_include_cache.py`
- **Unit tests for graft_include_children() — TC-094a through TC-094e.** (1 connections) — `tests/unit/test_include_cache.py`
- **Write a one-task playbook that includes *include_target* and return its path.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094a: A literal include_tasks stub gains children from cache.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094c: include_tasks: '{{ var }}.yml' does not populate cache.** (1 connections) — `tests/unit/test_include_cache.py`
- **A role listed in role_names but absent on disk does not log at WARNING/DEBUG.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094d: include A includes B includes C → children at depth 2 and 3.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094e: block: [include_tasks: foo.yml, ...] grafts under block task.** (1 connections) — `tests/unit/test_include_cache.py`
- **If a stub already has children (e.g. from runtime graft), graft appends.** (1 connections) — `tests/unit/test_include_cache.py`
- **If cache has no entry for an include, the stub stays empty.** (1 connections) — `tests/unit/test_include_cache.py`
- *... and 1 more nodes in this community*

## Relationships

- [Log Panel Search](Log_Panel_Search.md) (15 shared connections)
- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (14 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (8 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (2 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [Tree Projection Lifecycle](Tree_Projection_Lifecycle.md) (1 shared connections)
- [PreParseResult Assembly](PreParseResult_Assembly.md) (1 shared connections)
- [Exit Code From State](Exit_Code_From_State.md) (1 shared connections)

## Source Files

- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 107 (87%)
- INFERRED: 16 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*