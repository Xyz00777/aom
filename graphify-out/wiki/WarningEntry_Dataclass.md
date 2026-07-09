# WarningEntry Dataclass

> 22 nodes · cohesion 0.16

## Key Concepts

- **TestGraftIncludeChildren** (18 connections) — `tests/unit/test_include_cache.py`
- **test_include_cache.py** (11 connections) — `tests/unit/test_include_cache.py`
- **_make_play()** (10 connections) — `tests/unit/test_include_cache.py`
- **.test_graft_preserves_existing_children()** (9 connections) — `tests/unit/test_include_cache.py`
- **_include_stub()** (8 connections) — `tests/unit/test_include_cache.py`
- **.test_block_with_include_preserves_location()** (8 connections) — `tests/unit/test_include_cache.py`
- **.test_static_include_grafts_children_into_stub()** (8 connections) — `tests/unit/test_include_cache.py`
- **.test_graft_only_targets_include_stubs()** (7 connections) — `tests/unit/test_include_cache.py`
- **.test_graft_unknown_path_leaves_stub_alone()** (7 connections) — `tests/unit/test_include_cache.py`
- **.test_nested_includes_graft_transitively()** (7 connections) — `tests/unit/test_include_cache.py`
- **._write_playbook()** (7 connections) — `tests/unit/test_include_cache.py`
- **Unit tests for include/role file parsing and caching.  Covers all public functio** (1 connections) — `tests/unit/test_include_cache.py`
- **Build a single-play PlayDefinition wrapping *tasks*.** (1 connections) — `tests/unit/test_include_cache.py`
- **Build an include_tasks stub TaskDefinition like --list-tasks produces.      Real** (1 connections) — `tests/unit/test_include_cache.py`
- **Unit tests for graft_include_children() — TC-094a through TC-094e.** (1 connections) — `tests/unit/test_include_cache.py`
- **Write a one-task playbook that includes *include_target* and return its path.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094a: A literal include_tasks stub gains children from cache.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094d: include A includes B includes C → children at depth 2 and 3.** (1 connections) — `tests/unit/test_include_cache.py`
- **TC-094e: block: [include_tasks: foo.yml, ...] grafts under block task.** (1 connections) — `tests/unit/test_include_cache.py`
- **If a stub already has children (e.g. from runtime graft), graft appends.** (1 connections) — `tests/unit/test_include_cache.py`
- **If cache has no entry for an include, the stub stays empty.** (1 connections) — `tests/unit/test_include_cache.py`
- **A regular task whose name happens to start with 'Include ' is NOT touched.** (1 connections) — `tests/unit/test_include_cache.py`

## Relationships

- [Log Panel Search](Log_Panel_Search.md) (9 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (7 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (6 shared connections)
- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (6 shared connections)
- [JSONL Parse Failure Handling](JSONL_Parse_Failure_Handling.md) (5 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)
- [PreParseResult Assembly](PreParseResult_Assembly.md) (1 shared connections)
- [Multi-Play Cross Counters](Multi-Play_Cross_Counters.md) (1 shared connections)
- [Exit Code From State](Exit_Code_From_State.md) (1 shared connections)
- [Free Strategy Task Header](Free_Strategy_Task_Header.md) (1 shared connections)

## Source Files

- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 97 (87%)
- INFERRED: 14 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*