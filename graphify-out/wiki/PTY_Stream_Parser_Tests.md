# PTY Stream Parser Tests

> 17 nodes · cohesion 0.17

## Key Concepts

- **._many_tasks_state()** (14 connections) — `tests/unit/test_tree_projection.py`
- **TestRoleLabelsAfterTruncation** (12 connections) — `tests/unit/test_tree_projection.py`
- **TestTreeLinesPruning** (11 connections) — `tests/unit/test_tree_projection.py`
- **.test_role_label_shows_total_when_all_tasks_visible_after_cut()** (4 connections) — `tests/unit/test_tree_projection.py`
- **.test_role_label_shows_total_when_inside_cut()** (4 connections) — `tests/unit/test_tree_projection.py`
- **.test_role_label_shows_total_when_no_truncation()** (4 connections) — `tests/unit/test_tree_projection.py`
- **.test_role_label_singular_plural_format()** (4 connections) — `tests/unit/test_tree_projection.py`
- **.test_collapses_host_leaves_first()** (3 connections) — `tests/unit/test_tree_projection.py`
- **.test_invariant_one_each_active_role_keeps_one_line()** (3 connections) — `tests/unit/test_tree_projection.py`
- **.test_tight_budget_preserves_depth_over_breadth()** (3 connections) — `tests/unit/test_tree_projection.py`
- **.test_within_budget_is_unchanged()** (3 connections) — `tests/unit/test_tree_projection.py`
- **T3: post-truncation role-label pass.      After `_truncate_two_level` runs, ever** (1 connections) — `tests/unit/test_tree_projection.py`
- **Re-declaration of ``TestTreeLinesPruning._many_tasks_state`` —         small inl** (1 connections) — `tests/unit/test_tree_projection.py`
- **Within-budget tree: 1 role with 3 visible tasks (each with 1         host leaf).** (1 connections) — `tests/unit/test_tree_projection.py`
- **Cut inside the role's task list: 1 role + 3 tasks (each with         1 host leaf** (1 connections) — `tests/unit/test_tree_projection.py`
- **Edge case: visible == total. The role label reads ``(N tasks)``         — no ``r** (1 connections) — `tests/unit/test_tree_projection.py`
- **Verify exact format strings across the singular/plural cases:          - ``(1 ta** (1 connections) — `tests/unit/test_tree_projection.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (21 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (2 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (2 shared connections)

## Source Files

- `tests/unit/test_tree_projection.py`

## Audit Trail

- EXTRACTED: 60 (85%)
- INFERRED: 11 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*