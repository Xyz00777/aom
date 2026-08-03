# Shared Renderer Types

> 27 nodes · cohesion 0.11

## Key Concepts

- **parse_jsonl_output()** (31 connections) — `tests/integration/test_playbook_parser.py`
- **run_ansible_playbook()** (29 connections) — `tests/integration/test_playbook_parser.py`
- **.test_import_tasks_expands_statically()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **.test_include_tasks_expands_dynamically()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **.test_mixed_warnings_and_execution()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **.test_mixed_warnings_continue_after_ignore()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **.test_tags_all_runs_all_tasks()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **.test_tags_filter_runs_subset_of_tasks()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **.test_tags_filter_skips_untagged_tasks()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **.test_unreachable_host_detected()** (4 connections) — `tests/integration/test_playbook_parser.py`
- **.test_block_tasks_complete_and_expand()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_free_strategy_tracks_all_tasks()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_host_pattern_limits_hosts()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_multiple_plays_round_trip()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_role_grouping_completes_and_collects_role_tasks()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_localhost_connection_and_host_count()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_single_task_success_round_trip()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **Run ansible-playbook with JSONL callback and capture output.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Parser correctly handles unreachable host.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **--tags install runs only install-tagged tasks.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **--tags configure runs only configure-tagged tasks.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **--tags all runs every task regardless of tag.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **include_tasks expands dynamic tasks at runtime.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **import_tasks expands static tasks before execution.** (1 connections) — `tests/integration/test_playbook_parser.py`
- **Playbook with warnings and execution completes.** (1 connections) — `tests/integration/test_playbook_parser.py`
- *... and 2 more nodes in this community*

## Relationships

- [Role Group Task Models](Role_Group_Task_Models.md) (17 shared connections)
- [Rerun Main Function](Rerun_Main_Function.md) (4 shared connections)
- [Real Ansible Integration](Real_Ansible_Integration.md) (4 shared connections)
- [Compact Display Module Layout](Compact_Display_Module_Layout.md) (4 shared connections)
- [No Record Flag](No_Record_Flag.md) (4 shared connections)
- [Build Rerun Command](Build_Rerun_Command.md) (2 shared connections)
- [Failure Recap Formatting](Failure_Recap_Formatting.md) (2 shared connections)
- [Ansible Posix Version Check](Ansible_Posix_Version_Check.md) (2 shared connections)
- [Unicode Support Detection](Unicode_Support_Detection.md) (2 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (1 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (1 shared connections)

## Source Files

- `tests/integration/test_playbook_parser.py`

## Audit Trail

- EXTRACTED: 123 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*