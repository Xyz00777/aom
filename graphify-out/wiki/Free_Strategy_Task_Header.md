# Free Strategy Task Header

> 18 nodes · cohesion 0.15

## Key Concepts

- **resolve_includes_from_playbook()** (14 connections) — `src/ansible_aom/core/includes.py`
- **TestResolveIncludesFromPlaybook** (13 connections) — `tests/unit/test_include_cache.py`
- **.test_resolve_includes_from_playbook_missing_playbook()** (5 connections) — `tests/unit/test_include_cache.py`
- **.test_resolve_includes_from_playbook_deduplicates()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_resolve_includes_from_playbook_finds_static_include()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_resolve_includes_from_playbook_nested_blocks()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_resolve_includes_from_playbook_non_dict_entries_skipped()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_resolve_includes_from_playbook_scans_all_sections()** (4 connections) — `tests/unit/test_include_cache.py`
- **.test_resolve_includes_from_playbook_skips_jinja2_paths()** (4 connections) — `tests/unit/test_include_cache.py`
- **Parse the playbook YAML for static ``include_tasks`` directives and roles.** (1 connections) — `src/ansible_aom/core/includes.py`
- **Unit tests for resolve_includes_from_playbook().** (1 connections) — `tests/unit/test_include_cache.py`
- **Static include_tasks in a playbook are discovered and cached.** (1 connections) — `tests/unit/test_include_cache.py`
- **Include paths containing '{{' are skipped.** (1 connections) — `tests/unit/test_include_cache.py`
- **Missing playbook clears the cache dict.** (1 connections) — `tests/unit/test_include_cache.py`
- **Includes in pre_tasks, post_tasks, and handlers are all found.** (1 connections) — `tests/unit/test_include_cache.py`
- **Same include_tasks referenced multiple times only parsed once.** (1 connections) — `tests/unit/test_include_cache.py`
- **Includes inside block/rescue/always subsections are found.** (1 connections) — `tests/unit/test_include_cache.py`
- **Non-dict entries in the playbook list are safely skipped.** (1 connections) — `tests/unit/test_include_cache.py`

## Relationships

- [Log Panel Search](Log_Panel_Search.md) (7 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (4 shared connections)
- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (3 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)
- [State Machine Module](State_Machine_Module.md) (1 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (1 shared connections)
- [WarningEntry Dataclass](WarningEntry_Dataclass.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/includes.py`
- `tests/unit/test_include_cache.py`

## Audit Trail

- EXTRACTED: 45 (69%)
- INFERRED: 20 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*