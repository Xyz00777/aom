# Runtime Event Handlers

> 28 nodes · cohesion 0.10

## Key Concepts

- **._handle_v2_playbook_on_task_start()** (14 connections) — `src/ansible_aom/core/models.py`
- **._handle_v2_runner_on_start()** (12 connections) — `src/ansible_aom/core/models.py`
- **._resolve_play_id()** (11 connections) — `src/ansible_aom/core/models.py`
- **._task_dict()** (10 connections) — `src/ansible_aom/core/models.py`
- **._handle_v2_runner_item_on()** (8 connections) — `src/ansible_aom/core/models.py`
- **._handle_v2_runner_on_failed()** (8 connections) — `src/ansible_aom/core/models.py`
- **._handle_v2_runner_on_ok()** (8 connections) — `src/ansible_aom/core/models.py`
- **._handle_v2_runner_on_skipped()** (8 connections) — `src/ansible_aom/core/models.py`
- **._handle_v2_runner_on_unreachable()** (8 connections) — `src/ansible_aom/core/models.py`
- **._hosts_dict()** (8 connections) — `src/ansible_aom/core/models.py`
- **._handle_v2_playbook_on_handler_task_start()** (5 connections) — `src/ansible_aom/core/models.py`
- **._parent_role_from_cache()** (5 connections) — `src/ansible_aom/core/models.py`
- **._resolve_play_for_task()** (3 connections) — `src/ansible_aom/core/models.py`
- **._resolve_play_hosts()** (3 connections) — `src/ansible_aom/core/models.py`
- **Handle v2_runner_on_skipped event.** (1 connections) — `src/ansible_aom/core/models.py`
- **Handle v2_runner_on_unreachable event.** (1 connections) — `src/ansible_aom/core/models.py`
- **Return the play_id that already owns this task_id, or ``None``.          Searche** (1 connections) — `src/ansible_aom/core/models.py`
- **Resolve play_id from event, _current_play_id, or task ownership.          Resolu** (1 connections) — `src/ansible_aom/core/models.py`
- **Return the parent role recorded in ``_role_cache`` for a runtime task.** (1 connections) — `src/ansible_aom/core/models.py`
- **Handle v2_playbook_on_task_start event.** (1 connections) — `src/ansible_aom/core/models.py`
- **Look up preflight resolved_hosts for a runtime play.          Preflight assigns** (1 connections) — `src/ansible_aom/core/models.py`
- **Handle v2_playbook_on_handler_task_start event (same as task_start).** (1 connections) — `src/ansible_aom/core/models.py`
- **Handle v2_runner_on_start event.** (1 connections) — `src/ansible_aom/core/models.py`
- **Handle a per-item loop event (``v2_runner_item_on_*``).          These are addit** (1 connections) — `src/ansible_aom/core/models.py`
- **Extract the ``task`` field as a dict.          ansible.posix.jsonl may emit ``ta** (1 connections) — `src/ansible_aom/core/models.py`
- *... and 3 more nodes in this community*

## Relationships

- [[Run State Summary Panel]] (14 shared connections)
- [[Playbook Event Parsing]] (11 shared connections)
- [[Run State Completion Recap]] (11 shared connections)
- [[Run History Mining]] (8 shared connections)
- [[Role Inference Indexes]] (3 shared connections)
- [[Include Role Discovery]] (2 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`

## Audit Trail

- EXTRACTED: 123 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*