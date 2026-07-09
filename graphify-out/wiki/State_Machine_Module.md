# State Machine Module

> 60 nodes · cohesion 0.05

## Key Concepts

- **run_preflight()** (21 connections) — `src/ansible_aom/ansible/preflight.py`
- **assemble_definitions()** (14 connections) — `src/ansible_aom/ansible/preflight.py`
- **test_preflight.py** (12 connections) — `tests/unit/test_preflight.py`
- **test_preflight_runner.py** (11 connections) — `tests/integration/test_preflight_runner.py`
- **Path** (10 connections)
- **_trim_stderr()** (8 connections) — `src/ansible_aom/ansible/preflight.py`
- **preflight.py** (6 connections) — `src/ansible_aom/ansible/preflight.py`
- **_make_fake_ansible()** (5 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_grafts_include_children_into_definitions()** (5 connections) — `tests/integration/test_preflight_runner.py`
- **.test_assemble_definitions_transfers_resolved_hosts()** (5 connections) — `tests/unit/test_host_resolution.py`
- **test_assemble_definitions_combines_tasks_and_hosts()** (5 connections) — `tests/unit/test_preflight.py`
- **_spawn_one()** (4 connections) — `src/ansible_aom/ansible/preflight.py`
- **test_run_preflight_list_hosts_failure_yields_definitions_without_resolved_hosts()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_passes_ansible_args()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_populates_include_cache()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_role_relative_include_resolves_under_role()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_runs_both_commands_and_assembles_definitions()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_sets_ansible_nocolor_env()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_trims_argparse_help_wall_from_error()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_assemble_definitions_invokes_role_grouping()** (4 connections) — `tests/unit/test_preflight.py`
- **_preflight_env()** (3 connections) — `src/ansible_aom/ansible/preflight.py`
- **test_run_preflight_executable_not_found_records_error()** (3 connections) — `tests/integration/test_preflight_runner.py`
- **.test_assemble_definitions_with_empty_play_hosts_yields_empty()** (3 connections) — `tests/unit/test_host_resolution.py`
- **.test_assemble_definitions_no_match_yields_empty_resolved_hosts()** (3 connections) — `tests/unit/test_host_resolution.py`
- **.test_resolved_hosts_empty_when_list_hosts_blank()** (3 connections) — `tests/unit/test_host_resolution.py`
- *... and 35 more nodes in this community*

## Relationships

- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (4 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (4 shared connections)
- [Diagnostics and Profiler](Diagnostics_and_Profiler.md) (3 shared connections)
- [List Hosts Output Parser](List_Hosts_Output_Parser.md) (3 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (2 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (1 shared connections)
- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (1 shared connections)
- [Free Strategy Task Header](Free_Strategy_Task_Header.md) (1 shared connections)
- [JSONL Parse Failure Handling](JSONL_Parse_Failure_Handling.md) (1 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (1 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/preflight.py`
- `tests/integration/test_preflight_runner.py`
- `tests/unit/test_host_resolution.py`
- `tests/unit/test_preflight.py`

## Audit Trail

- EXTRACTED: 140 (69%)
- INFERRED: 62 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*