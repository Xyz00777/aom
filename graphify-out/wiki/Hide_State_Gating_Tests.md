# Hide State Gating Tests

> 84 nodes · cohesion 0.05

## Key Concepts

- **TreeProjection** (55 connections) — `src/ansible_aom/core/tree_projection.py`
- **TreeLine** (37 connections) — `src/ansible_aom/core/tree_projection.py`
- **._emit_runtime_play()** (23 connections) — `src/ansible_aom/core/tree_projection.py`
- **tree_projection.py** (18 connections) — `src/ansible_aom/core/tree_projection.py`
- **datetime** (14 connections)
- **._tree_lines_unbounded()** (14 connections) — `src/ansible_aom/core/tree_projection.py`
- **strip_role_prefix()** (12 connections) — `src/ansible_aom/core/models.py`
- **._build_role_total_tasks()** (11 connections) — `src/ansible_aom/core/tree_projection.py`
- **._emit_pending_play()** (11 connections) — `src/ansible_aom/core/tree_projection.py`
- **._touch_row_lease()** (10 connections) — `src/ansible_aom/core/tree_projection.py`
- **.tree_lines()** (10 connections) — `src/ansible_aom/core/tree_projection.py`
- **iter_preflight_task_defs()** (9 connections) — `src/ansible_aom/core/models.py`
- **._recompute_inner_footer_count()** (9 connections) — `src/ansible_aom/core/tree_projection.py`
- **._touch_task_lease()** (9 connections) — `src/ansible_aom/core/tree_projection.py`
- **.host_rows()** (8 connections) — `src/ansible_aom/core/tree_projection.py`
- **._play_running_and_pending()** (8 connections) — `src/ansible_aom/core/tree_projection.py`
- **_is_template_match()** (7 connections) — `src/ansible_aom/core/tree_projection.py`
- **._play_runtime_identity()** (7 connections) — `src/ansible_aom/core/tree_projection.py`
- **._relabel_role_lines()** (7 connections) — `src/ansible_aom/core/tree_projection.py`
- **._task_role()** (7 connections) — `src/ansible_aom/core/tree_projection.py`
- **runtime_role_from_task_name()** (6 connections) — `src/ansible_aom/core/models.py`
- **_effective_status()** (6 connections) — `src/ansible_aom/core/tree_projection.py`
- **._task_line()** (6 connections) — `src/ansible_aom/core/tree_projection.py`
- **._task_runtime_identity()** (6 connections) — `src/ansible_aom/core/tree_projection.py`
- **._touch_play_leases()** (6 connections) — `src/ansible_aom/core/tree_projection.py`
- *... and 59 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (22 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (7 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (7 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (6 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (5 shared connections)
- [Rerun Host Set Composition](Rerun_Host_Set_Composition.md) (5 shared connections)
- [Four-Layer Redaction System](Four-Layer_Redaction_System.md) (4 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (3 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (3 shared connections)
- [Integration Test Suite](Integration_Test_Suite.md) (3 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)
- [Ungrouped Role Tree Tests](Ungrouped_Role_Tree_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/tree_projection.py`
- `tests/unit/test_tree_projection.py`

## Audit Trail

- EXTRACTED: 387 (86%)
- INFERRED: 65 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*