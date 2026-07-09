# List Hosts Output Parser

> 52 nodes · cohesion 0.05

## Key Concepts

- **parse_list_tasks_output()** (30 connections) — `src/ansible_aom/core/parser.py`
- **TestListTasksEdgeCases** (26 connections) — `tests/unit/test_parser.py`
- **TestListTasksParser** (25 connections) — `tests/unit/test_parser.py`
- **.test_blocks_flattened()** (3 connections) — `tests/unit/test_parser.py`
- **.test_exit_code_error_output()** (3 connections) — `tests/unit/test_parser.py`
- **.test_exit_code_success_output()** (3 connections) — `tests/unit/test_parser.py`
- **.test_exit_code_syntax_error_output()** (3 connections) — `tests/unit/test_parser.py`
- **.test_import_tasks_expanded()** (3 connections) — `tests/unit/test_parser.py`
- **.test_import_tasks_with_role_prefix()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_hosts_stderr_not_in_result()** (3 connections) — `tests/unit/test_parser.py`
- **.test_list_tasks_play_hosts_pattern_extraction()** (3 connections) — `tests/unit/test_parser.py`
- **.test_output_no_stderr_in_parsed_content()** (3 connections) — `tests/unit/test_parser.py`
- **.test_pre_tasks_post_tasks_no_prefix()** (3 connections) — `tests/unit/test_parser.py`
- **.test_special_section_names_in_play()** (3 connections) — `tests/unit/test_parser.py`
- **.test_unnamed_task_fallback_module_name()** (3 connections) — `tests/unit/test_parser.py`
- **.test_empty_tags()** (3 connections) — `tests/unit/test_parser.py`
- **.test_include_tasks_not_expanded()** (3 connections) — `tests/unit/test_parser.py`
- **.test_multiple_plays()** (3 connections) — `tests/unit/test_parser.py`
- **.test_no_json_output()** (3 connections) — `tests/unit/test_parser.py`
- **.test_play_indent_recognition()** (3 connections) — `tests/unit/test_parser.py`
- **.test_playbook_header_skipped()** (3 connections) — `tests/unit/test_parser.py`
- **.test_role_prefix_extraction()** (3 connections) — `tests/unit/test_parser.py`
- **.test_tab_separator_used()** (3 connections) — `tests/unit/test_parser.py`
- **.test_task_indent_recognition()** (3 connections) — `tests/unit/test_parser.py`
- **.test_task_tags_extraction()** (3 connections) — `tests/unit/test_parser.py`
- *... and 27 more nodes in this community*

## Relationships

- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (7 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (6 shared connections)
- [State Machine Module](State_Machine_Module.md) (3 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (3 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (2 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (2 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (2 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (2 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)
- [Three-Pane Inspect App](Three-Pane_Inspect_App.md) (2 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (2 shared connections)
- [Diagnostics and Profiler](Diagnostics_and_Profiler.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 101 (57%)
- INFERRED: 75 (43%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*