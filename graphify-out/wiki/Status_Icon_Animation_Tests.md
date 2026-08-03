# Status Icon Animation Tests

> 45 nodes · cohesion 0.07

## Key Concepts

- **run_state.py** (64 connections) — `src/ansible_aom/core/run_state.py`
- **_BoundedDict** (18 connections) — `src/ansible_aom/core/run_state.py`
- **_BoundedSet** (18 connections) — `src/ansible_aom/core/run_state.py`
- **event_types.py** (14 connections) — `src/ansible_aom/core/event_types.py`
- **JsonlTask** (14 connections) — `src/ansible_aom/core/event_types.py`
- **._graft_or_match_task()** (11 connections) — `src/ansible_aom/core/run_state.py`
- **_iter_leaf_task_defs()** (10 connections) — `src/ansible_aom/core/run_state.py`
- **JsonlHostResult** (8 connections) — `src/ansible_aom/core/event_types.py`
- **JsonlPlay** (8 connections) — `src/ansible_aom/core/event_types.py`
- **._graft_role_pending_siblings()** (8 connections) — `src/ansible_aom/core/run_state.py`
- **count_leaf_tasks()** (7 connections) — `src/ansible_aom/core/run_state.py`
- **_iter_task_def_tree()** (6 connections) — `src/ansible_aom/core/models.py`
- **_leaves_of_role_group()** (6 connections) — `src/ansible_aom/core/run_state.py`
- **._bump_tree_revision()** (5 connections) — `src/ansible_aom/core/run_state.py`
- **TypedDict** (5 connections)
- **_parse_play_window_start()** (4 connections) — `src/ansible_aom/core/run_state.py`
- **._rebuild_definition_indexes()** (4 connections) — `src/ansible_aom/core/run_state.py`
- **.__setattr__()** (4 connections) — `src/ansible_aom/core/run_state.py`
- **JsonlHostStats** (3 connections) — `src/ansible_aom/core/event_types.py`
- **.add()** (3 connections) — `src/ansible_aom/core/run_state.py`
- **_extract_role_from_include_stub()** (3 connections) — `src/ansible_aom/core/run_state.py`
- **.__init__()** (2 connections) — `src/ansible_aom/core/run_state.py`
- **.__init__()** (2 connections) — `src/ansible_aom/core/run_state.py`
- **dict** (1 connections)
- **TypedDict for the JSONL event structure emitted by ``ansible.posix.jsonl``.  AOM** (1 connections) — `src/ansible_aom/core/event_types.py`
- *... and 20 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (28 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (14 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (8 shared connections)
- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (6 shared connections)
- [Hide State Gating Tests](Hide_State_Gating_Tests.md) (6 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (5 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (5 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (3 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (3 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (3 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (3 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (3 shared connections)

## Source Files

- `src/ansible_aom/core/event_types.py`
- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/run_state.py`

## Audit Trail

- EXTRACTED: 200 (80%)
- INFERRED: 49 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*