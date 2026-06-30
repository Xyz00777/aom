# Tree Projection Logic

> 17 nodes · cohesion 0.12

## Key Concepts

- **TreeProjection** (102 connections) — `src/ansible_aom/core/tree.py`
- **iter_preflight_task_defs()** (10 connections) — `src/ansible_aom/core/models.py`
- **._build_role_total_tasks()** (10 connections) — `src/ansible_aom/core/tree.py`
- **.tree_lines()** (10 connections) — `src/ansible_aom/core/tree.py`
- **.host_rows()** (8 connections) — `src/ansible_aom/core/tree.py`
- **._recompute_inner_footer_count()** (8 connections) — `src/ansible_aom/core/tree.py`
- **._task_role()** (7 connections) — `src/ansible_aom/core/tree.py`
- **._relabel_role_lines()** (6 connections) — `src/ansible_aom/core/tree.py`
- **._count_visible_tasks_per_role()** (5 connections) — `src/ansible_aom/core/tree.py`
- **._refresh_tree_cache()** (5 connections) — `src/ansible_aom/core/tree.py`
- **._remember_running_play()** (5 connections) — `src/ansible_aom/core/tree.py`
- **._prune_row_leases()** (4 connections) — `src/ansible_aom/core/tree.py`
- **._play_sticky_identity()** (3 connections) — `src/ansible_aom/core/tree.py`
- **._worst_status_of()** (3 connections) — `src/ansible_aom/core/tree.py`
- **.is_host_summary_visible()** (2 connections) — `src/ansible_aom/core/tree.py`
- **._task_definition_identity()** (2 connections) — `src/ansible_aom/core/tree.py`
- **Yield preflight task definitions in display order with effective role path.** (1 connections) — `src/ansible_aom/core/models.py`

## Relationships

- [[Play Definition Tree Population]] (39 shared connections)
- [[Play Tree Projection]] (24 shared connections)
- [[Task Definition Live Refresh]] (12 shared connections)
- [[Run State Completion Recap]] (8 shared connections)
- [[Role Chain Extraction]] (7 shared connections)
- [[Role Group Task Models]] (5 shared connections)
- [[Tree Truncation Utilities]] (4 shared connections)
- [[Tree Projection Utilities]] (4 shared connections)
- [[Ungrouped Role Tree Tests]] (3 shared connections)
- [[Loop Item Counter]] (2 shared connections)
- [[Host Overview Table]] (1 shared connections)
- [[Tree Block Animation]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/tree.py`

## Audit Trail

- EXTRACTED: 116 (61%)
- INFERRED: 75 (39%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*