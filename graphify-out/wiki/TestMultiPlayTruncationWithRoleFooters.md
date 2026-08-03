# TestMultiPlayTruncationWithRoleFooters

> 12 nodes · cohesion 0.27

## Key Concepts

- **TestMultiPlayTruncationWithRoleFooters** (14 connections) — `tests/unit/test_tree_projection.py`
- **._multi_play_completed_state()** (9 connections) — `tests/unit/test_tree_projection.py`
- **.test_inner_footer_for_role_in_head_when_cut_lands_in_later_play()** (6 connections) — `tests/unit/test_tree_projection.py`
- **.test_inner_footers_for_nested_roles_in_head()** (5 connections) — `tests/unit/test_tree_projection.py`
- **.test_outer_footer_count_is_total_remaining_across_all_plays()** (5 connections) — `tests/unit/test_tree_projection.py`
- **._extract_more_count()** (4 connections) — `tests/unit/test_tree_projection.py`
- **._find_more_at()** (4 connections) — `tests/unit/test_tree_projection.py`
- **Multi-play truncation with completed tasks in earlier plays.      Reproduces the** (1 connections) — `tests/unit/test_tree_projection.py`
- **Build the user's exact reproduction state.          Play 1 = ``podman`` (289 dir** (1 connections) — `tests/unit/test_tree_projection.py`
- **Bug 1: the angie role (in the head, before the outer cut) has         127 remain** (1 connections) — `tests/unit/test_tree_projection.py`
- **Bug 2: with nested roles (podman > angie) both roles in the         head have re** (1 connections) — `tests/unit/test_tree_projection.py`
- **Bug 3: the outer footer must report the TOTAL remaining tasks         across ALL** (1 connections) — `tests/unit/test_tree_projection.py`

## Relationships

- [TaskDefinition](TaskDefinition.md) (5 shared connections)
- [.from_run_state](from_run_state.md) (4 shared connections)
- [HostRunState](HostRunState.md) (2 shared connections)
- [PlayDefinition](PlayDefinition.md) (2 shared connections)
- [TreeProjection](TreeProjection.md) (2 shared connections)
- [RunState](RunState.md) (1 shared connections)

## Source Files

- `tests/unit/test_tree_projection.py`

## Audit Trail

- EXTRACTED: 47 (90%)
- INFERRED: 5 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*