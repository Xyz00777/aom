# Ungrouped Role Tree Tests

> 40 nodes · cohesion 0.10

## Key Concepts

- **includes.py** (25 connections) — `src/ansible_aom/core/includes.py`
- **graft_include_children()** (18 connections) — `src/ansible_aom/core/includes.py`
- **Path** (15 connections)
- **_discover_role()** (13 connections) — `src/ansible_aom/core/includes.py`
- **parse_include_tasks_file()** (13 connections) — `src/ansible_aom/core/includes.py`
- **_graft_section_dfs()** (11 connections) — `src/ansible_aom/core/includes.py`
- **parse_role_tasks()** (11 connections) — `src/ansible_aom/core/includes.py`
- **_load_task_list()** (9 connections) — `src/ansible_aom/core/includes.py`
- **_walk_documents_for_includes()** (9 connections) — `src/ansible_aom/core/includes.py`
- **_graft_imported_playbook()** (8 connections) — `src/ansible_aom/core/includes.py`
- **_lookup_directive()** (8 connections) — `src/ansible_aom/core/includes.py`
- **_scan_tasks_for_includes_impl()** (8 connections) — `src/ansible_aom/core/includes.py`
- **_build_name_index()** (7 connections) — `src/ansible_aom/core/includes.py`
- **_scan_role_tasks_for_includes()** (7 connections) — `src/ansible_aom/core/includes.py`
- **_scan_tasks_for_includes()** (6 connections) — `src/ansible_aom/core/includes.py`
- **_collect_role_refs_from_tasks()** (5 connections) — `src/ansible_aom/core/includes.py`
- **_find_nested_role_includes()** (5 connections) — `src/ansible_aom/core/includes.py`
- **_graft_children()** (5 connections) — `src/ansible_aom/core/includes.py`
- **_extract_role_name()** (4 connections) — `src/ansible_aom/core/includes.py`
- **_find_stub_by_role()** (4 connections) — `src/ansible_aom/core/includes.py`
- **_index_into()** (4 connections) — `src/ansible_aom/core/includes.py`
- **Pure read-only parsing of include/role files.  This module discovers and parses** (1 connections) — `src/ansible_aom/core/includes.py`
- **Read ``role_dir/tasks/main.yml`` and return the list of task names.      ``role** (1 connections) — `src/ansible_aom/core/includes.py`
- **Return names of roles included from this role's ``tasks/main.yml``.      Walks t** (1 connections) — `src/ansible_aom/core/includes.py`
- **Walk a task list depth-first, caching every static ``include_tasks``.      Skips** (1 connections) — `src/ansible_aom/core/includes.py`
- *... and 15 more nodes in this community*

## Relationships

- [Log Panel Search](Log_Panel_Search.md) (10 shared connections)
- [Rerun Confirmation Prompt](Rerun_Confirmation_Prompt.md) (9 shared connections)
- [WarningEntry Dataclass](WarningEntry_Dataclass.md) (6 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (5 shared connections)
- [Multi-Play Cross Counters](Multi-Play_Cross_Counters.md) (5 shared connections)
- [Exit Code From State](Exit_Code_From_State.md) (5 shared connections)
- [Free Strategy Task Header](Free_Strategy_Task_Header.md) (3 shared connections)
- [JSONL Parse Failure Handling](JSONL_Parse_Failure_Handling.md) (3 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (3 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (2 shared connections)
- [PreParseResult Assembly](PreParseResult_Assembly.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/includes.py`

## Audit Trail

- EXTRACTED: 187 (87%)
- INFERRED: 27 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*