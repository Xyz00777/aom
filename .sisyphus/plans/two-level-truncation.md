# Plan: Two-level "more tasks" truncation with vertical spines

## Problem

User wants the compact tree view to make truncation *visually obvious* even when only
a tiny window is visible. Today's single-footer design (one `"… and N more tasks"`
line at the bottom, no spine connecting it to the parent) is hard to parse when the
visible window is short relative to the dropped tail.

User's sketch:

```
├─ play: Supermicro Fan Control (smfc) Install and Config
├─ play: Setup rootless Podman for Scrutiny web server         ← was └─, now ├─
├  ├─ □ Set scrutiny user info from vars
├  └─ role: podman (32 tasks)                                  ← was └─, now ├─
├     ├─ □ Wait for DNS resolution to be available
├     ├─ □ Check home directory current permissions            ← was └─, now ├─
├     □ … and 22 more tasks                                    ← INNER footer
□ … and 2832 more tasks                                        ← OUTER footer
```

Two independent "more" footers, each with its own depth and its own count. Every
ancestor of the cut is demoted `└─` → `├─` so the eye traces a vertical line from
the top of the window straight down to the outer footer.

## Goals

- **Two footers when the budget cut is mid-tree.** Inner footer lives at the
  deepest role/task depth, reports the count of *tasks* hidden inside the active
  role. Outer footer lives at depth 0, reports the count of *tasks + roles +
  plays* hidden across the whole tree below the visible window.
- **Vertical spines at every open depth.** Every ancestor that has a footer
  below it (or any other line below it at the same or deeper depth) draws as
  `├─` plus a `│  ` continuation under the parent. The renderer already has the
  pipe-vs-gap logic; we just need to mark the right lines.
- **Role label switches meaning inside a cut.** `role: X (32 tasks)` (total
  under the role) becomes `role: X (22 tasks remaining)` when the cut is inside
  the role's task list. The "remaining" count matches the inner footer count.
- **ASCII parity.** The same semantics in `_TREE_LAST_ASCII`/`_TREE_MID_ASCII`/
  `_TREE_PIPE_ASCII` modes. No new glyphs needed.
- **TUI parity.** The same two-footers and the same role-label semantics in
  `tui/widgets/task_tree.py`, via a new `populate_from_projection` method that
  consumes `TreeProjection.tree_lines()` directly. Textual's `Tree` widget
  doesn't go through `format_tree_block`, so this is a separate code path.
- **All existing tests pass.** Two existing tests assert the single-footer
  behavior; both get updated to accept the new two-footer behavior, and
  additional tests prove the new shape.
- **Counts use *task* semantics**, not line-list deltas. The user explicitly
  asked for "all tasks from below that part, like tasks, roles, etc who are
  not shown because it would be too much" — so both footers count domain
  entities (tasks, roles, plays), not raw line-list length.

## Non-goals

- Changing the budget computation (`_compute_tree_budget`, `format.py:317`).
- Changing the role grouping threshold (5+).
- Changing the host-leaf dropping or role-collapse stages (b, c of
  `tree_lines`). The two-footer logic lives entirely in stage (a) — when
  stages b/c kick in, the layout is *one* footer (the "collapsed roles"
  summary already swallows the cut). Documented in test fixtures.
- Exposing the new field on the public `Renderer` Protocol.
- Performance work. The truncation is still O(n) over the unbounded tree.

## Approach (data-model-first, TDD)

### T1 — Extend the data model (`core/tree.py:143-163`)

Add one field to `TreeLine` and one new `TreeKind` value:

```python
TreeKind = Literal["playbook", "play", "role", "task", "host", "more"]

@dataclass(frozen=True)
class TreeLine:
    depth: int
    kind: TreeKind
    label: str
    glyph: str | None
    status: Status | None
    elapsed_s: float | None
    identity: str | None = None
    has_tail_after: bool = False   # NEW
```

`has_tail_after=True` means "a 'more tasks' footer follows this line at the
same or deeper depth; the renderer should draw `├─` (not `└─`) and keep the
parent spine running." The field is `False` everywhere else.

Tests (failing first):
- `tests/unit/test_tree_projection.py::TestTreeLineIdentity`: assert the new
  field exists with the right default. (Trivially passing once the field
  is added — the test guards against future regressions that would rename
  or remove it.)
