# parse_list_tasks_output

> 54 nodes · cohesion 0.05

## Key Concepts

- **parse_list_tasks_output()** (31 connections) — `src/ansible_aom/core/parser.py`
- **TestListTasksEdgeCases** (26 connections) — `tests/unit/test_parser.py`
- **TestListTasksParser** (25 connections) — `tests/unit/test_parser.py`
- **.test_exit_code_syntax_error_output()** (4 connections) — `tests/unit/test_parser.py`
- **.test_blocks_flattened()** (3 connections) — `tests/unit/test_parser.py`
- **.test_exit_code_error_output()** (3 connections) — `tests/unit/test_parser.py`
- **.test_exit_code_success_output()** (3 connections) — `tests/unit/test_parser.py`
- **.test_import_tasks_expanded()** (3 connections) — `tests/unit/test_parser.py`
- **.test_import_tasks_with_role_prefix()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_stderr_not_in_result()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_tasks_play_hosts_pattern_extraction()** (3 connections) — `tests/unit/test_parser.py`
- **.test_output_no_stderr_in_parsed_content()** (3 connections) — `tests/unit/test_parser.py`
- **.test_pre_tasks_post_tasks_no_prefix()** (3 connections) — `tests/unit/test_parser.py`
- **.test_special_section_names_in_play()** (3 connections) — `tests/unit/test_parser.py`
- **.test_unnamed_task_fallback_module_name()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_tasks_play_id_sequential()** (3 connections) — `tests/unit/test_parser.py`
- **.test_empty_tags()** (3 connections) — `tests/unit/test_parser.py`
- **.test_include_tasks_not_expanded()** (3 connections) — `tests/unit/test_parser.py`
- **.test_multiple_plays()** (3 connections) — `tests/unit/test_parser.py`
- **.test_no_json_output()** (3 connections) — `tests/unit/test_parser.py`
- **.test_play_indent_recognition()** (3 connections) — `tests/unit/test_parser.py`
- **.test_playbook_header_skipped()** (3 connections) — `tests/unit/test_parser.py`
- **.test_role_prefix_extraction()** (3 connections) — `tests/unit/test_parser.py`
- **.test_tab_separator_used()** (3 connections) — `tests/unit/test_parser.py`
- **.test_task_indent_recognition()** (3 connections) — `tests/unit/test_parser.py`
- *... and 29 more nodes in this community*

## Relationships

- [WarningType](WarningType.md) (10 shared connections)
- [HostRunState](HostRunState.md) (8 shared connections)
- [TaskDefinition](TaskDefinition.md) (4 shared connections)
- [StreamPhase](StreamPhase.md) (3 shared connections)
- [PtyStreamParser](PtyStreamParser.md) (3 shared connections)
- [assemble_definitions](assemble_definitions.md) (2 shared connections)
- [PlayDefinition](PlayDefinition.md) (2 shared connections)
- [JsonLineStream](JsonLineStream.md) (2 shared connections)
- [IncludeCacheEntry](IncludeCacheEntry.md) (1 shared connections)
- [run_preflight](run_preflight.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 158 (87%)
- INFERRED: 24 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*