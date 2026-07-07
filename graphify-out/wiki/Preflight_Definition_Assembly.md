# Preflight Definition Assembly

> 24 nodes · cohesion 0.11

## Key Concepts

- **assemble_definitions()** (14 connections) — `src/ansible_aom/ansible/preflight.py`
- **test_preflight.py** (12 connections) — `tests/unit/test_preflight.py`
- **_trim_stderr()** (8 connections) — `src/ansible_aom/ansible/preflight.py`
- **test_assemble_definitions_combines_tasks_and_hosts()** (5 connections) — `tests/unit/test_preflight.py`
- **test_assemble_definitions_invokes_role_grouping()** (3 connections) — `tests/unit/test_preflight.py`
- **test_assemble_definitions_missing_host_data_yields_empty_resolved_hosts()** (3 connections) — `tests/unit/test_preflight.py`
- **test_preparseresult_definitions_and_errors_default_to_empty()** (3 connections) — `tests/unit/test_preflight.py`
- **test_preparseresult_has_definitions_and_errors_fields()** (3 connections) — `tests/unit/test_preflight.py`
- **test_trim_stderr_extracts_only_error_line_from_argparse_wall()** (3 connections) — `tests/unit/test_preflight.py`
- **test_trim_stderr_falls_back_to_first_lines_without_error_marker()** (3 connections) — `tests/unit/test_preflight.py`
- **test_assemble_definitions_empty_inputs_returns_empty_list()** (2 connections) — `tests/unit/test_preflight.py`
- **test_trim_stderr_empty_returns_empty()** (2 connections) — `tests/unit/test_preflight.py`
- **test_trim_stderr_handles_multiple_error_lines()** (2 connections) — `tests/unit/test_preflight.py`
- **test_trim_stderr_returns_short_message_unchanged()** (2 connections) — `tests/unit/test_preflight.py`
- **Reduce ansible-playbook stderr to the diagnostic lines worth showing.      Argpa** (1 connections) — `src/ansible_aom/ansible/preflight.py`
- **Build PlayDefinition objects from parsed --list-tasks / --list-hosts dicts.** (1 connections) — `src/ansible_aom/ansible/preflight.py`
- **Tests for the pre-flight orchestrator (--list-tasks + --list-hosts).** (1 connections) — `tests/unit/test_preflight.py`
- **When there's no `: error:` marker, keep the first few non-empty lines, capped.** (1 connections) — `tests/unit/test_preflight.py`
- **5+ consecutive same-role tasks collapse into a RoleGroupDefinition.** (1 connections) — `tests/unit/test_preflight.py`
- **The new fields are optional with empty defaults so old call sites still work.** (1 connections) — `tests/unit/test_preflight.py`
- **assemble_definitions builds a PlayDefinition per play with tasks + resolved_host** (1 connections) — `tests/unit/test_preflight.py`
- **When --list-hosts has no entry for a play, resolved_hosts stays empty.** (1 connections) — `tests/unit/test_preflight.py`
- **ansible-playbook on bad args dumps usage + error + full --help. Keep only error.** (1 connections) — `tests/unit/test_preflight.py`
- **PreParseResult exposes assembled definitions plus an errors list.** (1 connections) — `tests/unit/test_preflight.py`

## Relationships

- [[Role Group Task Models]] (3 shared connections)
- [[Preflight Env Subprocess]] (2 shared connections)
- [[Parallel Pre-flight Runner]] (2 shared connections)
- [[Play Definition Tree Population]] (1 shared connections)
- [[Task Definition Live Refresh]] (1 shared connections)
- [[List Hosts Output Parser]] (1 shared connections)
- [[List Tasks Output Parser]] (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/preflight.py`
- `tests/unit/test_preflight.py`

## Audit Trail

- EXTRACTED: 47 (63%)
- INFERRED: 28 (37%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*