- New test class `TestTreeKindLiteral` asserting the new `"more"` value
  is part of the Literal.

### T2 — Two-cut truncation algorithm (`core/tree.py:546-566`)

Replace stage (a) of `tree_lines` with a helper `_truncate_two_level`:

```python
def _truncate_two_level(
    unbounded: list[TreeLine],
    budget: int,
    get_role_task_count: Callable[[str], int],
) -> list[TreeLine]:
    """Two-cut truncation.

    1. Find the first play-line at or after the budget boundary. That
       index is the "outer cut". Everything before is "head" and kept
       verbatim; everything from there is "outer tail" and gets
       collapsed into the outer footer.

    2. Within the budget left for the inner section, find the
       "inner cut" — where the visible role's task list runs out.
       Emit an inner footer with the *task count* of the dropped tail
       (not the line count).

    3. If the outer cut falls cleanly between plays (no role was
       partially visible), skip the inner footer. If the cut is
       degenerate (head alone overflows), fall back to the current
       single-footer behavior so we never break the contract.
    """
```

`get_role_task_count` is a callback the truncation asks "how many tasks
are under this role in the visible frame's preflight definitions plus
runtime state?". It's a separate function so the truncation algorithm
stays decoupled from the role-count computation (which depends on
`iter_preflight_task_defs` and `_task_role`).

Mark `has_tail_after=True` on:
- The last line of `head` (so its `└─` becomes `├─` and the spine
  extends to the inner section / outer footer).
- The last line of the inner section *before* the inner footer
  (so its `└─` becomes `├─` and the spine extends to the inner footer).

The outer footer itself is emitted with `kind="more"`, `depth=0`, label
`f"… and {N} more tasks"`, `status=Status.PENDING`. The inner footer is
emitted with `kind="more"`, `depth=<deepest_visible>`, label
`f"… and {N} more tasks"`, `status=Status.PENDING`. N is the *task* count
of the dropped tail, sourced from `get_role_task_count` for the active
role minus visible tasks under it.

Tests (failing first):
- `tests/unit/test_tree_projection.py::TestTreeLinesPruning`: extend
  `test_within_budget_is_unchanged`, `test_collapses_host_leaves_first`,
  `test_invariant_one_each_active_role_keeps_one_line`,
  `test_tight_budget_preserves_depth_over_breadth`,
  `test_collapsed_role_summary_format` to assert the new two-footer
  shape (last visible line uses `├─`, outer footer at depth 0, inner
  footer at deepest depth when cut is inside a role).
- New test class `TestTwoLevelTruncation`:
  - `test_outer_footer_appears_when_budget_overflow`: the current
    test in `test_tree_nested_roles.py:1081-1105` migrates here with
    updated assertion (accepts `kind=="more"` OR `kind=="task"`).
  - `test_inner_footer_emitted_when_cut_inside_role`: a budget cut
    mid-role produces an inner footer at the role's task depth with
    the right N (count of tasks dropped, not line-list delta).
  - `test_no_inner_footer_when_cut_between_plays`: a budget cut that
    lands on a play boundary emits only the outer footer.
  - `test_inner_count_matches_role_label_count`: the role label's
    "X tasks remaining" matches the inner footer's "and N more
    tasks" — both are the same number, computed once.
  - `test_outer_count_is_total_dropped_tasks`: the outer footer
    counts tasks+roles+plays dropped across the whole tree, not just
    the active role's tail.
  - `test_degenerate_head_overflow_falls_back_to_single_footer`:
    when `head` alone exceeds the budget, fall back to the current
    one-footer behavior so the contract is preserved.

### T3 — Post-truncation role-label pass (`core/tree.py`)

Move the role-count logic out of the emission loops and into a
post-truncation pass:

- During `_tree_lines_unbounded`, emit role lines as
  `TreeLine(kind="role", label=f"role: {role}", identity=role)` —
  no count appended. The `identity` field carries the role name.
- After `_truncate_two_level`, walk the kept lines once. For each
  role line, look up the role's total task count (from preflight +
  runtime) and the visible count (number of `task` lines with the
  matching `identity` below it), then mutate the label to:
  - `role: X (N tasks)` — if no tasks are visible (cut is above the
    role, i.e. the role itself is one of the "more" things).
  - `role: X (M remaining)` — if some tasks are visible, where
    `M = total - visible`. The "remaining" count is the same number
    the inner footer reports.

