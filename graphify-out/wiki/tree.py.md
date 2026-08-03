# tree.py

> 37 nodes · cohesion 0.09

## Key Concepts

- **tree.py** (48 connections) — `src/ansible_aom/core/tree.py`
- **tree_projection.py** (42 connections) — `src/ansible_aom/core/tree_projection.py`
- **run_state_status_counts()** (10 connections) — `src/ansible_aom/core/tree.py`
- **_effective_status()** (9 connections) — `src/ansible_aom/core/tree_projection.py`
- **test_status_tally.py** (8 connections) — `tests/unit/test_status_tally.py`
- **_run_state()** (8 connections) — `tests/unit/test_status_tally.py`
- **_truncate_two_level()** (7 connections) — `src/ansible_aom/core/tree_projection.py`
- **_is_meta_task()** (6 connections) — `src/ansible_aom/core/tree_projection.py`
- **_more_footer()** (6 connections) — `src/ansible_aom/core/tree_projection.py`
- **_play_target_hostnames()** (6 connections) — `src/ansible_aom/core/tree_projection.py`
- **run_state_host_counts()** (6 connections) — `src/ansible_aom/core/tree.py`
- **_count_domain_entities()** (5 connections) — `src/ansible_aom/core/tree_projection.py`
- **_host_leaf_label()** (5 connections) — `src/ansible_aom/core/tree_projection.py`
- **_name_role_chain()** (5 connections) — `src/ansible_aom/core/tree_projection.py`
- **_pending_host_count()** (5 connections) — `src/ansible_aom/core/tree_projection.py`
- **_bump()** (4 connections) — `src/ansible_aom/core/tree.py`
- **_collapse_role_path()** (4 connections) — `src/ansible_aom/core/tree_projection.py`
- **_leaf_visible()** (4 connections) — `src/ansible_aom/core/tree_projection.py`
- **test_aggregate_status_counts()** (4 connections) — `tests/unit/test_status_tally.py`
- **test_per_host_status_counts()** (4 connections) — `tests/unit/test_status_tally.py`
- **_template_skeleton()** (3 connections) — `src/ansible_aom/core/tree_projection.py`
- **Host-leaf visibility under a running task.      RUNNING leaves are the tree's pa** (2 connections) — `src/ansible_aom/core/tree_projection.py`
- **Pure projection of RunState into renderable tree + host-row data.  This module c** (1 connections) — `src/ansible_aom/core/tree_projection.py`
- **Extract the role chain encoded in a task name's ``" : "`` segments.      ansible** (1 connections) — `src/ansible_aom/core/tree_projection.py`
- **Collect hostnames targeted by this play (read-only).      Uses ``play_def.resolv** (1 connections) — `src/ansible_aom/core/tree_projection.py`
- *... and 12 more nodes in this community*

## Relationships

- [TreeProjection](TreeProjection.md) (24 shared connections)
- [HostRunState](HostRunState.md) (23 shared connections)
- [StatusCounts](StatusCounts.md) (6 shared connections)
- [TaskDefinition](TaskDefinition.md) (5 shared connections)
- [strip_role_prefix](strip_role_prefix.md) (5 shared connections)
- [Execution State Transitions](Execution_State_Transitions.md) (5 shared connections)
- [renderer.py](renderer.py.md) (4 shared connections)
- [RunState](RunState.md) (4 shared connections)
- [.from_run_state](from_run_state.md) (3 shared connections)
- [inspect_model.py](inspect_model.py.md) (2 shared connections)
- [json.py](json.py.md) (2 shared connections)
- [format_tree_block](format_tree_block.md) (2 shared connections)

## Source Files

- `src/ansible_aom/core/tree.py`
- `src/ansible_aom/core/tree_projection.py`
- `tests/unit/test_status_tally.py`

## Audit Trail

- EXTRACTED: 215 (100%)
- INFERRED: 1 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*