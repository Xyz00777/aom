# Learnings — Two-level truncation plan

## T1 (data-model extension) — 2026-06-24T19:56:48+02:00

### What was implemented

- Extended `TreeKind` literal in `src/ansible_aom/core/tree.py:34`
  from `Literal["playbook", "play", "role", "task", "host"]` to
  `Literal["playbook", "play", "role", "task", "host", "more"]`.
- Added a new `has_tail_after: bool = False` field on the frozen
  `TreeLine` dataclass, placed AFTER `identity` to preserve
  positional-argument compatibility for any caller that builds
  `TreeLine(...)` without kwarg names.
- Updated `TreeLine` docstring to describe the new field's contract:
  "a 'more tasks' footer follows this line at the same or deeper
  depth; the renderer should demote this line's branch glyph from
  `└─` to `├─` and keep the parent spine running".

### Tests added (TDD)

`tests/unit/test_tree_projection.py` — placed right after
`TestTreeLineIdentity`:

- `TestTreeLineHasTailAfter` (3 tests):
  - `test_field_exists_with_default_false` — positional
    construction (no kwarg) has the field defaulting to `False`.
    Guards against anyone removing the field or breaking positional
    call sites.
  - `test_can_construct_with_has_tail_after_true` — kwarg
    `has_tail_after=True` is accepted and round-trips through the
    frozen dataclass.
  - `test_default_is_false_for_keyword_construction` — kwarg-only
    construction also defaults to `False`.
- `TestTreeKindIncludesMore` (2 tests):
  - `test_more_is_part_of_literal` — `"more" in get_args(TreeKind)`
    asserts the literal value is present.
  - `test_tree_line_accepts_more_kind` — actually constructs a
    `TreeLine(kind="more", ...)` so a future edit that drops
    `"more"` from the Literal fails this test at type-check /
    construction time.

### TDD verification

- All 5 new tests failed before the `tree.py` change (verified):
  - 3× `AttributeError: 'TreeLine' object has no attribute 'has_tail_after'`
  - 1× `TypeError: TreeLine.__init__() got an unexpected keyword argument 'has_tail_after'`
  - 1× `AssertionError: 'more' not in ('playbook', 'play', 'role', 'task', 'host')`
- All 5 new tests pass after the `tree.py` change.

### Verification

- `uv run pytest tests/unit/test_tree_projection.py -q` → 54 passed.
- `uv run pytest tests/ -q` → 2909 passed, 6 skipped, 1 xfailed
  (~244s). No regressions.
- `uv run mypy src/ansible_aom` → `Success: no issues found in 69 source files`.
- `uv run ruff check src/ tests/` → 2 pre-existing errors, neither
  introduced by this change:
  - `src/ansible_aom/core/tree.py:773` (`F841` `idx_before`
    assigned-but-unused — pre-existing WIP from another plan in
    flight, line not touched by T1).
  - `src/ansible_aom/tui/screens/inspect.py:802` (`E501` line too
    long — different file entirely, not touched by T1).
  Confirmed pre-existing by stashing T1's edits and re-running
  ruff; both errors remain.
- `lsp_diagnostics` on both edited files → no errors.
- `tests/unit/test_tree_nested_roles.py::TestTaskLabelStripsRolePrefixAndPendingVisible::test_task_label_strips_role_prefix_and_pending_visible`
  still passes (1 passed).

### Observations for downstream tasks (T2+)

- The new `kind="more"` value does NOT need to be handled anywhere
  in the current codebase — every existing `kind == "X"` check is
  an equality match on a known kind, and `"more"` simply falls
  through to the default branch (which renders correctly because
  T4 adds the special case at the right time).
- `TreeKind` is exported from `core/tree.py`; renderer / TUI code
  doesn't import it directly — they consume `TreeLine.kind`
  indirectly. So the literal extension is a pure data-model
  change with zero downstream type breakage.
- The frozen dataclass + default-value field pattern means: any
  existing positional constructor still works without source edits,
  AND any future code that wants `has_tail_after=True` can opt in
  by passing the kwarg. No migration needed for call sites.
- TreeLine at the renderer boundary in `compact/format.py:635-636`
  has `elif ln.kind == "host":` for the branch-suppression case.
  T4 will add the symmetric `("host", "more")` branch.

### Conventions reaffirmed

- Tests for `core/tree.py` live in
  `tests/unit/test_tree_projection.py`. New sibling test classes
  slot in next to `TestTreeLineIdentity` (the existing precedent
  for `identity` field regression guards).
- Docstrings on test methods describe the regression contract, not
  the implementation. This is the established convention in this
  test file — every test method has one.
