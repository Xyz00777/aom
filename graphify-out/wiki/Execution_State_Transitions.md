# Execution State Transitions

> 30 nodes · cohesion 0.13

## Key Concepts

- **test_task_completion.py** (18 connections) — `tests/unit/test_task_completion.py`
- **task_complete_on_all_targets()** (16 connections) — `src/ansible_aom/core/tree_projection.py`
- **_state()** (11 connections) — `tests/unit/test_task_completion.py`
- **_ran_ok()** (10 connections) — `tests/unit/test_task_completion.py`
- **test_dead_host_does_not_block_later_task()** (7 connections) — `tests/unit/test_task_completion.py`
- **test_all_hosts_failed_in_task_is_complete()** (6 connections) — `tests/unit/test_task_completion.py`
- **test_running_host_blocks_completion()** (6 connections) — `tests/unit/test_task_completion.py`
- **_runner_start()** (5 connections) — `tests/unit/test_task_completion.py`
- **test_early_task_not_complete_before_slow_targets_start()** (5 connections) — `tests/unit/test_task_completion.py`
- **test_incomplete_while_a_target_host_has_not_finished()** (5 connections) — `tests/unit/test_task_completion.py`
- **test_no_target_information_is_not_complete()** (5 connections) — `tests/unit/test_task_completion.py`
- **test_complete_when_all_targets_terminal()** (4 connections) — `tests/unit/test_task_completion.py`
- **play_dead_hosts()** (3 connections) — `src/ansible_aom/core/tree_projection.py`
- **_play_def_for_state()** (3 connections) — `src/ansible_aom/core/tree_projection.py`
- **_failed()** (3 connections) — `tests/unit/test_task_completion.py`
- **_play_def()** (3 connections) — `tests/unit/test_task_completion.py`
- **_play_start()** (3 connections) — `tests/unit/test_task_completion.py`
- **test_unknown_task_is_not_complete()** (3 connections) — `tests/unit/test_task_completion.py`
- **_ok()** (2 connections) — `tests/unit/test_task_completion.py`
- **Resolve a runtime play to its preflight PlayDefinition.      Mirrors ``TreeProje** (1 connections) — `src/ansible_aom/core/tree_projection.py`
- **Hosts that went FAILED/UNREACHABLE anywhere in ``play``.      Ansible drops thes** (1 connections) — `src/ansible_aom/core/tree_projection.py`
- **True when every live target host has finished ``task_uuid``.      "Live targets"** (1 connections) — `src/ansible_aom/core/tree_projection.py`
- **Tests for ``task_complete_on_all_targets`` — the full-play-completion predicate** (1 connections) — `tests/unit/test_task_completion.py`
- **The undercount guard: with a fork limit, a fast cohort finishes     the task whi** (1 connections) — `tests/unit/test_task_completion.py`
- **A host that died *in* this task finished it (by failing) and is     counted — an** (1 connections) — `tests/unit/test_task_completion.py`
- *... and 5 more nodes in this community*

## Relationships

- [tree.py](tree.py.md) (5 shared connections)
- [RunState](RunState.md) (3 shared connections)
- [._emit_event_log](_emit_event_log.md) (2 shared connections)
- [renderer.py](renderer.py.md) (1 shared connections)
- [HostRunState](HostRunState.md) (1 shared connections)
- [PlayDefinition](PlayDefinition.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/tree_projection.py`
- `tests/unit/test_task_completion.py`

## Audit Trail

- EXTRACTED: 129 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*