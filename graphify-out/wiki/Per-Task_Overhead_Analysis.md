# Per-Task Overhead Analysis

> 31 nodes · cohesion 0.12

## Key Concepts

- **datetime** (15 connections)
- **._task_dict()** (13 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_failed()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_ok()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_skipped()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_on_unreachable()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **._resolve_play_id()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **._resolve_runner_task()** (11 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_runner_item_on()** (9 connections) — `src/ansible_aom/core/run_state.py`
- **._hosts_dict()** (9 connections) — `src/ansible_aom/core/run_state.py`
- **._note_unmatched()** (8 connections) — `src/ansible_aom/core/run_state.py`
- **._prior_host_start_time()** (8 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_playbook_on_handler_task_start()** (5 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_playbook_on_stats()** (5 connections) — `src/ansible_aom/core/run_state.py`
- **._handle_v2_playbook_on_start()** (4 connections) — `src/ansible_aom/core/run_state.py`
- **._resolve_play_for_task()** (4 connections) — `src/ansible_aom/core/run_state.py`
- **Handle v2_playbook_on_handler_task_start event (same as task_start).** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Handle a per-item loop event (``v2_runner_item_on_*``).          These are addit** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Extract the ``task`` field as a dict.          ansible.posix.jsonl may emit ``ta** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Extract the ``hosts`` field as a dict.          mitogen bulk-reconnect events ca** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Carry the host's recorded start_time into a terminal HostRunState.          Term** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Handle v2_runner_on_ok event.** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Handle v2_runner_on_failed event.** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Handle v2_runner_on_skipped event.** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Handle v2_runner_on_unreachable event.** (1 connections) — `src/ansible_aom/core/run_state.py`
- *... and 6 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (22 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (15 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (13 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (3 shared connections)
- [Unknown Event Hint](Unknown_Event_Hint.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/run_state.py`

## Audit Trail

- EXTRACTED: 166 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*