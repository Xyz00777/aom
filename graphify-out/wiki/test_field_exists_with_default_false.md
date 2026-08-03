# .test_field_exists_with_default_false

> 23 nodes · cohesion 0.12

## Key Concepts

- **TreeLine** (38 connections) — `src/ansible_aom/core/tree_projection.py`
- **TestMultiPlayTruncationWithRoleFooters** (14 connections) — `tests/unit/test_tree_projection.py`
- **._multi_play_completed_state()** (9 connections) — `tests/unit/test_tree_projection.py`
- **.test_inner_footer_for_role_in_head_when_cut_lands_in_later_play()** (6 connections) — `tests/unit/test_tree_projection.py`
- **.test_inner_footers_for_nested_roles_in_head()** (5 connections) — `tests/unit/test_tree_projection.py`
- **.test_outer_footer_count_is_total_remaining_across_all_plays()** (5 connections) — `tests/unit/test_tree_projection.py`
- **._extract_more_count()** (4 connections) — `tests/unit/test_tree_projection.py`
- **._find_more_at()** (4 connections) — `tests/unit/test_tree_projection.py`
- **.test_tree_line_accepts_more_kind()** (3 connections) — `tests/unit/test_tree_projection.py`
- **.test_can_construct_with_has_tail_after_true()** (3 connections) — `tests/unit/test_tree_projection.py`
- **.test_default_is_false_for_keyword_construction()** (3 connections) — `tests/unit/test_tree_projection.py`
- **.test_field_exists_with_default_false()** (3 connections) — `tests/unit/test_tree_projection.py`
- **.test_tree_line_is_frozen()** (2 connections) — `tests/unit/test_tree_projection.py`
- **One rendered line in the tree.      The renderer turns this into "{indent}{branc** (1 connections) — `src/ansible_aom/core/tree_projection.py`
- **A TreeLine constructed positionally (no kwarg) has         ``has_tail_after=Fals** (1 connections) — `tests/unit/test_tree_projection.py`
- **Constructing a TreeLine with ``has_tail_after=True`` works and         the value** (1 connections) — `tests/unit/test_tree_projection.py`
- **Kwarg-only construction also defaults to ``False`` — covers         the case whe** (1 connections) — `tests/unit/test_tree_projection.py`
- **Constructing a TreeLine with ``kind='more'`` is statically valid         — guard** (1 connections) — `tests/unit/test_tree_projection.py`
- **Multi-play truncation with completed tasks in earlier plays.      Reproduces the** (1 connections) — `tests/unit/test_tree_projection.py`
- **Build the user's exact reproduction state.          Play 1 = ``podman`` (289 dir** (1 connections) — `tests/unit/test_tree_projection.py`
- **Bug 1: the angie role (in the head, before the outer cut) has         127 remain** (1 connections) — `tests/unit/test_tree_projection.py`
- **Bug 2: with nested roles (podman > angie) both roles in the         head have re** (1 connections) — `tests/unit/test_tree_projection.py`
- **Bug 3: the outer footer must report the TOTAL remaining tasks         across ALL** (1 connections) — `tests/unit/test_tree_projection.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (21 shared connections)
- [Hide State Gating Tests](Hide_State_Gating_Tests.md) (10 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (4 shared connections)
- [tree.py](tree.py.md) (4 shared connections)
- [Rerun Host Set Composition](Rerun_Host_Set_Composition.md) (4 shared connections)
- [Four-Layer Redaction System](Four-Layer_Redaction_System.md) (3 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (2 shared connections)
- [List-Tasks Failure Handling](List-Tasks_Failure_Handling.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/tree_projection.py`
- `tests/unit/test_tree_projection.py`

## Audit Trail

- EXTRACTED: 88 (81%)
- INFERRED: 21 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*