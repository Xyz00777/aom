# TreeProjection

> 62 nodes · cohesion 0.08

## Key Concepts

- **TreeProjection** (62 connections) — `src/ansible_aom/core/tree_projection.py`
- **TreeLine** (38 connections) — `src/ansible_aom/core/tree_projection.py`
- **._emit_runtime_play()** (27 connections) — `src/ansible_aom/core/tree_projection.py`
- **datetime** (15 connections)
- **._tree_lines_unbounded()** (14 connections) — `src/ansible_aom/core/tree_projection.py`
- **iter_preflight_task_defs()** (12 connections) — `src/ansible_aom/core/models.py`
- **._build_role_total_tasks()** (12 connections) — `src/ansible_aom/core/tree_projection.py`
- **._emit_pending_play()** (11 connections) — `src/ansible_aom/core/tree_projection.py`
- **._touch_row_lease()** (10 connections) — `src/ansible_aom/core/tree_projection.py`
- **.tree_lines()** (10 connections) — `src/ansible_aom/core/tree_projection.py`
- **._recompute_inner_footer_count()** (9 connections) — `src/ansible_aom/core/tree_projection.py`
- **._touch_task_lease()** (9 connections) — `src/ansible_aom/core/tree_projection.py`
- **runtime_role_from_task_name()** (8 connections) — `src/ansible_aom/core/models.py`
- **_collapse_role_path_aggressive()** (8 connections) — `src/ansible_aom/core/tree_projection.py`
- **.host_rows()** (8 connections) — `src/ansible_aom/core/tree_projection.py`
- **._play_running_and_pending()** (8 connections) — `src/ansible_aom/core/tree_projection.py`
- **._play_runtime_identity()** (7 connections) — `src/ansible_aom/core/tree_projection.py`
- **._relabel_role_lines()** (7 connections) — `src/ansible_aom/core/tree_projection.py`
- **._role_total_preflight_for()** (6 connections) — `src/ansible_aom/core/tree_projection.py`
- **._task_line()** (6 connections) — `src/ansible_aom/core/tree_projection.py`
- **._task_runtime_identity()** (6 connections) — `src/ansible_aom/core/tree_projection.py`
- **._touch_play_leases()** (6 connections) — `src/ansible_aom/core/tree_projection.py`
- **_leaf_elapsed_s()** (5 connections) — `src/ansible_aom/core/tree_projection.py`
- **._count_visible_tasks_per_role()** (5 connections) — `src/ansible_aom/core/tree_projection.py`
- **._leased_play_id()** (5 connections) — `src/ansible_aom/core/tree_projection.py`
- *... and 37 more nodes in this community*

## Relationships

- [HostRunState](HostRunState.md) (26 shared connections)
- [tree.py](tree.py.md) (24 shared connections)
- [strip_role_prefix](strip_role_prefix.md) (11 shared connections)
- [TaskDefinition](TaskDefinition.md) (8 shared connections)
- [PlayDefinition](PlayDefinition.md) (6 shared connections)
- [Rerun Host Set Composition](Rerun_Host_Set_Composition.md) (5 shared connections)
- [test_tree_render.py](test_tree_render.py.md) (4 shared connections)
- [AOM TUI Application](AOM_TUI_Application.md) (4 shared connections)
- [RunState](RunState.md) (3 shared connections)
- [.test_default_is_false_for_keyword_construction](test_default_is_false_for_keyword_construction.md) (3 shared connections)
- [json.py](json.py.md) (2 shared connections)
- [TestMultiPlayTruncationWithRoleFooters](TestMultiPlayTruncationWithRoleFooters.md) (2 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/tree_projection.py`
- `tests/unit/test_tree_projection.py`

## Audit Trail

- EXTRACTED: 356 (90%)
- INFERRED: 38 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*