# JSON Renderer

> 62 nodes · cohesion 0.04

## Key Concepts

- **JsonRenderer** (63 connections) — `src/ansible_aom/formats/json.py`
- **test_json_renderer.py** (26 connections) — `tests/unit/test_json_renderer.py`
- **_state_two_hosts_one_failure()** (12 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_unreachable_lands_in_tasks_failed()** (7 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_aggregates_per_host_counts()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_emits_one_json_object()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_lists_failed_tasks()** (4 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_uses_state_timestamps()** (4 connections) — `tests/unit/test_json_renderer.py`
- **.note_subprocess_active()** (3 connections) — `src/ansible_aom/formats/json.py`
- **.start()** (3 connections) — `src/ansible_aom/formats/json.py`
- **test_handle_completion_empty_state_emits_zero_exit()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_records_playbook_and_exit_code()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_schema_version_is_one()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_interactive_prompt_refuses_to_stderr()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_noop_methods_emit_nothing()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_satisfies_renderer_protocol()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_set_definitions_stores_them()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_start_records_playbook_and_args()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_through_full_lifecycle()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_password_prompt_refuses_to_stderr()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_prompt_refusal_does_not_corrupt_completion_json()** (3 connections) — `tests/unit/test_json_renderer.py`
- **.add_warning()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.handle_interactive_prompt()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.handle_password_prompt()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.note_pty_bytes()** (2 connections) — `src/ansible_aom/formats/json.py`
- *... and 37 more nodes in this community*

## Relationships

- [[CLI Interface Tests]] (17 shared connections)
- [[Run State Completion Recap]] (10 shared connections)
- [[Renderer Factory Function]] (5 shared connections)
- [[Run State Summary Panel]] (4 shared connections)
- [[JSON Output Renderer]] (3 shared connections)
- [[Replay Determinism Tests]] (2 shared connections)
- [[CLI Argument Parser]] (2 shared connections)
- [[Role Group Task Models]] (1 shared connections)
- [[Renderer Parity Invariant]] (1 shared connections)
- [[Install Completion Flag]] (1 shared connections)
- [[Renderer Protocol Tests]] (1 shared connections)
- [[Renderer Stats Parity]] (1 shared connections)

## Source Files

- `src/ansible_aom/formats/json.py`
- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 144 (67%)
- INFERRED: 72 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*