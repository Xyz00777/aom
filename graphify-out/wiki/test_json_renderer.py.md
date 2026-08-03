# test_json_renderer.py

> 34 nodes · cohesion 0.07

## Key Concepts

- **test_json_renderer.py** (25 connections) — `tests/unit/test_json_renderer.py`
- **_state_two_hosts_one_failure()** (12 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_aggregates_per_host_counts()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_emits_one_json_object()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_lists_failed_tasks()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_uses_state_timestamps()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_satisfies_renderer_protocol()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_empty_state_emits_zero_exit()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_records_playbook_and_exit_code()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_schema_version_is_one()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_interactive_prompt_refuses_to_stderr()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_noop_methods_emit_nothing()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_set_definitions_stores_them()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_start_records_playbook_and_args()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_through_full_lifecycle()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_password_prompt_refuses_to_stderr()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_prompt_refusal_does_not_corrupt_completion_json()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_run_summary_schema_version_is_literal_one()** (2 connections) — `tests/unit/test_json_renderer.py`
- **Unit tests for the JSON output renderer (F6).** (1 connections) — `tests/unit/test_json_renderer.py`
- **web1: 2 ok + 1 changed; web2: 1 ok + 1 failed (msg='boom').** (1 connections) — `tests/unit/test_json_renderer.py`
- **The renderer prints exactly one JSON object on stdout.** (1 connections) — `tests/unit/test_json_renderer.py`
- **started_at / ended_at come from RunState when present.** (1 connections) — `tests/unit/test_json_renderer.py`
- **Hosts dict has one entry per host with summed counts across tasks.** (1 connections) — `tests/unit/test_json_renderer.py`
- **tasks_failed names host, task, and the failure message.** (1 connections) — `tests/unit/test_json_renderer.py`
- **An empty RunState produces a valid JSON with exit_code=0 and empty hosts.** (1 connections) — `tests/unit/test_json_renderer.py`
- *... and 9 more nodes in this community*

## Relationships

- [HostRunState](HostRunState.md) (20 shared connections)
- [create_renderer](create_renderer.md) (3 shared connections)
- [json.py](json.py.md) (2 shared connections)
- [RunState](RunState.md) (1 shared connections)
- [Renderer](Renderer.md) (1 shared connections)

## Source Files

- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 85 (81%)
- INFERRED: 20 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*