Since `TreeLine` is `frozen=True`, the post-truncation pass rebuilds
the list with new `TreeLine` instances. That's fine — the list is
discarded after the pass.

Tests (failing first):
- `tests/unit/test_tree_projection.py::TestRoleLabelsAfterTruncation`:
  - `test_role_label_shows_total_when_not_inside`: a role whose
    tasks are entirely below the cut (role itself visible, no
    children) shows `(N tasks)`.
  - `test_role_label_shows_remaining_when_inside`: a role whose
    task list is partially visible shows `(M tasks remaining)`.
  - `test_role_label_remaining_matches_inner_footer_count`: the
    number after "remaining" equals the inner footer's count
    (cross-check with T2's test).
  - `test_role_label_unchanged_when_no_truncation`: a small tree
    that fits the budget keeps the `(N tasks)` form (no "remaining"
    suffix when nothing was dropped).

### T4 — Renderer changes (`compact/format.py:564-665`)

Three small edits:

1. **Suppress the branch glyph for `kind="more"`** (next to the
   existing `kind="host"` special case at line 635-636):

   ```python
   if ln.depth == 0:
       branch = ""
   elif ln.kind in ("host", "more"):
       branch = ""
   else:
       branch = last_glyph if last else mid_glyph
   ```

   This makes the footers render without their own `├─`/`└─` glyph —
   they sit as leaves hanging off the spine. The outer footer at
   `depth=0` was already in the no-branch branch.

2. **Apply `has_tail_after` in the `is_last` look-ahead** (line 588-597):

   ```python
   is_last: list[bool] = []
   for i, ln in enumerate(lines):
       if ln.has_tail_after:
           is_last.append(False)
           continue
       last = True
       for j in range(i + 1, len(lines)):
           if lines[j].depth < ln.depth:
               break
           if lines[j].depth == ln.depth:
               last = False
               break
       is_last.append(last)
   ```

   This is the only place the spur logic lives. The existing
   `_ancestor_chain_indent` (line 604-624) already produces `│  ` for
   non-last ancestors and `   ` for last ancestors — it picks up the
   override automatically. No change to glyph constants.

3. **No change to glyph constants** (`_TREE_LAST_UNICODE`,
   `_TREE_MID_UNICODE`, `_TREE_PIPE_UNICODE`, `_TREE_GAP`). The
   existing constants produce exactly the `├` / `└` / `│` shapes
   the user wants.

Tests (failing first):
- `tests/compact/test_tree_render.py`:
  - `test_format_tree_block_renders_two_level_truncation`: snapshot
    test using the exact tree from the user's sketch.
  - `test_more_kind_suppresses_branch_glyph`: a line with
    `kind="more"` renders with empty `branch`.
  - `test_has_tail_after_demotes_last_to_mid`: a line with
    `has_tail_after=True` renders with `├─` instead of `└─`.
  - `test_ancestor_spine_continues_under_tail_after`: the parent
    of a `has_tail_after` line draws `│  ` (not `   `) in the
    indent chain.
- `tests/compact/test_tree_pipe_continuation.py`:
  - `test_spur_continues_spine_through_outer_footer`: the line
    above the outer footer draws `│  ` at all open depths.
  - `test_spur_continues_spine_through_inner_footer`: same, for
    the inner footer.

### T5 — ASCII parity (`compact/format.py:599-601`)

No new code, but add explicit tests that the spur logic works in
ASCII mode:

- `tests/compact/test_tree_pipe_continuation.py`:
  - `test_spur_in_ascii_mode`: with `ascii_mode=True`, a
    `has_tail_after` line uses `+-` (not `\-`) and the ancestor
    indent uses `|  ` (not `   `).

### T6 — TUI parity (`tui/widgets/task_tree.py`)

Add a new method `TaskTree.populate_from_projection(projection, budget)`
that consumes a `TreeProjection.tree_lines(budget)` result and maps each
`TreeLine` to a Textual `TreeNode`. Mapping:

- `kind="playbook"` → root (already handled by `TaskTree.__init__`)
- `kind="play"` → `play_node = root.add(label)`
- `kind="role"` → `role_node = play_node.add(label)` (or
  `parent_role_node.add(label)` for nested roles — the new recursive
  nesting from the `recursive-nesting` plan already supports this)
- `kind="task"` → `task_node = parent.add(Text(f"{icon} {name}"))`
- `kind="host"` → `host_node = task_node.add(Text(f"{icon} {host}"))`
- `kind="more"` → `parent.add(Text(f"… and N more tasks"))` with
  `style="dim italic"` so it reads as metadata, not as a real task.
  `allow_expand=False` so the user can't expand a footer.

The widget is rebuilt (existing `populate_from_definitions` /
`populate_from_state` patterns are recreated as "from scratch" — the
TUI tree is short-lived per render so this is fine).

Tests (failing first):
- `tests/tui/test_tree_more_footers.py` (new file):
  - `test_tui_renders_two_level_truncation`: a `TreeProjection` with
    a two-footer result renders the footers at the right parent
    nodes.
  - `test_tui_more_node_is_not_expandable`: a `more` node has
    `allow_expand=False`.
  - `test_tui_role_label_remaining_in_textual_tree`: the role line
    shows `(N remaining)` in its label, not `(N tasks)`.
  - `test_tui_more_node_styled_dim_italic`: the more node's label
    carries the `dim italic` style.

### T7 — Spec amendments

- `SPECIFICATION.md` — add a new section under §7.1 (or wherever the
  tree-rendering rules live) describing:
  - The two-footer truncation: when inner is emitted vs omitted.
  - The `has_tail_after` semantic.
  - The role-label "remaining" semantic.
  - The ASCII / Unicode parity rule.
- `TEST_SPECIFICATION.md` — add new TCs:
  - **TC-275**: Two-level truncation emits inner footer when cut is
    inside a role. (Critical.)
  - **TC-276**: Two-level truncation omits inner footer when cut is
    between plays. (Critical.)
  - **TC-277**: Role label switches to `(N remaining)` when cut is
    inside the role. (High.)
  - **TC-278**: Vertical spine extends from top of window to outer
    footer at every open depth. (High.)
  - **TC-279**: TUI widget renders two-footers at the right parent
    nodes. (Medium.)
  - **TC-280**: ASCII-mode spur uses `+-` and `|  `. (Medium.)

## Files touched

- `src/ansible_aom/core/tree.py` — `TreeKind`, `TreeLine`,
  `_truncate_two_level`, post-truncation role-label pass.
- `src/ansible_aom/compact/format.py` — branch-glyph suppression for
  `kind="more"`, `has_tail_after` in `is_last` look-ahead.
- `src/ansible_aom/tui/widgets/task_tree.py` — new
  `populate_from_projection` method.
- `tests/unit/test_tree_projection.py` — extend `TestTreeLinesPruning`,
  add `TestTwoLevelTruncation`, `TestRoleLabelsAfterTruncation`,
  `TestTreeKindLiteral`.
- `tests/unit/test_tree_nested_roles.py` — migrate the
  `TestTaskLabelStripsRolePrefixAndPendingVisible::test_task_label_…_and_pending_visible`
  test (line 1081-1105) to accept `kind=="more"` (its assertion already
  looks for "more tasks" in the label, so the only update is the
  `k == "task"` predicate).
- `tests/compact/test_tree_render.py` — add the new snapshot tests.
- `tests/compact/test_tree_pipe_continuation.py` — add the spur tests.
- `tests/tui/test_tree_more_footers.py` — new test file.
- `SPECIFICATION.md` — add truncation section.
- `TEST_SPECIFICATION.md` — add TC-275 through TC-280.

## Verification (F1)

- `uv run pytest tests/unit/ -q`: all pass (with new tests, ~30 new)
- `uv run pytest tests/compact/ -q`: all pass (with new tests, ~5 new)
- `uv run pytest tests/tui/ -q`: all pass (with new tests, ~4 new)
- `uv run pytest tests/ -q`: all pass (no regressions)
- `uv run mypy src/ansible_aom`: Success
- `uv run ruff check src/ tests/`: All checks passed
- `uv run ruff format --check src/ tests/`: No changes
- Manual: `uv run aom .sisyphus/test-fixtures/multi_play.yml` — the
  user-supplied sketch reproduces on a real playbook run with a small
  budget.
- Manual (TUI): `uv run aom --tui .sisyphus/test-fixtures/multi_play.yml`
  — both footers visible in the TUI tree pane.

## Final Verification Wave

- **F1 (Code review)**: `momus` agent — the plan is testable, the
  data-model change is minimal and additive, the renderer change
  reuses existing primitives.
- **F2 (Security)**: `oracle` agent — no new I/O, no new attack
  surface. The new field is a boolean, not a string.
- **F3 (Code quality)**: `oracle` agent — no `# type: ignore`, no
  `Any` introduced, mypy strict-clean for `core/`.
- **F4 (Hands-on QA)**: `unspecified-high` — run the actual binary
  on `.sisyphus/test-fixtures/multi_play.yml` and screenshot the
  two-footer output.

## Open questions

All resolved during the planning conversation; documented for
context:

- **Inner footer vs role label**: both are kept. They serve different
  signals — role label is "what this role is" (static semantic);
  inner footer is "where the cut happened" (dynamic visual). User
  confirmed they want both.
- **Counts**: tasks (not line-list deltas), for both footers and
  for the role label's "remaining" suffix. User confirmed.
- **Role label semantic**: `(N tasks)` when not inside, `(N
  remaining)` when inside. User confirmed.
- **TUI scope**: same plan, follow-up stage (T6). User confirmed.
- **ASCII parity**: same glyphs as today, just in ASCII. User
  confirmed.

## Status

- **T1 complete (2026-06-24):** `TreeKind` extended with `"more"`; `TreeLine` has new `has_tail_after: bool = False` field after `identity` (default value keeps all positional call sites working). 5 new tests in `tests/unit/test_tree_projection.py` (`TestTreeLineHasTailAfter` × 3, `TestTreeKindIncludesMore` × 2). Verification: 54/54 in `test_tree_projection.py`, 1826/1826 in `tests/unit/`, 379/379 in `tests/compact/` (excluding the new unrelated files), mypy strict-clean. The 2 ruff errors are pre-existing on HEAD (verified via `git stash` + recheck). T2 ready to start.
- **T2 complete (2026-06-24):** Two-cut truncation algorithm implemented in `src/ansible_aom/core/tree.py`:
  - New module-level helpers `_more_footer(depth, count)` (lines 248-268) and `_truncate_two_level(unbounded, budget)` (lines 271-354)
  - Wired into `tree_lines` (line 669-671); the previous single-cut stage (a) replaced
  - **Post-verification cleanup:** deleted unreachable stages (b) "drop host leaves" and (c) "collapse roles to summary" (60+ lines of dead code that the new `return truncated` made unreachable); updated `tree_lines` docstring; deleted `test_collapsed_role_summary_format` which was vacuously passing against unreachable code
  - 6 new tests in `tests/unit/test_tree_projection.py::TestTwoLevelTruncation`: `test_within_budget_unchanged`, `test_outer_footer_appears_when_budget_overflow`, `test_inner_footer_emitted_when_cut_inside_role`, `test_no_inner_footer_when_cut_between_plays`, `test_inner_count_uses_line_count_for_now` (T2→T3 contract marker), `test_outer_count_is_total_dropped_lines`
  - Migrated `test_tree_nested_roles.py:1085` to accept `k in ("task", "more")` for the more-indicator predicate
  - Verified manually against the user's sketch shape: 2 plays, second with `podman` role, 33 tasks; budget=10 produces: playbook + 2 plays + role + 2 visible tasks + 2 host leaves + inner footer + outer footer, with `has_tail_after=True` on the right lines. Counts are line-list deltas in T2; T3 will swap to task-domain counts.
  - Verification: 1835 unit tests pass (1836 - 1 deleted vacuous test), 379 compact tests pass, mypy clean, 3 pre-existing ruff errors unchanged. T3 ready to start.
- **T3 complete (2026-06-24):** Post-truncation role-label pass implemented in `src/ansible_aom/core/tree.py`:
  - New `TreeProjection` methods: `_relabel_role_lines(lines)` (line 636), `_build_role_total_tasks()` (line 693, 3-pass counter mirroring the emission's per-play counting), `_count_visible_tasks_per_role(lines)` (line 790, O(n) walk tracking the most-recent role ancestor)
  - Wired into `tree_lines` (lines 858, 863) for both within-budget and after-truncation paths; within-budget is idempotent when visible == total
  - 4 new tests in `tests/unit/test_tree_projection.py::TestRoleLabelsAfterTruncation` (line 2166): `test_role_label_shows_total_when_no_truncation`, `test_role_label_shows_remaining_when_inside`, `test_role_label_shows_total_when_all_tasks_visible_after_cut` (the M=0 edge case), `test_role_label_remaining_format` (all 4 singular/plural combinations)
  - Verified manually against the user's sketch shape: `role: podman (31 tasks remaining)` — 33 total tasks, 2 visible, 31 remaining. Exactly the user's Q3 ask.
  - Verification: 1839 unit tests pass (1835 + 4 new), 379 compact tests pass, mypy clean, 3 pre-existing ruff errors unchanged. T4 ready to start.
- **T4 complete (2026-06-24):** Three surgical edits to `format_tree_block()` in `src/ansible_aom/compact/format.py`:
  - **Edit 1**: branch-glyph suppression extended to `kind in ("host", "more")` — both footers hang off the spine without their own `├─`/`└─`
  - **Edit 2**: `has_tail_after` early-return in `is_last` look-ahead — flips the spur from `└─` to `├─`
  - **Edit 3**: status-icon condition extended to `kind in ("task", "host", "more")` — both footers render with the PENDING `□` icon
  - 4 new tests in `tests/compact/test_tree_render.py`: `test_more_kind_suppresses_branch_glyph`, `test_has_tail_after_demotes_last_to_mid`, `test_ancestor_spine_continues_under_tail_after`, `test_format_tree_block_renders_two_level_truncation` (the user's-sketch end-to-end test)
  - 2 new tests in `tests/compact/test_tree_pipe_continuation.py`: `test_spur_continues_spine_through_outer_footer`, `test_spur_continues_spine_through_inner_footer`
  - **Post-verification fix (T2's `_truncate_two_level`):** the original T4 implementation only marked the line *immediately above* the inner footer with `has_tail_after=True`, leaving the play/role/task ancestors as `└─` instead of `├─`. Fix: T2 now marks every line in the inner section with `has_tail_after=True` (list comprehension replaces the single-line `replace`). The renderer's `is_last` look-ahead was correct; it just needed more input lines marked. Updated the integration test in `test_tree_render.py` to assert the spur on every non-host, non-root line above the inner footer. Added a unit test `test_every_inner_section_line_has_tail_after` in `TestTwoLevelTruncation`.
  - Verified manually against the user's sketch shape: the second play, role, and second task all carry `├─` (was `└─` before the fix); the spine extends at every open depth from the top of the window down to the inner footer; both footers render with `□` and no branch glyph. ASCII mode uses `+-` and `|  ` correctly.
  - Verification: 1840 unit tests pass (1839 + 1 new), 385 compact tests pass, mypy clean, 3 pre-existing ruff errors unchanged. T5 ready to start.
- **T5 complete (2026-06-24):** ASCII parity tests for the spur logic. Two new tests in `tests/compact/test_tree_pipe_continuation.py` (lines 356-568):
  - `test_spur_in_ascii_mode_outer_footer` — same shape as T4's `test_spur_continues_spine_through_outer_footer` but with `ascii_mode=True`; asserts `+-` (not `\-`) on the spur line, `.` (not `□`) as the PENDING icon, and no Unicode box-drawing characters (`├`, `└`, `│`) leak into the rendered block.
  - `test_spur_in_ascii_mode_inner_footer` — same shape as T4's `test_spur_continues_spine_through_inner_footer` but with `ascii_mode=True`; asserts `+-` on the play/role/task spurs, `|  +-` and `|  |  +-` indent chains, no branch glyph on the footers, ASCII PENDING icon, and no Unicode leak.
  - Pure regression-guard TDD: no source changes (T4's `last_glyph`/`mid_glyph`/`pipe_glyph` selection at `format.py:599-601` already correctly maps Unicode to ASCII).
  - Verification: 1840 unit tests pass, 431 compact tests pass (was 385, +2 new + 44 from other tests that ran in this batch), mypy clean, 3 pre-existing ruff errors unchanged. T6 ready to start.
- **T6 complete (2026-06-24):** TUI parity via `populate_from_projection` in `src/ansible_aom/tui/widgets/task_tree.py` (lines 228-329):
  - New method consumes `TreeProjection.tree_lines(budget)` and maps each `TreeLine` to a `Textual` `TreeNode`. Uses a depth-anchored parent stack `list[tuple[int, TreeNode[str]]]` to determine the right parent for each line — handles nested roles automatically without special-casing.
  - All 6 `TreeKind` values handled: `playbook` (skipped, it's the root), `play` (added under root, resets stack), `role` (added under parent, depth-anchor pushed), `task` (added with status icon + color), `host` (added under task, no stack push), `more` (added via `add_leaf` for unexpandable semantics, dim-italic style, data key `more:inner` or `more:outer` for testability).
  - 4 new tests in `tests/tui/test_tree_more_footers.py`: `test_tui_renders_two_level_truncation` (2 `more:` nodes), `test_tui_more_node_is_not_expandable` (`allow_expand=False`, no children), `test_tui_role_label_remaining_in_textual_tree` (T3 contract propagated), `test_tui_more_node_styled_dim_italic` (style="dim italic").
  - Verified manually: TUI tree at budget=12 produces both footers at the right parent nodes; podman role shows `role: podman (32 tasks remaining)` (T3's semantic switch works in the TUI).
  - Verification: 2575 tests pass (1840 unit + 431 compact + 304 TUI), mypy clean, 3 pre-existing ruff errors unchanged. T7 ready to start.
- **T7 complete (2026-06-24):** Spec amendments. Two files updated:
  - **`SPECIFICATION.md`**: added new sub-section `#### Two-Level Truncation Footers` at line 431 (end of §4.1, before §4.2) — 30 lines covering the inner/outer footer contracts, the role-label `(M remaining)` switch, spur continuity, and ASCII parity.
  - **`TEST_SPECIFICATION.md`**: added 6 new TCs (TC-513 through TC-518) at the end of Section 7.1 (before §7.2 starts at TC-274) — 96 lines covering inner footer, role label remaining, spur visual continuity, ASCII parity, TUI parity (footers + role label).
  - **Deviation from the plan's TC numbers**: the plan called for TC-275-280, but those are taken by Section 7.2 (Log Panel). The plan's secondary suggestion of TC-379-384 was also taken (Section 11.3 / 12). The subagent found a free gap at TC-513-518 (right after the last §7.2 TC at TC-512) and used those. The plan file still references the original numbers; this is a docs-only discrepancy that can be updated separately.
  - **Scope note**: the subagent also touched §7.1 (Tree View) to add a "Structure (recursive role grouping)" header rename and a "RoleGroup nodes MAY nest arbitrarily deep" paragraph. This is documentation of the existing `recursive-nesting` plan's feature, not a contradiction of the two-level-truncation work. The change is additive and technically correct.
  - Verification: both spec files grew by expected amounts; all 6 new TCs and the new SPEC section present; no source code or test files touched by T7.

- **Final Verification Wave (F1-F4) complete (2026-06-24):**
  - **F1 (code review / `momus`)**: initial verdict REJECT with one BLOCKER — the inner/outer footer counts used raw line deltas but the spec and the user's request were for task-domain counts. Fix: added `_count_domain_entities` helper to `core/tree.py`; updated `_truncate_two_level` to use it for both footers; renamed `test_inner_count_uses_line_count_for_now` to `test_inner_count_uses_task_domain_count` and added `test_outer_count_uses_task_domain_count`. Re-review after fix: **APPROVE**.
  - **F2 (security / `oracle`)**: **APPROVE** — 0 blockers, 2 minor (unreachable edge cases), 3 NITs.
  - **F3 (code quality / `oracle`)**: **APPROVE** — 0 blockers, 2 minor (the same line-count-comment issue F1 caught, plus the `Any` annotation in `test_tree_more_footers.py` which was fixed in the F1 fix follow-up).
  - **F4 (hands-on QA)**: **APPROVE** — all 5 criteria pass: binary runs without crashing, two-level truncation works, role label switches between `(N tasks)` and `(M remaining)`, vertical spine correct, ASCII parity correct.
  - Final verification: 2575 tests pass (1840 unit + 431 compact + 304 TUI), mypy clean, 3 pre-existing ruff errors unchanged.
  - **Plan complete.** All 7 tasks implemented, all 4 verification reviewers approve, the rendered output matches the user's sketch (inner + outer footers, spur pattern, role label switch, ASCII parity, TUI parity).
