# run_preflight

> 26 nodes · cohesion 0.14

## Key Concepts

- **run_preflight()** (22 connections) — `src/ansible_aom/ansible/preflight.py`
- **test_preflight_runner.py** (11 connections) — `tests/integration/test_preflight_runner.py`
- **Path** (10 connections)
- **_make_fake_ansible()** (5 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_grafts_include_children_into_definitions()** (5 connections) — `tests/integration/test_preflight_runner.py`
- **_spawn_one()** (4 connections) — `src/ansible_aom/ansible/preflight.py`
- **test_run_preflight_list_hosts_failure_yields_definitions_without_resolved_hosts()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_passes_ansible_args()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_populates_include_cache()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_role_relative_include_resolves_under_role()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_runs_both_commands_and_assembles_definitions()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_sets_ansible_nocolor_env()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **test_run_preflight_trims_argparse_help_wall_from_error()** (4 connections) — `tests/integration/test_preflight_runner.py`
- **_preflight_env()** (3 connections) — `src/ansible_aom/ansible/preflight.py`
- **test_run_preflight_executable_not_found_records_error()** (3 connections) — `tests/integration/test_preflight_runner.py`
- **Spawn a single ansible-playbook invocation; return (exit_code, stdout, stderr).** (1 connections) — `src/ansible_aom/ansible/preflight.py`
- **Run --list-tasks and --list-hosts in parallel; return assembled result.      Bot** (1 connections) — `src/ansible_aom/ansible/preflight.py`
- **Environment for preflight subprocesses.      `ANSIBLE_NOCOLOR=1` forces ansible-** (1 connections) — `src/ansible_aom/ansible/preflight.py`
- **Integration tests for run_preflight against a fake ansible-playbook.** (1 connections) — `tests/integration/test_preflight_runner.py`
- **ANSIBLE_NOCOLOR=1 must be set so ansible-playbook emits stderr without colours.** (1 connections) — `tests/integration/test_preflight_runner.py`
- **When ansible-playbook fails with an argparse error, only the error line surfaces** (1 connections) — `tests/integration/test_preflight_runner.py`
- **Args like -i inventory.ini must reach both subprocess invocations.** (1 connections) — `tests/integration/test_preflight_runner.py`
- **TC-094f: run_preflight populates include_cache for literal include_tasks.** (1 connections) — `tests/integration/test_preflight_runner.py`
- **Create a Python script that mimics ansible-playbook --list-tasks/--list-hosts.** (1 connections) — `tests/integration/test_preflight_runner.py`
- **TC-094g: grafted children appear on include_tasks stubs in definitions.** (1 connections) — `tests/integration/test_preflight_runner.py`
- *... and 1 more nodes in this community*

## Relationships

- [IncludeCacheEntry](IncludeCacheEntry.md) (6 shared connections)
- [assemble_definitions](assemble_definitions.md) (2 shared connections)
- [WarningType](WarningType.md) (2 shared connections)
- [run_playbook](run_playbook.md) (2 shared connections)
- [parse_list_tasks_output](parse_list_tasks_output.md) (1 shared connections)
- [TaskDefinition](TaskDefinition.md) (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/preflight.py`
- `tests/integration/test_preflight_runner.py`

## Audit Trail

- EXTRACTED: 81 (79%)
- INFERRED: 21 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*