# Play Tree Projection

> 16 nodes · cohesion 0.21

## Key Concepts

- **._emit_runtime_play()** (22 connections) — `src/ansible_aom/core/tree.py`
- **._tree_lines_unbounded()** (14 connections) — `src/ansible_aom/core/tree.py`
- **datetime** (13 connections)
- **._emit_pending_play()** (10 connections) — `src/ansible_aom/core/tree.py`
- **._touch_row_lease()** (10 connections) — `src/ansible_aom/core/tree.py`
- **._touch_task_lease()** (9 connections) — `src/ansible_aom/core/tree.py`
- **._play_runtime_identity()** (7 connections) — `src/ansible_aom/core/tree.py`
- **_collapse_role_path_aggressive()** (6 connections) — `src/ansible_aom/core/tree.py`
- **._touch_play_leases()** (6 connections) — `src/ansible_aom/core/tree.py`
- **._leased_play_id()** (5 connections) — `src/ansible_aom/core/tree.py`
- **._task_runtime_identity()** (5 connections) — `src/ansible_aom/core/tree.py`
- **._touch_host_lease()** (5 connections) — `src/ansible_aom/core/tree.py`
- **._touch_role_lease()** (5 connections) — `src/ansible_aom/core/tree.py`
- **.is_tree_visible()** (3 connections) — `src/ansible_aom/core/tree.py`
- **._play_lease_alive()** (3 connections) — `src/ansible_aom/core/tree.py`
- **Drop any element that duplicates an earlier element of the path.      Stricter t** (1 connections) — `src/ansible_aom/core/tree.py`

## Relationships

- [[Tree Projection Logic]] (24 shared connections)
- [[Run State Completion Recap]] (8 shared connections)
- [[Role Chain Extraction]] (6 shared connections)
- [[Tree Projection Utilities]] (4 shared connections)
- [[Play Definition Tree Population]] (3 shared connections)
- [[Role Inference Indexes]] (2 shared connections)
- [[Role Group Task Models]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/tree.py`

## Audit Trail

- EXTRACTED: 120 (97%)
- INFERRED: 4 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*