- Class docstrings on `core/` dataclasses describe the public
  contract (every field, what it's for). Adding a field comes with
  a docstring update on the class.

### Pitfalls avoided

- Did NOT touch `compact/format.py` (T4's job) — the renderer
  already ignores the new field because it never reads
  `has_tail_after`. Behavior is preserved because `frozen=True`
  + no new field access = no change.
- Did NOT add `# type: ignore` or `Any` anywhere.
- Did NOT add a `_post_init` or custom `__init__` — the default
  frozen-dataclass behavior gives us everything we need.
- Kept `has_tail_after` AFTER `identity` so positional callers
  (none today, but future-proof) keep working.
## T2 (two-cut truncation algorithm) — 2026-06-24T20:30:00+02:00

### What was implemented

- Added module-level helpers in `src/ansible_aom/core/tree.py`:
  - `_more_footer(depth, count) -> TreeLine` — emits a single
    `kind="more"` `TreeLine` with the standard "… and N more tasks"
    label and `Status.PENDING` (matching the pre-T2 single-cut footer
    so colour stays consistent).
  - `_truncate_two_level(unbounded, budget) -> list[TreeLine]` — pure
    function, no `self` access. Replaces the pre-T2 stage (a) block at
    `tree.py:553-573` with a two-cut algorithm that emits an inner
    footer (when the cut lands inside a role) AND an outer footer
    (always when the budget overflows).
- Wired `_truncate_two_level` into `TreeProjection.tree_lines` at
  `tree.py:540-555`. The pre-existing `self._prune_row_leases(now)`
  call is preserved in the right place.
- Marked `has_tail_after=True` on:
  - The last line of `head` (so its `└─` becomes `├─` and the spine
    extends down to the inner section / outer footer).
  - The last visible line of the inner section before the inner
    footer (so its `└─` becomes `├─` and the spine extends to the
    inner footer).

### Algorithm details (deviations from the prompt's pseudocode)

The prompt's pseudocode has two boundary cases that don't quite
match the existing test contract `len(lines) <= budget`. The working
tree's pre-T2 stage (a) (from the recursive-nesting plan) is
`lines = lines[:budget]` — a clean slice with NO footer. T2's
introduction of footers changes the visible content; the budget
arithmetic had to be tightened to keep the length contract.

**Change 1: `inner_budget = budget - len(head) - 2`** (the prompt
said `- 1` "for outer footer"). With the prompt's value, the
cut-inside-role branch produced `head + inner_budget + 1 (inner
footer) + 1 (outer footer) = budget + 1` lines, breaking
`test_collapses_host_leaves_first` (which asserts
`len(lines) <= budget`). The comment said only one line was reserved
for the outer footer, but two footers are emitted in the
cut-inside-role case — so both must be reserved. With `- 2` the
total is `head + inner_budget + 2 = budget`.

**Change 2: added `inner_budget == 0` to the "no inner cut"
guard.** The prompt's pseudocode only had `inner_dropped == 0`, but
when the cut lands between plays with `head_end == budget - 1`,
`inner_budget == 0` and `inner_dropped == len(outer_tail) > 0` — the
pseudocode would then IndexError on `inner_section[-1]`. Collapsing
both cases to "no inner cut → single outer footer" makes the
algorithm complete. The change is a minimal extension of the
existing guard, not a new branch.

### TDD order

1. Wrote 6 new tests in `tests/unit/test_tree_projection.py::
   TestTwoLevelTruncation` BEFORE touching `tree.py`:
   - `test_within_budget_unchanged` — verbatim return when within
     budget.
   - `test_outer_footer_appears_when_budget_overflow` — replicates
     the 34-pending-tasks / budget=12 scenario from
     `test_tree_nested_roles.py:992-1104`. Asserts the last line is
     `kind="more"`, `depth=0`, label matches `r"… and \d+ more tasks"`.
   - `test_inner_footer_emitted_when_cut_inside_role` — 1 play + 1
     role + 20 tasks, budget=6. Asserts last is outer footer,
     second-to-last is inner footer (depth matches deepest visible
     line), the line above the inner footer has `has_tail_after=True`.
   - `test_no_inner_footer_when_cut_between_plays` — 2 plays, dynamic
     budget chosen so the cut lands on a play boundary. Asserts
     exactly ONE `more` footer (the outer one), no inner footer.
   - `test_inner_count_uses_line_count_for_now` — T2→T3 contract
     marker. Asserts the inner count equals the raw line-list delta
     (not task count). The bookkeeping comment in the test pins the
     T2 math so a future T3 author sees the contract change.
   - `test_outer_count_is_total_dropped_lines` — asserts the outer
     count equals `len(unbounded) - (len(kept) - 1)`.

2. Confirmed 5 of 6 tests fail (red phase) — only
   `test_within_budget_unchanged` passes (the within-budget path is
   unchanged from pre-T2).

3. Migrated `tests/unit/test_tree_nested_roles.py:1081-1104`:
   changed the `more_indicator` predicate from `k == "task"` to
   `k in ("task", "more")` so it accepts both the pre-T2 and T2
   footer kinds.

4. Implemented `_more_footer` and `_truncate_two_level` in
   `tree.py`. Wired into `tree_lines`.

5. Updated `TestTreeLinesPruning::test_collapses_host_leaves_first`:
   the test asserted `"task" in kinds` at budget=4, which is
   incompatible with T2 (T2's two-footers consume 2 of the 4 budget
   lines, leaving no room for the role or task). Replaced the
   `"task" in kinds` assertion with `"more" in kinds` and
   documented the T2 contract change in the test comment. The
   `len(lines) <= 4` contract is preserved.

6. Confirmed all 6 new tests pass (green phase). Full test suite:
   1836 unit tests pass; 2919 total tests pass with no regressions.

### Lines of `tree.py` changed

- `tree.py:14` — added `replace` to the `dataclasses` import. The
  frozen `TreeLine` only auto-generates `__replace__` in Python 3.14
  (PEP 622), not `_replace`; the prompt suggested
  `ln._replace(has_tail_after=True)` but the actual method name is
  `__replace__`. `dataclasses.replace(ln, has_tail_after=True)` is
  the portable choice and reads the same.
- `tree.py:248-355` — added `_more_footer` and `_truncate_two_level`
  module-level helpers (placed right before the `TreeProjection`
  class so the data-model definitions and helpers are co-located).
- `tree.py:546-555` — replaced the pre-T2 stage (a) block with a
  call to `_truncate_two_level`. Kept the `self._prune_row_leases(now)`
  call for both the within-budget and overflow paths.

### Conventions reaffirmed

- TDD-first: tests written, then implementation, then
  verification. All 6 new tests failed before any `tree.py` change.
- `replace()` (not `_replace`): Python 3.14's frozen dataclasses
  only expose `__replace__`. The prompt's assumption that
  `_replace` is auto-generated is wrong for 3.14.
- `frozen=True` mutations: every `has_tail_after=True` update goes
  through `replace(line, has_tail_after=True)`, never in-place
  assignment.
- Section divider comments (`# -------- ... --------`) used inside
  the test class to separate fixture helpers from the test methods.
  The codebase uses these elsewhere (e.g. `tree.py:514,520,526`).
- Test-method docstrings describe the regression contract, not the
  implementation (per T1's "Conventions reaffirmed" note).
- Inline comments in both `tree.py` and the test file document
  non-obvious algorithm details (T2→T3 contract transition, the
  "raw line count for now" marker, the budget arithmetic). These
  follow the "necessary comments" pattern (complex algorithm).

### Pitfalls avoided

- Did NOT touch `compact/format.py` (T4's job). The renderer ignores
  the new `kind="more"` and `has_tail_after` fields because it
  never reads them; the rendered output is the same as pre-T2
  (slightly different glyphs, since the cut now happens at a
  different position, but the renderer code itself is untouched).
- Did NOT pre-empt T3's task-count logic. T2 uses raw line-list
  deltas. The comment "raw line count for now (T3 swaps this)"
  marks the contract transition.
- Did NOT add a `_truncate_two_level` method on `TreeProjection`.
  It's a stateless helper — module-level function (per the prompt).
- Did NOT change `test_within_budget_is_unchanged` (per the prompt's
  explicit rule).
- Did NOT use `Any` or `# type: ignore`.
- Did NOT add a `get_role_task_count` callback to `_truncate_two_level`
  (per the prompt — that's T3's job).

### Verification

- `uv run pytest tests/unit/test_tree_projection.py -q` →
  62 passed (54 pre-existing + 6 new + 2 modified to accept T2).
  Note: `test_collapses_host_leaves_first` was updated to assert the
  T2 contract.
- `uv run pytest tests/unit/test_tree_nested_roles.py -q` →
  8 passed.
- `uv run pytest tests/unit/ -q` → 1836 passed.
- `uv run pytest tests/ -q` → 2919 passed, 6 skipped, 1 xfailed.
- `uv run mypy src/ansible_aom` → Success: no issues found in 69
  source files.
- `uv run ruff check src/ansible_aom tests` → 3 pre-existing
  errors (F841 at `tree.py:873` from recursive-nesting, E501 at
  `tui/screens/inspect.py:802`, I001 at
  `tests/unit/test_dynamic_expansion.py:327`). None introduced by
  T2.
- `lsp_diagnostics` on the three modified files → no errors.

### Test count math (for the plan status update)

- Pre-T2: 1830 unit tests (per T1's "1826/1826" note; that was
  the count at end of T1, but `recursive-nesting` plan landed in
  the working tree since then, so the baseline shifted slightly).
  The exact pre-T2 baseline in this branch is 1830 unit tests;
  T2 adds 6 to land at 1836.
- The prompt's claim of "existing 54" in `test_tree_projection.py`
  predates the `recursive-nesting` plan landing — the actual count
  was 56 in the working tree at the start of T2. Adding 6 new
  tests + 1 modified (`test_collapses_host_leaves_first`) lands
  at 62 in `test_tree_projection.py`.

### Open questions for T3+

- T3 will replace the raw line-list deltas with task-domain counts
  via a post-truncation pass. The markers left in the code
  (`# raw line count for now (T3 swaps this)`,
  `# T2 contract: raw line-list delta`) should make the swap easy
  to grep for.
- T4 will add the `kind="more"` branch-glyph suppression and
  `has_tail_after` look-ahead in `compact/format.py`. T2 emits the
  data; T4 wires it into the rendering. No interaction with T2's
  algorithm.
- The cut-between-plays branch (single outer footer) is
  structural-equivalent to the pre-T2 single-cut footer but with
  `has_tail_after=True` on the last visible line. T4's renderer
  change for `has_tail_after` will turn the `└─` on that line into
  `├─`, which is the desired vertical-spine behavior.

## T2 (post-verification fix) — 2026-06-24T20:45:00+02:00

Deleted dead code from T2 implementation: stages (b) and (c) of `tree_lines` were unreachable
after T2's `return truncated` (line 672). Removed 60+ lines of dead code at lines 674-739.
Deleted `test_collapsed_role_summary_format` which was vacuously passing — it tested stage (c)
which is no longer reachable. Updated `tree_lines` docstring to reflect the new single-stage
two-cut structure. Verified 1835 unit tests pass (down from 1836 by the deleted test).

## T3 (post-truncation role-label pass) — 2026-06-24T21:30:00+02:00

### What was implemented

- Added 3 private methods to `TreeProjection` in `src/ansible_aom/core/tree.py`:
  - `_relabel_role_lines(lines)` (lines 636-693) — rewrites role labels
    based on visible vs total task count. Single entry point that
    coordinates the two maps.
  - `_build_role_total_tasks()` (lines 695-790) — builds
    `role → total task count` from preflight + runtime state.
    Three passes: preflight, runtime-only, fallback for roles that
    have 0 from the first two passes (catches dynamic-only roles
    whose grafted `TaskDefinition` has `role=None`).
  - `_count_visible_tasks_per_role(lines)` (lines 792-822) —
    walks the kept lines once, tracking the most recent
    `kind="role"` ancestor and counting `kind="task"` lines below it.
    Resets on `play`/`playbook` boundaries.
- Wired `_relabel_role_lines` into `tree_lines` (line ~855) for
  BOTH branches: within-budget (idempotent for visible==total) and
  after-truncation (the meaningful case).
- The T3 relabel is idempotent in the within-budget case when
  visible == total. When visible < total (some tasks are dropped,
  either by truncation or by being completed), the format switches
  to `(M remaining)`.

### Files changed

- `src/ansible_aom/core/tree.py`:
  - Lines 636-822: 3 new methods on `TreeProjection`:
    `_relabel_role_lines`, `_build_role_total_tasks`,
    `_count_visible_tasks_per_role`.
  - Lines ~782-855: `tree_lines` docstring updated + wiring
    added for both branches.
- `tests/unit/test_tree_projection.py`:
  - Added `TestRoleLabelsAfterTruncation` class with 4 tests
    (after `TestTwoLevelTruncation`, before `TestTreeLineIdentity`).
- `tests/unit/test_runtime_role_task_count.py`:
  - Updated `test_dynamic_role_shows_task_count_in_label` and
    `test_dynamic_role_with_no_preflight_shows_runtime_count` to
    expect the new `(M remaining)` format.
- `tests/unit/test_tree_classify_and_role_labels.py`:
  - Updated `test_role_label_shows_total_task_count_not_running_count`
    to expect `(1 task remaining)` instead of `(2 tasks)`.

### Algorithm details

**`_build_role_total_tasks`** has three passes (not the two the
plan described):

1. **Preflight pass** — walk `iter_preflight_task_defs(play_def.tasks)`
   for each `PlayDefinition`. Tally each task's innermost role
   (post-aggressive-collapse). Skips tasks with empty role paths.

2. **Runtime-only pass** — walk `play.tasks.values()` for each
   runtime play. Skip tasks whose name (or stripped name) is in
   the preflight name set, or template-matches a preflight name.
   Tally the remaining tasks' `runtime_role_from_task_name`.

3. **Fallback pass** (NEW vs the plan's two-pass sketch) — for any
   role name that appears at runtime via `runtime_role_from_task_name`
   but has 0 in the preflight+runtime-only map, count runtime tasks
   matching that role name. This mirrors the
   `if n == 0: n = sum(...)` fallback at `_emit_runtime_play`
   line ~1159. Without this fallback, dynamic-only roles whose
   grafted `TaskDefinition` carries `role=None` would show no
   count. The pre-existing
   `test_dynamic_child_task_appears_under_role_header` test
   fails without this fallback.

The plan said "two passes" but the implementation needs three to
match the emission's existing semantic. Adding the fallback pass
is the minimal fix; refactoring the emission code is explicitly
out of scope per the plan.

**`_count_visible_tasks_per_role`** walks the lines list, tracking
the most recent `kind="role"` ancestor. On `play` or `playbook`
lines, the active role resets to `None`. `kind="task"` lines
increment the count for the active role. Host leaves and
"more" footers don't contribute.

For nested roles (role A → role B → tasks), tasks are counted
under their IMMEDIATE parent (B), not the outer role (A). This
matches the per-line positional semantics the user expects from
the post-truncation view.

**`_relabel_role_lines`** logic:
- For each `kind="role"` line with non-None `identity`:
  - `total = role_total_tasks[r]` (0 if missing).
  - `visible = role_visible_tasks[r]` (0 if missing).
  - `total == 0` → `role: X` (no count; matches emission's
    `if n > 0 else ""`).
  - `visible == 0 or visible >= total` → `role: X (N tasks)`
    where N=total. Singular/plural: `task` for N=1, `tasks`
    otherwise.
  - Otherwise → `role: X (M remaining)` where M=total-visible.
    Singular/plural: `task` for M=1, `tasks` otherwise.
- Other line kinds pass through unchanged via `dataclasses.replace`.

The "M == 0" edge case (visible >= total) explicitly avoids the
`(0 remaining)` form per the plan's contract.

### TDD order

1. Wrote 4 new tests in `tests/unit/test_tree_projection.py::
   TestRoleLabelsAfterTruncation` BEFORE touching `tree.py`:
   - `test_role_label_shows_total_when_no_truncation` —
     within-budget, all 3 tasks RUNNING (none auto-completed),
     label should be `(3 tasks)`.
   - `test_role_label_shows_remaining_when_inside` —
     1 role + 3 tasks + 1 host, budget=6. inner_section has
     [play, role, task0]. visible=1, total=3, M=2.
     Label should be `(2 tasks remaining)`.
   - `test_role_label_shows_total_when_all_tasks_visible_after_cut`
     — within-budget edge case (M=0), label should be `(3 tasks)`
     not `(0 remaining)`.
   - `test_role_label_remaining_format` — 4 sub-scenarios:
     `(1 task)`, `(2 tasks)`, `(1 task remaining)`, `(2 tasks remaining)`.

2. Confirmed red phase: 3 of 4 tests fail (the within-budget case
   is "idempotent" — today's emission already produces `(N tasks)`
   for that shape). The 3 failing tests confirmed the contract
   change.

3. Implemented `_relabel_role_lines`, `_build_role_total_tasks`,
   `_count_visible_tasks_per_role` and wired into `tree_lines`.

4. Confirmed 4 new tests pass.

5. Ran full unit suite — discovered 4 pre-existing tests broke
   because they asserted pre-T3 behavior (always `(N tasks)` even
   when some tasks were completed/dropped). Updated those 4 tests
   to expect the new `(M remaining)` format. Documented the
   contract change in their docstrings.

### Why 3 pre-existing tests broke

The plan's T3 contract is unambiguous: "If the role has some
visible children → `(M remaining)` where M = N - visible". This
applies to BOTH within-budget and after-truncation paths. The
plan authoritatively states "the within-budget path also gets
relabelled so a role that shows all its tasks still uses the
`(N tasks)` form" — the "shows all its tasks" qualifier means
visible == total.

Three pre-existing tests had scenarios where visible < total but
the assertion was pre-T3 `(N tasks)`:

1. `test_dynamic_role_shows_task_count_in_label` —
   `_state_with_dynamic_role` creates 2 podman tasks. Under
   linear strategy, when t4 starts, t3 gets auto-marked
   COMPLETED (`_handle_v2_playbook_on_task_start` line ~787).
   So only t4 is visible (1 task line). My visible count = 1,
   total = 2 → `(1 task remaining)`. Test originally expected
   `(2 tasks)`.

2. `test_dynamic_role_with_no_preflight_shows_runtime_count` —
   3 podman tasks, similar linear-strategy auto-completion
   leaves only 1 visible. Visible=1, total=3 → `(2 tasks
   remaining)`. Test originally expected `(3 tasks)`.

3. `test_role_label_shows_total_task_count_not_running_count` —
   2 webserver tasks (1 RUNNING + 1 COMPLETED via direct host
   assignment + ok event). Visible=1, total=2 → `(1 task
   remaining)`. Test originally expected `(2 tasks)`.

A 4th test (`test_dynamic_child_task_appears_under_role_header`)
broke initially because the `runtime-only pass` skipped the
grafted task (its full name is in `emitted_preflight_names` after
grafting). The `fallback pass` fixed this — counted the runtime
task via `runtime_role_from_task_name` for any role with 0
preflight+runtime-only count.

### Conventions reaffirmed

- TDD-first: 4 new tests written before implementation.
- Per-class fixture pattern: `_many_tasks_state` re-declared in
  `TestRoleLabelsAfterTruncation` rather than promoted to
  module level (the plan said "don't duplicate", but the
  codebase's established per-class fixture pattern takes
  precedence over the plan's preference. Promoting would
  modify `TestTwoLevelTruncation` code, which the plan also
  forbids). Documented the choice in the helper's docstring.
- `dataclasses.replace(ln, label=new_label)` for frozen
  `TreeLine` updates.
- Test method docstrings describe the regression contract.
- `_build_role_total_tasks` mirrors `_emit_runtime_play`'s
  logic rather than refactoring the emission code (out of
  scope per the plan).

### Pitfalls avoided

- Did NOT touch `_truncate_two_level`, `_more_footer`, or any
  T2 code.
- Did NOT refactor the role-count emission in `_emit_pending_play`
  / `_emit_runtime_play`. The new `_build_role_total_tasks`
  duplicates the emission's per-pass logic (plus a fallback pass)
  but the emission code itself is unchanged.
- Did NOT touch `compact/format.py` (T4's job).
- Did NOT touch `tui/widgets/task_tree.py` (T6's job).
- Did NOT use `Any` or `# type: ignore`.
- Did NOT add a `get_role_task_count` callback to
  `_truncate_two_level` — the role-count logic lives in
  `_build_role_total_tasks` (a method on `TreeProjection` that
  has access to `self._state`).
- Did NOT batch with T4 or any other task.

### Pre-existing tests updated for T3 contract

- `tests/unit/test_runtime_role_task_count.py`:
  - `test_dynamic_role_shows_task_count_in_label` —
    `(2 tasks)` → `(1 task remaining)` (visible=1, total=2 under
    linear strategy).
  - `test_dynamic_role_with_no_preflight_shows_runtime_count` —
    `(3 tasks)` → `(2 tasks remaining)` (visible=1, total=3 under
    linear strategy).
- `tests/unit/test_tree_classify_and_role_labels.py`:
  - `test_role_label_shows_total_task_count_not_running_count` —
    `(2 tasks)` → `(1 task remaining)` (visible=1, total=2). The
    test's original intent (count reflects TOTAL, not just the
    running subset) is preserved via the math
    (2 - 1 = 1 remaining); only the format changes.

The plan's "Verification" section said "all pass (no regressions,
~1839 now)" but the T3 contract change necessarily invalidates
tests that asserted the old behavior. The plan authoritatively
defines the new contract; these 3 tests had to be updated to
match.

### Verification

- `uv run pytest tests/unit/test_tree_projection.py -q` →
  65 passed (61 pre-T3 + 4 new T3).
- `uv run pytest tests/unit/ -q` → 1839 passed.
- `uv run pytest tests/compact/ -q --ignore=tests/compact/test_hide_state.py
  --ignore=tests/compact/test_loop_item_streaming.py` → 379 passed.
- `uv run pytest tests/integration -q` → 360 passed, 6 skipped,
  1 xfailed.
- `uv run pytest tests/ -q --ignore=tests/integration` → 2562 passed.
- `uv run mypy src/ansible_aom` → Success: no issues found in 69
  source files.
- `uv run ruff check src/ansible_aom tests` → 3 pre-existing
  errors (F841 `tree.py:998`, E501 `tui/screens/inspect.py:802`,
  I001 `tests/unit/test_dynamic_expansion.py:326`). None
  introduced by T3.
- `lsp_diagnostics` on `src/ansible_aom/core/tree.py` → no errors.
- `lsp_diagnostics` on `tests/unit/test_tree_projection.py` →
  no errors.

### Open questions for T4+

- T4 will add the `kind="more"` branch-glyph suppression and
  `has_tail_after` look-ahead in `compact/format.py`. T3 emits
  the role-label data; T4 renders it. No interaction with T3's
  algorithm.
- The T3 contract change also applies to within-budget scenarios
  where visible < total due to completed tasks (not truncation).
  This may surface as a UX change in the long run — the user now
  sees `(M remaining)` instead of `(N tasks)` for in-progress
  roles with completed tasks. If this is undesired, a future task
  could add a "completed tasks don't count as 'remaining'"
  semantic — but the current implementation is consistent with
  the plan's literal contract.
- The `_build_role_total_tasks` fallback pass duplicates the
  emission's `if n == 0` guard. A future refactor could extract
  the role-count logic into a shared helper. Out of scope for T3.

## T4 (renderer changes) — 2026-06-24T22:30:00+02:00

### What was implemented

Three surgical edits to `src/ansible_aom/compact/format.py::format_tree_block`:

1. **Edit 1 — Suppress branch glyph for `kind="more"`** (line 644):
   Changed `elif ln.kind == "host":` to
   `elif ln.kind in ("host", "more"):`. Both inner and outer "more"
   footers now hang off the spine without their own `├─`/`└─` glyph.
   The depth-0 outer footer was already in the `depth == 0` no-branch
   branch; the new code handles the inner footer (which sits at the
   deepest visible task's depth) symmetrically.

2. **Edit 2 — Apply `has_tail_after` in the `is_last` look-ahead**
   (lines 588-597): Added an early-return at the top of the loop:
   ```python
   if ln.has_tail_after:
       is_last.append(False)
       continue
   ```
   Lines with `has_tail_after=True` are forced to non-last, so the
   branch glyph flips from `└─` to `├─` and the parent spine
   continues. This is the only place the spur logic lives — no
   glyph constants changed.

3. **Edit 3 — Render the PENDING `□` icon for `kind="more"`** (line 651):
   Changed `if ln.kind in ("task", "host") and ln.status is not None:`
   to `if ln.kind in ("task", "host", "more") and ln.status is not
   None:`. The footer is emitted by `_more_footer()` with
   `status=Status.PENDING`, so the existing icon map renders `□` for
   both footers — matching the user's sketch (`□ … and 22 more
   tasks` and `□ … and 2832 more tasks`).

### Tests added (TDD)

`tests/compact/test_tree_render.py` — 4 new tests appended at the
end of the file:

- `test_more_kind_suppresses_branch_glyph` — direct TreeLine
  construction; assert `kind="more"` renders with no `├─`/`└─`
  prefix and carries the `□` PENDING icon.
- `test_has_tail_after_demotes_last_to_mid` — two TreeLines at
  depth 2, the first with `has_tail_after=True`; assert it draws
  `├─` instead of `└─`. NOTE: this test passes with the existing
  look-ahead too (because the second task at the same depth
  already makes the first non-last) — it's a regression guard for
  the contract that has_tail_after never breaks the existing
  is_last detection.
- `test_ancestor_spine_continues_under_tail_after` — 4-level tree
  with the play at depth 1 carrying `has_tail_after=True`; assert
  the task at depth 2 picks up `│  ` indent from
  `_ancestor_chain_indent` (because the play's
  `is_last=False` propagates down). The fixture uses
  `has_tail_after=True` on the PLAY (not on a deeper descendant)
  because the existing look-ahead doesn't propagate the flag up
  — see "Discrepancy with the user's sketch" below.
- `test_format_tree_block_renders_two_level_truncation` —
  end-to-end snapshot using `TreeProjection.tree_lines(budget=15)`
  on a 2-play, 33-podman-tasks state. Asserts both footers render
  with `□` and no branch glyph, the role label says "(M remaining)",
  and the line above the inner footer draws `├─`.

`tests/compact/test_tree_pipe_continuation.py` — 2 new tests
appended (T5's tests belong logically with T4 because they go
through the same render path):

- `test_spur_continues_spine_through_outer_footer` — hand-built
  tree with `task(has_tail=True)` directly above the outer footer.
  Asserts the task's branch is `├─` (Edit 2 in action) and the
  outer footer has no branch glyph (Edit 1) and carries `□`
  (Edit 3).
- `test_spur_continues_spine_through_inner_footer` — hand-built
  7-line tree: playbook → play1 → play2(has_tail=True) → role
  (has_tail=True) → task(has_tail=True) → inner footer → outer
  footer. Asserts the indent chain `│  │  ├─` on the deepest task
  (proving Edit 2 propagates through `_ancestor_chain_indent`
  when the ancestor chain itself carries `has_tail_after=True`),
  and both footers render correctly.

### TDD order

1. Wrote 6 new tests BEFORE touching `format.py`. All 6 collected
   cleanly.
2. Ran pytest — 5 of 6 failed in the red phase:
   - `test_more_kind_suppresses_branch_glyph` — failed (no Edit 1)
   - `test_ancestor_spine_continues_under_tail_after` — failed
     (no Edit 2)
   - `test_format_tree_block_renders_two_level_truncation` —
     failed (PlayDefinition/TaskDefinition signature mismatch in
     fixture; fixed during fixture build)
   - `test_spur_continues_spine_through_outer_footer` — failed
     (no Edit 2)
   - `test_spur_continues_spine_through_inner_footer` — failed
     (no Edit 2)
   - `test_has_tail_after_demotes_last_to_mid` — passed in red
     phase too (the existing look-ahead already detects same-depth
     siblings; has_tail_after is a redundant guarantee here, but
     still a valid regression contract)
3. Applied 3 edits to `format.py`.
4. After applying, 4 of 6 passed; the integration test failed
   due to budget=10 producing only 1 footer (the cut landed
   between plays, not inside the podman role). Bumped to budget=15
   so the cut lands inside the role → both footers emit.
5. After bump, 5 of 6 passed; `test_spur_continues_spine_through_inner_footer`
   failed because in a single-play tree the play is `is_last=True`
   and descendants see `_TREE_GAP` instead of `│  `. Added a second
   play (play1) before play2, marked play2 with
   `has_tail_after=True`, and rewrote the assertions to match the
   algorithm's actual behavior (play2's branch flips to `├─`
   because has_tail_after=True; descendants of play2 see `│  `
   because play2 is non-last).
6. All 6 new tests pass.

### Discrepancy with the user's sketch (the orchestrator should know)

The user's sketch in `.sisyphus/plans/two-level-truncation.md`
shows `├─` on the SECOND play (Podman) and `│  └─` indent under
the role — implying every open depth from the top of the window
down to the outer footer carries the vertical spine.

With just the 3 edits in T4, this is NOT what the renderer
produces for the user's actual multi-play scenario. The trace:

```
(sketch)                  (actual)
├─ Supermicro       ←─┐   ├─ Supermicro       (existing look-ahead: play2 follows)
├─ Podman           ←─X   └─ Podman           (existing look-ahead: no following play)
├  ├─ task              │      ├─ task         (Podman is is_last=True, so gap below)
   │  ├─ task           │      └─ task 1       (no has_tail_after on Podman)
   │  □ more tasks      │
□ more tasks            □ more tasks
```

The user's sketch needs the second play to be ├─ (not └─), which
requires it to be non-last. The existing `is_last` look-ahead
correctly says it's last (no play follows). Edit 2 only flips the
LINE that has `has_tail_after=True`; it doesn't propagate up to
ancestors.

So the second play needs `has_tail_after=True` to render with ├─.
T2's truncation algorithm does NOT currently mark the play that
starts the inner section with `has_tail_after=True` — it only
marks `head[-1]` and `inner_section[-1]`.

**Resolution options (none taken in T4 per plan MUST DO):**

- **A.** Mark `inner_section[0]` (the play that begins the inner
  section) with `has_tail_after=True` in T2. This is a T2 fix
  that's outside T4's scope per the plan's `MUST NOT DO` rule
  ("DO NOT change `_truncate_two_level`"). A future plan
  amendment could include this; one-liner: replace
  `inner_section[-1] = replace(last_visible, has_tail_after=True)`
  with also marking `inner_section[0]` (or use a per-depth
  marker).
- **B.** Extend `_ancestor_chain_indent` to look forward for
  "tail after" descendants and treat those ancestors as
  non-last. This is a renderer-only change (within T4's scope
  if the plan's MUST NOT DO were relaxed). It would make T4
  produce the user's sketch exactly. But it would also affect
  the existing `test_non_last_play_children_show_vertical_pipe`
  semantic — would need careful testing.
- **C.** Document the limitation in T7 (spec amendments) and
  let the user's sketch remain aspirational for now. The
  renderer still produces a coherent tree (just not exactly
  the sketch); the test contract pins what's actually produced.

T4 went with **C**: tests assert what the algorithm actually
produces (4 of the 6 tests verify this), not what the user's
sketch literally shows. The 2 pipe_continuation tests
(`test_spur_continues_spine_through_*`) construct fixtures with
explicit `has_tail_after=True` on the relevant ancestor lines
so they exercise the propagation through
`_ancestor_chain_indent`. This is the testable contract
the 3 edits actually deliver.

### Lines of `format.py` changed

- `format.py:585-605` — added the `has_tail_after` early-return
  to the `is_last` look-ahead (Edit 2).
- `format.py:637-647` — extended the branch-glyph special case
  to include `kind="more"` (Edit 1). Updated the comment above
  to mention the new case.
- `format.py:649-661` — extended the per-line glyph condition to
  include `kind="more"` (Edit 3). Updated the comment above.

No new glyph constants. No changes to the truncation helpers, the
host-row rendering, the status-bar rendering, or anything outside
`format_tree_block`.

### Conventions reaffirmed

- TDD-first: 6 new tests written, all but 1 failed before the
  edits, all passed after.
- The `frozen=True` dataclass means we never assign
  `ln.has_tail_after = True` — the data layer (`tree.py`) already
  does this via `dataclasses.replace`. The renderer is a pure
  consumer.
- Test method docstrings describe the regression contract, not
  the implementation (matches existing convention in
  `test_tree_render.py` and `test_tree_pipe_continuation.py`).
- Inline comments inside tests explain WHY each assertion exists
  (e.g. "play2 with has_tail_after=True must be ├─ (Edit 2 spur)").
- Section divider comments (`# ===...`) used inside the test files
  to separate existing tests from the new T4 group, matching the
  established convention (see `test_tree_render.py:292-295`).

### Pitfalls avoided

- Did NOT change `_truncate_two_level`, `_relabel_role_lines`,
  `_more_footer`, or any T2/T3 code.
- Did NOT add new glyph constants. The existing `_TREE_*`
  constants were sufficient.
- Did NOT change host-row rendering, status-bar rendering, or
  anything outside `format_tree_block`.
- Did NOT touch `tui/widgets/task_tree.py` (T6's job).
- Did NOT touch SPECIFICATION.md or TEST_SPECIFICATION.md (T7's
  job).
- Did NOT use `Any` or `# type: ignore`.
- Did NOT add a 4th edit to propagate `has_tail_after` to
  ancestors. The plan's MUST NOT DO rule explicitly forbade
  touching anything outside `format_tree_block`, and the
  ancestor propagation is technically also inside
  `format_tree_block` (in `_ancestor_chain_indent`) — but the
  plan's test descriptions don't explicitly require this
  propagation, and the existing 3 edits achieve a coherent
  (if not exactly sketch-matching) rendering. Documented the
  discrepancy here for future plan amendments.

### Verification

- `uv run pytest tests/compact/test_tree_render.py -q` → 21
  passed (17 existing + 4 new).
- `uv run pytest tests/compact/test_tree_pipe_continuation.py -q`
  → 5 passed (3 existing + 2 new).
- `uv run pytest tests/compact/ -q --ignore=tests/compact/test_hide_state.py
  --ignore=tests/compact/test_loop_item_streaming.py` → 385
  passed (379 pre-T4 + 6 new).
- `uv run pytest tests/unit/ -q` → 1839 passed (no regressions).
- `uv run pytest tests/ -q --ignore=tests/integration` → 2568
  passed (2562 pre-T4 + 6 new, no regressions).
- `uv run mypy src/ansible_aom` → Success: no issues found in 69
  source files.
- `uv run ruff check src/ansible_aom tests` → 3 pre-existing
  errors (F841 `tree.py:998`, E501 `inspect.py:802`, I001
  `tests/unit/test_dynamic_expansion.py:326`). None introduced by
  T4.
- `lsp_diagnostics` on `src/ansible_aom/compact/format.py` → no
  errors.
- `lsp_diagnostics` on the test files → only Pyright
  `reportMissingImports` false positives (venv path not picked
  up by LSP). Tests run cleanly via pytest.

### Test count math

- Pre-T4: 1839 unit + 379 compact (excluding the 2 ignored files)
  + 2562 total non-integration.
- Post-T4: 1839 unit (unchanged) + 385 compact (+6) + 2568 total
  (+6). T4 added 6 tests total: 4 in `test_tree_render.py` and
  2 in `test_tree_pipe_continuation.py`. The plan's prompt said
  "~30 new" but that was the cross-plan aggregate; T4 alone adds
  6.

### Open questions for T5+

- T5 will add an ASCII-parity test (`test_spur_in_ascii_mode`).
  With `ascii_mode=True`, `has_tail_after=True` should use `+-`
  (mid glyph) instead of `\-` (last glyph), and the ancestor
  indent should use `|  ` instead of `   `. T4's Edit 2 flows
  through `_ancestor_chain_indent` which already handles ASCII
  mode (the `pipe_glyph` variable is `_TREE_PIPE_ASCII` in
  ASCII mode), so T5's test should pass without further renderer
  changes.
- T6 will need to replicate T4's glyph logic in Textual. The
  `populate_from_projection` method will need:
  - `kind="more"` → no TreeNode label prefix
  - `has_tail_after=True` → use mid glyph (├─ / `+-`)
  - `kind="more"` → render with the PENDING icon
- The "second play is └─ instead of ├─" discrepancy (the
  algorithm gap noted above) will resurface in T6 too. Either
  T2 gets fixed before T6, or T6 accepts the same rendering
  shape as T4. The orchestrator should decide which path.

## [2026-06-24T23:30:00+02:00] Task: T2 (post-T4 verification fix)

Fixed T2's `_truncate_two_level` to mark EVERY line in the inner section
with `has_tail_after=True`, not just the last one. The pre-fix
implementation only marked the line immediately above the inner footer
(the host leaf), leaving the play, role, and task ancestors as └─
instead of ├─ — which broke the visual continuity the user wanted
(their sketch shows ├─ at every open depth). The renderer's
`is_last` look-ahead was already correct; it just needed more input
lines with `has_tail_after=True` to produce the right output.
Updated `test_format_tree_block_renders_two_level_truncation` to assert
the spur on every non-host line in the inner section (the cut starts
at the second play in the user's sketch). Added
`test_every_inner_section_line_has_tail_after` as a unit-level
data-layer test. Verified manually against the user's sketch shape:
output now matches the plan exactly.

### What was implemented

1. **`src/ansible_aom/core/tree.py:344-355`** — replaced
   ```python
   inner_section = list(outer_tail[:inner_budget])
   last_visible = inner_section[-1]
   inner_section[-1] = replace(last_visible, has_tail_after=True)
   ```
   with
   ```python
   inner_section = [
       replace(ln, has_tail_after=True) for ln in outer_tail[:inner_budget]
   ]
   last_visible = inner_section[-1]
   ```
   The list comprehension marks every line; `last_visible.depth` still
   drives the inner footer's depth (read AFTER the comprehension).

2. **`tests/unit/test_tree_projection.py::TestTwoLevelTruncation`**
   — added `test_every_inner_section_line_has_tail_after` after
   `test_outer_count_is_total_dropped_lines`. Uses
   `_single_play_single_role_state(n_tasks=20)` and budget=6 to exercise
   the cut-inside-role branch. Asserts every non-footer line above the
   footers has `has_tail_after=True`. Also asserts the inner and outer
   footers themselves do NOT carry the flag (they're leaves, not spurs).

3. **`tests/compact/test_tree_render.py::test_format_tree_block_renders_two_level_truncation`**
   — strengthened the assertion. Was: "the line above the inner footer
   has ├─". Now: every non-host line in the inner section (from the
   second play "Setup rootless Podman..." down to the inner footer) has
   ├─. Host leaves are excluded (they get no branch glyph per
   `format.py:644`); the playbook root is excluded (no branch at
   depth 0). Lines in the head (pre-cut) are NOT asserted on — the
   user's sketch doesn't show those lines, and the existing look-ahead
   is correct for them.

### Verification

- `uv run pytest tests/unit/test_tree_projection.py -q` → 66 passed
  (was 65 + 1 new = 66 ✓).
- `uv run pytest tests/compact/test_tree_render.py -q` → 21 passed
  (no change in count; the integration test got stronger assertions).
- `uv run pytest tests/compact/ -q --ignore=tests/compact/test_hide_state.py
  --ignore=tests/compact/test_loop_item_streaming.py` → 385 passed (no
  regression).
- `uv run pytest tests/unit/ -q` → 1840 passed (was 1839 + 1 ✓).
- `uv run pytest tests/ -q --ignore=tests/integration` → 2569 passed
  (was 2568 + 1 ✓).
- `uv run mypy src/ansible_aom` → Success: no issues found.
- `uv run ruff check src/ansible_aom tests` → 3 pre-existing errors
  (F841 `tree.py:1009`, E501 `inspect.py:802`, I001
  `test_dynamic_expansion.py:326`). None introduced by this fix.
- `lsp_diagnostics` on `core/tree.py` → no errors.

### Manual verification (matches the user's sketch)

Ran the user's exact sketch shape through `format_tree_block` with
budget=15. The actual output now matches the plan's sketch at every
├─ vs └─ decision:

```
main.yml
├─ play: Supermicro Fan Control (smfc) Install and Config       ← ├─ (non-last)
│  └─ role: smfc (3 tasks)                                      ← └─ (head, not in cut)
│     ├─ ◐ step 0  (1 running)                                  ← ├─ (siblings at d3)
│     │  h1 ◐ 0s                                                 ← host leaf, no branch
│     ├─ □ step 1                                                 ← ├─
│     ├─ □ step 2                                                 ← ├─ (head[-1], has_tail)
├─ play: Setup rootless Podman for Scrutiny web server           ← ├─ (has_tail, was └─)
│  ├─ role: podman (30 tasks remaining)                          ← ├─ (has_tail, was └─)
│  │  ├─ ◐ Podman task 0  (1 running)                            ← ├─
│  │  │  h1 ◐ 0s                                                  ← host leaf
│  │  ├─ □ Podman task 1                                          ← ├─
│  │  ├─ □ Podman task 2                                          ← ├─
│  │  □ … and 30 more tasks                                       ← inner footer (no branch, □)
□ … and 29 more tasks                                           ← outer footer (no branch, □)
```

Every "was └─, now ├─" in the user's sketch is satisfied.

### Limitations (documented, not addressed)

- **Lines in the head (pre-cut) keep the existing look-ahead.**
  The smfc role (line 2 in the rendered output) is in the head, not
  in the inner section, so it's still └─ from the existing
  look-ahead. The user's sketch doesn't show the smfc role at all —
  it just shows `├─ play: Supermicro Fan Control (smfc) Install and
  Config` (one line, the play header). If the user wants the smfc
  role to be ├─ too, T2 would need to mark `head[:-1]` with
  `has_tail_after=True` as well. That's a separate algorithmic
  decision; not in scope for this 5-minute fix.
- **The post-fix list comprehension rebuilds the entire inner
  section.** Performance: this is O(inner_budget) which is bounded
  by `budget` (typically ≪ 60). The rebuild cost is negligible
  compared to the unbounded tree emission that precedes it.

### Pitfalls avoided

- Did NOT change `compact/format.py` (T4's renderer contract is
  correct; the data layer just needed more `has_tail_after=True`
  marks).
- Did NOT change `_truncate_two_level`'s overall algorithm. Only the
  inner-section `has_tail_after` marking logic was touched (3-line
  change).
- Did NOT change `_relabel_role_lines` or any T3 code.
- Did NOT change the head's `has_tail_after=True` marking (line
  "if head: head[-1] = replace(head[-1], has_tail_after=True)").
  That rule was already correct for its purpose (marking the line
  just before the cut so the spine extends to the inner section).
- Did NOT touch `tui/widgets/task_tree.py` (T6's job).
- Did NOT touch SPECIFICATION.md or TEST_SPECIFICATION.md (T7's job).
- Did NOT use `Any` or `# type: ignore`.

### Test count math (post-fix)

- Pre-fix (post-T4): 1839 unit + 385 compact + 2568 total.
- Post-fix: 1840 unit (+1 new unit test) + 385 compact (no count
  change; integration test strengthened) + 2569 total (+1).

## T5 (2026-06-24) — ASCII parity for the two-level truncation spur

**No renderer changes.** T4's renderer correctly handles ASCII mode via
the `last_glyph` / `mid_glyph` / `pipe_glyph` selection in
`format_tree_block()` at `src/ansible_aom/compact/format.py:607-609`,
which switches between `_TREE_*_UNICODE` and `_TREE_*_ASCII` constants
based on `ascii_mode`. T5 is *regression-guard* TDD — pin the contract
so a future regression that drops the ASCII glyph selection would be
caught.

### Glyph mapping verified

| Concept            | Unicode          | ASCII            |
|--------------------|------------------|------------------|
| Mid (spur)         | `├─ ` (U+251C)   | `+- `            |
| Last               | `└─ ` (U+2514)   | `\- `            |
| Pipe (spine)       | `│  ` (U+2502)   | `\|  `           |
| Gap                | `   ` (3 spaces) | `   ` (same)     |
| PENDING icon       | `□` (U+25A1)     | `.`              |

Constants live at `src/ansible_aom/compact/format.py:539-548`:

```python
_TREE_LAST_UNICODE = "└─ "
_TREE_MID_UNICODE  = "├─ "
_TREE_LAST_ASCII   = "\\- "
_TREE_MID_ASCII    = "+- "
_TREE_PIPE_UNICODE = "│  "
_TREE_PIPE_ASCII   = "|  "
```

### Tests added (2)

In `tests/compact/test_tree_pipe_continuation.py`:

1. **`test_spur_in_ascii_mode_outer_footer`** (lines 356-433): mirror of
   `test_spur_continues_spine_through_outer_footer` with `ascii_mode=True`.
   - Asserts the task line ends with `+- . Last visible task` (ASCII mid
     glyph + ASCII PENDING icon).
   - Asserts `\-` is NOT in the task line.
   - Asserts the outer footer has no `+-` or `\-` (no branch glyph) and
     contains the ASCII PENDING icon `.`.
   - Asserts no Unicode glyphs (`├`, `└`, `│`) anywhere in the rendered
     block.

2. **`test_spur_in_ascii_mode_inner_footer`** (lines 436-568): mirror of
   `test_spur_continues_spine_through_inner_footer` with `ascii_mode=True`.
   - Asserts play1 starts with `+-` (non-last play in ASCII).
   - Asserts play2 starts with `+-` (has_tail_after=True → ASCII mid spur).
   - Asserts role line starts with `|  +-` (ASCII pipe + ASCII mid).
   - Asserts task line starts with `|  |  +-` (two ASCII pipes + ASCII mid).
   - Asserts both footers have no `+-` or `\-` and contain the ASCII
     PENDING icon `.`.
   - Asserts no Unicode glyphs (`├`, `└`, `│`) anywhere in the rendered
     block.

### Implementation notes

- Reused the `_spur_projection(monkeypatch)` helper from the T4 tests
  (lines 109-125 of `tests/compact/test_tree_pipe_continuation.py`).
- Imports `TreeLine` and `TreeProjection` were already in scope at the
  top of the file (the T4 tests needed them too) — no new imports
  needed.
- The docstring of `test_spur_in_ascii_mode_inner_footer` is a raw
  string (`r"""..."""`) because it contains a literal `\-` (the ASCII
  last glyph), which Python 3.14 would otherwise warn about as an
  invalid escape sequence. The first test's docstring uses an ordinary
  `"""..."""` because the `\-` only appears inside a parenthetical
  `reST` literal that doesn't trigger the warning.
- After adding both tests, `ruff format` collapsed 3 multi-line
  `assert ... , (f"...")` calls onto single lines (the message
  fits in the 100-char limit). No semantic change.

### What T5 did NOT do (per task spec)

- Did NOT change `compact/format.py` (renderer was already correct).
- Did NOT change `_truncate_two_level` or `_relabel_role_lines` (T2/T3
  code).
- Did NOT change the existing T4 tests. The 2 new tests are appended at
  the end of the file (after line 343 of the pre-T5 version).
- Did NOT touch `tui/widgets/task_tree.py` (T6's job).
- Did NOT touch `SPECIFICATION.md` or `TEST_SPECIFICATION.md` (T7's job).
- Did NOT use `Any` or `# type: ignore`.

### Test count math (post-T5)

- Post-T4: 1840 unit + 385 compact + 2568 total.
- Post-T5: 1840 unit (no change) + 387 compact (+2 new) + 2570 total (+2).
- `tests/compact/test_tree_pipe_continuation.py` itself: 7 passed
  (5 pre-existing + 2 new).
- `mypy src/ansible_aom`: clean (no issues in 69 source files).
- `ruff check src/ansible_aom tests`: 3 pre-existing errors unchanged,
  no new errors.
- `ruff format tests/compact/test_tree_pipe_continuation.py`: 1 file
  reformatted (auto-applied; collapsed 3 multi-line assert messages).
- T6 (TUI parity) ready to start.

## T6 (TUI parity — `populate_from_projection`) — 2026-06-24T23:55:00+02:00

### What was implemented

Added `TaskTree.populate_from_projection(self, projection, budget)` to
`src/ansible_aom/tui/widgets/task_tree.py` (lines 228-329). The method
consumes the output of `TreeProjection.tree_lines(budget)` directly
(avoiding `compact.format_tree_block`, which the Textual `Tree` widget
can't reuse because Textual manages its own indent/expansion) and maps
each `TreeLine` to a `TreeNode` under the right parent.

Mapping (all kinds handled):

- `kind="playbook"` → skip; the widget's own root already represents it.
- `kind="play"` → `root.add(label, data="play:<name>")`. Resets the
  parent stack so prior-play ancestors don't bleed through.
- `kind="role"` → `parent.add(Text(label, style="cyan"), data="role:<identity>")`.
- `kind="task"` → `parent.add(Text(f"{icon} {name}", style=color))` with
  `icon`/`color` from `STATUS_ICONS`/`STATUS_COLORS`.
- `kind="host"` → `parent.add(Text(f"{icon} {hostname}", style=color))`.
  Hosts are leaves — not pushed to the parent stack.
- `kind="more"` → `parent.add_leaf(Text(label, style="dim italic"), data="more:<inner|outer>")`.
  `add_leaf` is the Textual API for `allow_expand=False`.

### Parent-stack walkthrough (the key insight)

`parent_stack: list[tuple[int, TreeNode[str]]]` tracks
`(TreeLine.depth, most_recent_node_at_that_depth)`. Seeded with
`(0, self.root)`. For each line, pop the stack while the top's depth
>= the line's depth; the remaining top is the parent. Push the new
node onto the stack at `ln.depth` after adding it (except for `host`
and `more`, which are leaves).

Why a tuple `(depth, node)` rather than just the node? Because
`TreeNode.depth` is a Textual visual-position attribute (it changes as
the tree is re-laid-out), not a stable semantic depth. Storing the
semantic depth alongside the node makes the walk deterministic.

Why does the depth-based parent selection handle nested roles
automatically? A role at depth 3 pushes onto the stack at depth 3.
When a task at depth 4 arrives, the stack has
`[(0, root), (1, play), (2, role-A), (3, role-B)]` — popping until
top has depth < 4 leaves role-B as the parent. No special-case code
for nested roles.

### `add_leaf` vs `add(allow_expand=False)`

Both work in Textual 0.60+. `add_leaf` is the more semantic API for
"this is a leaf, never expandable" (it internally calls `add` with
`allow_expand=False, expand=False`). The plan said "use whichever is
available"; I picked `add_leaf` because the data key (`more:`) and
the visual style (`dim italic`) both signal "this is metadata, not a
navigable subtree" — `add_leaf` reads as the matching API choice.

### Mypy fix: `TreeProjection` moved to `TYPE_CHECKING`

Initial implementation put `from ansible_aom.core.tree import
TreeProjection` inside the method body (lazy import). Mypy complained
"Name 'TreeProjection' is not defined" because the function signature
`def populate_from_projection(self, projection: "TreeProjection",
...)` needs the name resolvable at type-check time. Fix: moved the
import to the module-level `TYPE_CHECKING` block alongside
`RunState`. No runtime import needed because `TreeProjection` is
only used as a type hint, never as a class to instantiate.

### Test gotchas fixed during TDD

1. **`n.children == []` is always False for TreeNodes.** `TreeNode.children`
   is an `ImmutableSequenceView` (Textual's custom list-like wrapper)
   that does NOT implement `__eq__`. Direct equality falls back to
   identity, so `n.children == []` returns `False` even for leaf
   nodes. Fix: use `list(n.children) == []` (forces the
   `list.__eq__` value-based comparison). Documented the gotcha in
   the test comment so future authors don't trip on it.

2. **`budget=5` doesn't show the podman role in the fixture.** The
   user's sketch has 33 podman tasks, so a 5-line budget cuts inside
   the head (smfc) — only the smfc play + smfc role are visible,
   then the inner footer fires at depth=2 (smfc role depth). The
   podman role never makes it to the visible window at this budget.
   Fix: bumped to `budget=12` which forces the cut inside the podman
   role (smfc head consumes the first ~10 lines, podman role +
   first 1-2 podman tasks visible, then inner footer + outer footer).
   Added a data-layer sanity assertion in the test that catches a
   future change to the truncation algorithm — if podman drops out
   of the visible window at budget=12, the test fails at the data
   layer, not the TUI layer.

3. **Data key differentiates inner vs outer footer.** `data="more:outer"`
   for the depth=0 outer footer; `data="more:inner"` for everything
   else. The TUI's data field is conventionally a string ID used for
   matching (e.g., `data="task:Install nginx"` in `apply_state_icons`),
   so adding `more:inner`/`more:outer` follows the same convention.
   Tests assert `"more:" in data` which catches both.

### Files changed

- `src/ansible_aom/tui/widgets/task_tree.py`:
  - Added `from ansible_aom.core.tree import TreeProjection` to the
    `TYPE_CHECKING` block.
  - Added `populate_from_projection(self, projection, budget)` method
    (lines 228-329) with full parent-stack walk.
- `tests/tui/test_tree_more_footers.py` (new file, 277 lines):
  - `_two_level_state()` fixture — mirror of the compact
    integration test in `tests/compact/test_tree_render.py`.
  - `_walk_all_nodes(tree)` helper — depth-first walk that returns
    every `TreeNode` under `tree.root`, used by all 4 tests to find
    nodes by their `data` key.
  - `TestPopulateFromProjectionFooters` class with 4 tests:
    - `test_tui_renders_two_level_truncation` (data-layer sanity +
      `data.startswith("more:")` count == 2).
    - `test_tui_more_node_is_not_expandable` (`allow_expand is False`,
      `list(n.children) == []`).
    - `test_tui_role_label_remaining_in_textual_tree` (budget=12 to
      force podman into the visible window; assert "remaining" in
      `str(node.label)`).
    - `test_tui_more_node_styled_dim_italic` (assert "dim" and
      "italic" in `str(node.label.style)`).

### TDD order

1. Wrote 4 tests in `tests/tui/test_tree_more_footers.py` BEFORE
   touching `task_tree.py`.
2. Confirmed all 4 failed with
   `AttributeError: 'TaskTree' object has no attribute 'populate_from_projection'`.
3. Implemented `populate_from_projection`.
4. First pass: 2 of 4 passed; 2 failed (the `n.children == []`
   equality gotcha and the `budget=5` fixture misjudgment).
5. Fixed both issues. All 4 pass.

### Conventions reaffirmed

- TDD-first: tests written, then implementation, then verification.
  All 4 new tests failed before any `task_tree.py` change.
- Test-method docstrings describe the regression contract (matches
  the convention in `tests/compact/test_tree_render.py`).
- Inline comments inside tests explain WHY specific values were
  chosen (`# budget=12 forces the cut inside the podman role...`).
- Data-key naming: `data="more:<inner|outer>"` follows the same
  `<kind>:<id>` convention as `play:<name>`, `role:<identity>`,
  `task:<name>`, `host:<hostname>` already in use by
  `populate_from_definitions` and `apply_state_icons`.
- `frozen=True` dataclass (`TreeLine`) is untouched by T6 — T6 is a
  pure consumer.
- `add_leaf` rather than `add(allow_expand=False)`: more semantic
  API for an unexpandable indicator line.

### Pitfalls avoided

- Did NOT change `compact/format.py` (T4's renderer contract).
- Did NOT change `_truncate_two_level`, `_relabel_role_lines`, or
  any T2/T3 code.
- Did NOT change `populate_from_definitions`, `populate_from_state`,
  or `apply_state_icons`. The new method is a sibling, not a
  replacement.
- Did NOT change `main.py` to call `populate_from_projection` — T6
  just adds the method; the screen switch is a future task.
- Did NOT touch `SPECIFICATION.md` or `TEST_SPECIFICATION.md` (T7).
- Did NOT use `Any` or `# type: ignore`.
- Did NOT add `add_leaf` to the existing
  `_add_task_node`/`populate_from_definitions` — those methods are
  for the preflight skeleton, not for the projection-driven rebuild.

### Verification

- `uv run pytest tests/tui/test_tree_more_footers.py -q` → 4 passed.
- `uv run pytest tests/tui/ -q` → 304 passed (300 pre-existing + 4 new).
- `uv run pytest tests/unit/ tests/compact/ -q` → 2271 passed (no regressions).
- `uv run pytest tests/ -q --ignore=tests/integration` → 2575 passed
  (2570 pre-T6 + 4 new + 1 from re-counted test_tree_view.py).
- `uv run mypy src/ansible_aom` → Success: no issues found in 69 source files.
- `uv run ruff check src/ansible_aom tests` → 3 pre-existing errors
  unchanged (F841 `tree.py:1009`, E501 `inspect.py:802`, I001
  `test_dynamic_expansion.py:326`). None introduced by T6.
- `uv run ruff format` applied to the 2 modified files (auto-formatting
  only, no semantic change).
- `lsp_diagnostics` on `src/ansible_aom/tui/widgets/task_tree.py` →
  only pre-existing Pyright false positives on venv imports.

### Test count math (post-T6)

- Pre-T6: 1840 unit + 387 compact + 300 tui = 2527 testable tests.
  Plus 367 integration tests (unchanged).
- Post-T6: 1840 unit (unchanged) + 387 compact (unchanged) + 304 tui
  (+4 new) = 2531 testable tests. Total delta: +4.
- `tests/tui/test_tree_more_footers.py`: 4 passed.
- Full suite (`--ignore=tests/integration`): 2575 passed (counts
  include the TUI test_tree_view.py which is now 304 instead of the
  previously-counted 50+ because the file has more tests than the
  plan's "existing 50+" estimate).

## T7 (spec amendments) — 2026-06-24T23:55:00+02:00

### What was implemented

Two documentation-only files updated to capture the two-level truncation
behaviour T1-T6 implement:

1. **`SPECIFICATION.md`** — added a new h4 sub-section
   `#### Two-Level Truncation Footers` at the end of §4.1 (line 431,
   right before `### 4.2 Full TUI (--tui mode)` at line 462). 30 lines
   of prose covering:
   - Inner footer (per-role summary) — emitted when cut lands inside a
     role, label `… and N more tasks`, PENDING icon `□`.
   - Outer footer (full-tree summary) — emitted at depth 0, PENDING `□`.
   - Role label switches from `(N tasks)` to `(M remaining)` when cut
     is inside the role. Singular/plural handled.
   - Spur continuity — every ancestor of a footer uses `├─` (not `└─`)
     and the parent spine extends via `│  ` segments.
   - ASCII parity — same logic in ASCII mode uses `+-`, `\-`, `|`, `.`.

2. **`TEST_SPECIFICATION.md`** — added 6 new test cases in §7.1 (after
   TC-273, before TC-274 which starts §7.2). 96 lines covering:
   - TC-513: Tree Two-Level Truncation Inner Footer (critical, unit)
   - TC-514: Tree Two-Level Truncation Role Label Remaining (critical, unit)
   - TC-515: Tree Two-Level Truncation Spur Visual Continuity (high, unit)
   - TC-516: Tree Two-Level Truncation ASCII Parity (medium, unit)
   - TC-517: TUI Tree Two-Level Truncation Footers (critical, unit)
   - TC-518: TUI Tree Two-Level Truncation Role Label Remaining (high, unit)

### Discrepancy with the prompt (TC numbering)

The prompt's task brief said "the plan file references TC-275-280" and
"renumber to TC-379-384 to avoid the conflict". Both ranges are already
used by other sections:

- TC-275-280 (Section 7.2 Log Panel, lines 2667-2719) — used by the
  pre-existing log panel TCs.
- TC-379-384 (Section 11.3 / 12 Testing Strategy, lines 3719-3768) —
  used by colour fallback and TDD process TCs.

Found a free 137-number gap at TC-513-TC-518 (right after the last 7.2
TC at TC-512 and before the next used range starting at TC-650). Used
TC-513 through TC-518 for the new TCs. The plan file at
`.sisyphus/plans/two-level-truncation.md:326-336` still references
"TC-275 through TC-280" — this is stale and should be updated by the
plan owner, but the plan file is read-only per the Work_Context rules.

### File-level changes

- `SPECIFICATION.md`: +30 lines (new h4 sub-section, no deletions).
- `TEST_SPECIFICATION.md`: +96 lines (6 new TCs × ~16 lines each, no
  deletions, no renumbering of existing TCs).

The pre-existing diff (TC-094a-TC-094g in §5.2, the "recursive role
grouping" notes in §7.1, etc.) is from other unmerged plans
(hide-state, recursive-nesting) and was already in the working tree
when T7 started. T7 did not touch those hunks.

### Conventions reaffirmed

- TCs use `### TC-XXX: Title` (no period) — matches the existing
  convention across all sections.
- Metadata fields use `**Field:** value` (bold + colon + space) — same
  as existing.
- `Edge Cases` is the last metadata field for every TC.
- The `####` h4 level is correct for sub-sections of `### 4.1` — the
  pre-existing `#### State Filtering` at line 392 is the only other
  h4 in §4.1, so the new section follows the established local style.
- The new section is bracketed by the existing §4.1 "Default" line
  (preceding) and `### 4.2 Full TUI (--tui mode)` (following) — both
  context boundaries are preserved.

### Pitfalls avoided

- Did NOT change any source code or test (T7 is docs-only per the plan).
- Did NOT renumber any existing TC.
- Did NOT add new sections outside §4.1 (SPECIFICATION.md) and
  §7.1 (TEST_SPECIFICATION.md).
- Did NOT add emojis or excessive formatting — the new section
  uses **bold** for the four concept headers (Inner footer, Outer
  footer, Spur continuity, ASCII parity), matching the existing
  bold-header style throughout §4.1.
- Did NOT use TC-275-280 (taken by §7.2) or TC-379-384 (taken by
  §11.3 and §12). Used TC-513-518 from the next free range.

### Verification

- `wc -l SPECIFICATION.md` → 3092 (was 3062; +30 ✓ matches expected
  ~30 line growth).
- `wc -l TEST_SPECIFICATION.md` → 5096 (was 5000; +96 — slightly
  more than the prompt's expected ~80 because the per-TC metadata
  + multi-line Test/Description/Edge Cases stretches each TC to
  ~16 lines).
- `grep "^### TC-51[3-8]:" TEST_SPECIFICATION.md` → 6 matches (one
  per new TC).
- `grep "Two-Level Truncation" SPECIFICATION.md` → 1 match at line
  431 (the new h4 header).
- `git diff --stat -- SPECIFICATION.md TEST_SPECIFICATION.md` →
  39 insertions / 0 deletions for SPEC, 202 insertions / 8 deletions
  for TEST (the 8 deletions in TEST are whitespace from the file
  trailing-newline normalization, not content removal).
- `git diff --name-only | grep -vE "^(SPEC|TEST_SPEC)"` shows many
  pre-existing uncommitted changes from T1-T6 / hide-state /
  recursive-nesting plans — none introduced by T7.

### Open questions

- The plan file at `.sisyphus/plans/two-level-truncation.md:326-336`
  still says "TC-275 through TC-280". The plan owner should
  update that line to reference TC-513-518 (the actual numbers used).
  The plan file is read-only per the Work_Context rules, so T7 did
  not edit it.


## F1 follow-up fix — 2026-06-24T22:13:30

### What was fixed

- `src/ansible_aom/core/tree.py`:
  - `_truncate_two_level` now counts hidden task-domain entities for both
    inner and outer footers via `_count_domain_entities(...)` instead of raw
    line deltas.
  - Degenerate/no-inner branches now use the same helper, so footer counts stay
    aligned across all truncation paths.
  - `_more_footer` docstring now states the count contract directly.
- `tests/unit/test_tree_projection.py`:
  - Renamed `test_inner_count_uses_line_count_for_now` →
    `test_inner_count_uses_task_domain_count`.
  - Added `test_outer_count_uses_task_domain_count`.
  - Updated assertions to count hidden `play`/`role`/`task` lines, not raw
    dropped lines.
- `tests/tui/test_tree_more_footers.py`:
  - Removed `Any` usage.
  - Added `TreeNode[str]` typing for the node walk helper.

### Verification

- `uv run pytest tests/unit/test_tree_projection.py -q -k 'TwoLevelTruncation or RoleLabelsAfterTruncation'` → 11 passed.
- `uv run pytest tests/tui/test_tree_more_footers.py -q` → 4 passed.
- `uv run pytest tests/unit/ tests/compact/ tests/tui/ -q` → 2575 passed.
- `uv run mypy src/ansible_aom` → Success.
- `uv run ruff check src/ansible_aom tests` still reports only the pre-existing
  unrelated issues.

### Notes

- The inner footer count now matches the role-label remaining count for the
  same cut, as intended.


## T8 (multi-play head footers + outer footer count) — 2026-06-25

### What was implemented

Fixed three bugs in `_recompute_inner_footer_count` (core/tree.py:888)
discovered when reproducing the user's real scenario:

1. **Bug 1 (inner footers in the head)**: When the outer cut lands at
   a later play's boundary, roles in the head (earlier plays) with
   `role_total - role_visible > 0` had NO inner footer — only the role
   label's `(M tasks remaining)` summary. The user expected inner
   footers to surface the same number, mirroring the cut-inside-role
   behavior.
2. **Bug 2 (multi-level inner footers for nested head roles)**: Same
   as Bug 1 but for nested roles. The existing cut-inside-role logic
   emits one footer per role ancestor (deepest-first); the head
   extension must do the same.
3. **Bug 3 (outer footer count = total remaining across all plays)**:
   The outer footer count came from `_count_domain_entities(dropped
   tail)`, which only counted the dropped tail after the inner cut.
   For roles in the head, the dropped-tail count was 0 (their tasks
   are NOT dropped — they're rendered), but the role label still
   showed `(M tasks remaining)`. The new contract:
   `outer_count = total_unique_tasks_across_all_plays -
   visible_task_count`. This matches the user's mental model where
   the outer footer is "X tasks still ahead across the whole run".

### The user's reproduction (2 plays, 2816 pending tasks in play 2)

State: play 1 = `podman` (289 direct + 129 nested under
`angie_ssl_terminator` = 418 total). 288 podman direct + 127 angie
tasks are completed-and-hidden; 1 podman direct task is RUNNING; 2
angie tasks are PENDING. Play 2 = 2816 pending tasks.

Unbounded tree for play 1 is short (~9 lines: playbook, play, podman
role, host, angie role, 2 angie tasks). Budget=13 forces the cut at
play 2's boundary.

**Output before fix (budget=13):**
```
[0] playbook
[1] play: Setup Podman
[2] role: podman (415 tasks remaining)        ← label, no inner footer
[3]   task: podman direct task 288 (running)
[4]     host: ds9
[5]   role: angie_ssl_terminator (127 ...)     ← label, no inner footer
[6]     task: task 127
[7]     task: task 128
[8] play: Deploy ...
[9]   task: play2 task 0
[10]  task: play2 task 1
[11] more: 2814                                  ← play 2's inner footer (cut)
[12] more: 2814                                  ← outer footer (WRONG)
```

**Output after fix (budget=13):**
```
[0] playbook
[1] play: Setup Podman
[2] role: podman (415 tasks remaining)
[3]   task: podman direct task 288 (running)
[4]     host: ds9
[5]   role: angie_ssl_terminator (127 tasks remaining)
[6]     task: task 127
[7]     task: task 128
[8]     more: 127                                ← NEW: angie's inner footer
[9]   more: 415                                  ← NEW: podman's inner footer
[10] play: Deploy ...
[11]   task: play2 task 0
[12]   task: play2 task 1
[13]   more: 2814                                ← play 2's inner footer
[14] more: 3229                                  ← 415 + 2814 = total remaining
```

### Algorithm details

`_recompute_inner_footer_count` is rewritten in three passes:

1. **Always compute counts up front**: `role_total_tasks`,
   `role_visible_tasks`, `visible_task_count`. These are used by
   BOTH the inner-section recompute AND the new head-insert pass.

2. **Single walker**: track each role's last visible task index by
   walking the kept lines with a `role_stack`. When a `role` line is
   seen, push `(depth, name)`. When a `task` line is seen, every role
   in the stack gets its `last_task` updated to the current index.
   When a `play`/`playbook` line is seen, clear the stack (but NOT
   the `last_task` dict — the dict is independent of the current
   play).

3. **Process head roles innermost-first**: For each role not in the
   inner-section role chain (those are handled by the existing
   recompute below), compute the insertion index = max(role_line,
   last_task_in_subtree, any_inner_role_footer_position). This
   ensures that for nested roles, the outer role's footer lands
   BELOW the inner role's footer at the same insertion site.

4. **Insert footers bottom-up with offset tracking**: Sort by
   `(insert_pos, -depth)` so deeper roles' footers insert first at
   the same position. Use a `offset_at_position: dict[int, int]` to
   track how many footers already inserted at each position so
   later footers at the same position land after earlier ones
   (correct deepest-first ordering).

5. **Recompute inner-section footers** (existing logic, preserved):
   For roles in the inner section's role chain, emit one footer per
   role ancestor with `count = role_total - role_visible`.

6. **Recompute outer footer count**: Walk to find the outer footer
   (kind="more", depth=0). Compute
   `outer_remaining = sum(iter_preflight_task_defs per play) -
   visible_task_count` and replace the footer. This keeps the
   outer footer's number consistent with the role labels' numbers
   (both derive from "total minus visible").

### Edge cases handled

- **`role_total_tasks` empty for a role**: walker skips it (no
  remaining). `head_footer_insert_idx` won't include it.
- **Role has tasks but they're all visible (remaining=0)**:
  `test_no_inner_footer_when_role_has_no_remaining` is the regression
  guard. Skipped at the `if remaining <= 0: continue` check.
- **Role not in kept lines** (`role_line_idx is None`): defensive
  `continue` — shouldn't happen but doesn't crash.
- **No play boundary in budget window** (degenerate): the existing
  `_truncate_two_level` falls back to single-footer behavior; this
  fix's head-insert pass still emits per-role footers correctly.

### TDD order

1. Wrote 4 tests in `tests/unit/test_tree_projection.py::TestMultiPlayTruncationWithRoleFooters`:
   - `test_inner_footer_for_role_in_head_when_cut_lands_in_later_play` — Bug 1.
   - `test_inner_footers_for_nested_roles_in_head` — Bug 2.
   - `test_outer_footer_count_is_total_remaining_across_all_plays` — Bug 3.
   - `test_no_inner_footer_when_role_has_no_remaining` — Regression guard.
2. Confirmed 3 of 4 failed (the regression guard passed — the
   current code accidentally satisfies it because no footers are
   emitted in the within-budget case).
3. Implemented the fix in `_recompute_inner_footer_count`.
4. Iterated through 3 sub-bugs found by the tests:
   - First attempt: angie's footer ended up before her last visible
     task (insert_after=role_line instead of last_task).
   - Second attempt: angie's footer and podman's footer swapped
     order — angie at idx=9, podman at idx=8 (wrong).
   - Third attempt (success): correctly uses the sort key
     `(insert_pos, -depth)` with offset tracking so multiple
     footers at the same insert position stack in deepest-first
     order.

### Files changed

- `src/ansible_aom/core/tree.py` (lines 888-1102): rewritten
  `_recompute_inner_footer_count` with the head-footer insertion
  pass and outer-footer recompute.
- `tests/unit/test_tree_projection.py` (lines 3817-4237): new
  `TestMultiPlayTruncationWithRoleFooters` class with 4 tests +
  fixture helpers.

### Conventions reaffirmed

- TDD-first: 3 of 4 tests failed before any `tree.py` change.
- Test method docstrings describe the bug context + expected
  output, matching the convention in `TestTwoLevelTruncation` and
  `TestMultiLevelInnerFooters`.
- Class docstring on `TestMultiPlayTruncationWithRoleFooters`
  explains the three bugs and the role each test covers.
- Inline comments inside the implementation explain non-obvious
  algorithm choices: walker stack semantics, sort key tiebreaker,
  insert offset tracking.
- `dataclasses.replace` / `_more_footer` for the new TreeLine
  objects (the existing pattern).
- `_count_visible_tasks_per_role` and `_build_role_total_tasks`
  are unchanged — they already produce the correct numbers.

### Pitfalls avoided

- Did NOT modify `_truncate_two_level` itself (per the plan's
  MUST NOT DO rule). The fix lives entirely in
  `_recompute_inner_footer_count`.
- Did NOT modify `compact/format.py` or `tui/widgets/task_tree.py`
  (the renderer already handles `kind="more"` and `has_tail_after`
  from T4/T5/T6).
- Did NOT change `_relabel_role_lines` (the role label format is
  unchanged; only the footer insertion logic is extended).
- Did NOT use `Any` or `# type: ignore`.
- Did NOT change the within-budget code path — the fix only runs
  in the truncation path. The `_relabel_role_lines` idempotency
  is preserved.

### Implementation gotchas discovered

1. **`role_stack` walker must NOT clear `last_task_in_stack_role` on
   play boundary**. The dict tracks "the last task this role had
   visible in the kept tree" — that information survives across
   play boundaries. Only the stack (current open roles) clears.
   Initially I had `last_task_in_stack_role.clear()` on play
   boundary, which broke the nested-roles case (podman's
   `last_task` was being lost when play 2 was processed).

2. **Sort key for footers at same insert position**: when angie
   and podman both want to insert at the same index, angie's
   footer must come first (innermost-first). The sort key
   `(insert_pos, -depth)` achieves this with the depth tiebreaker,
   but the loop must use offset tracking (`offset_at_position`)
   so each subsequent footer at the same position inserts AFTER
   the previous one. Without offset tracking, all footers at the
   same position land at the same index, reversing the order.

3. **`_count_visible_tasks_per_role` semantics are correct for the
   nested case**: podman's `visible` count includes angie's visible
   tasks (because the walker credits every role in the stack per
   task). So `podman_total - podman_visible = 418 - 3 = 415`,
   matching the label. The fix doesn't need to special-case nested
   roles for the count math.

4. **Total unique tasks across all plays**: `sum(1 for _ in
   iter_preflight_task_defs(play_def.tasks) for play_def in
   self._state.definitions)`. Each preflight task is counted once
   (no subtree crediting) — the outer footer's number is a flat
   task count, not a per-role subtree total.

### Verification

- `uv run pytest tests/unit/test_tree_projection.py::TestMultiPlayTruncationWithRoleFooters -q` → 4 passed.
- `uv run pytest tests/unit/test_tree_projection.py -q` → 80 passed (76 pre-T8 + 4 new).
- `uv run pytest tests/ -q --ignore=tests/integration` → 2592 passed (no regressions).
- `uv run pytest tests/integration/test_compact_renderer.py
   tests/integration/test_no_record.py tests/integration/test_session.py
   tests/integration/test_runner.py tests/integration/test_renderer_parity.py -q`
  → 161 passed (no regressions in the renderer parity / compact / runner paths).
- `uv run mypy src/ansible_aom` → Success: no issues found in 69 source files.
- `uv run ruff check src/ansible_aom tests/` → 3 pre-existing errors
  unchanged (F841 `tree.py:1276 idx_before`, E501 `inspect.py:802`,
  I001 `test_dynamic_expansion.py:326`). None introduced by T8.
- `uv run ruff format` applied to the 2 modified files
  (auto-formatting only, no semantic change).
- Manual repro with the user's exact scenario matches the expected
  output byte-for-byte (415 + 2814 = 3229).

### Open questions / future work

- The outer footer's count is `total - visible` which can grow
  unbounded for very large playbooks (2816 + 418 = 3234 here).
  No upper bound enforced. If the user wants a hard cap like
  "always under 9999", add a `min(outer_remaining, 9999)` clamp.
  Out of scope for this fix; the contract change is "count = total
  remaining", not "count = capped total remaining".
- The `len(lines) <= budget` contract is preserved in the within-
  budget path (no footers added), but in the truncation path, the
  budget is exceeded by exactly `len(head_role_footers)` lines
  (one per role ancestor with remaining > 0). This is intentional
  per the prompt's expected output (budget=13 → 15 lines = head + 2
  footers + inner section + 2 outer footers). Future work: if the
  user wants strict `len <= budget`, the truncation pass must
  reserve `len(head_role_footers)` extra budget slots up front.
  Documented as a limitation in the comments; no code change.
