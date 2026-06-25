# List Tasks Output Parser

> 43 nodes · cohesion 0.05

## Key Concepts

- **parse_list_tasks_output()** (30 connections) — `src/ansible_aom/core/parser.py`
- **.test_exit_code_error_output()** (3 connections) — `tests/unit/test_parser.py`
- **.test_exit_code_success_output()** (3 connections) — `tests/unit/test_parser.py`
- **.test_exit_code_syntax_error_output()** (3 connections) — `tests/unit/test_parser.py`
- **.test_import_tasks_expanded()** (3 connections) — `tests/unit/test_parser.py`
- **.test_import_tasks_with_role_prefix()** (3 connections) — `tests/unit/test_parser.py`
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
- **.test_role_prefix_extraction()** (3 connections) — `tests/unit/test_parser.py`
- **.test_tab_separator_used()** (3 connections) — `tests/unit/test_parser.py`
- **.test_task_indent_recognition()** (3 connections) — `tests/unit/test_parser.py`
- **.test_task_tags_extraction()** (3 connections) — `tests/unit/test_parser.py`
- **.test_task_without_role()** (3 connections) — `tests/unit/test_parser.py`
- **TC-114: import_tasks IS expanded — tasks appear inline in --list-tasks.** (1 connections) — `tests/unit/test_parser.py`
- **TC-116: pre_tasks and post_tasks appear as regular tasks.** (1 connections) — `tests/unit/test_parser.py`
- **TC-117: Unnamed tasks use their module/action as the name.** (1 connections) — `tests/unit/test_parser.py`
- *... and 18 more nodes in this community*

## Relationships

- [[Role Group Task Models]] (22 shared connections)
- [[List Hosts Output Parser]] (2 shared connections)
- [[Parallel Pre-flight Runner]] (1 shared connections)
- [[Block Task Flattening]] (1 shared connections)
- [[PreParseResult Assembly]] (1 shared connections)
- [[Playbook Header Parsing]] (1 shared connections)
- [[Preflight Definition Assembly]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 66 (58%)
- INFERRED: 48 (42%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*