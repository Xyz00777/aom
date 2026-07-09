## 2026-06-28 — Drop (M remaining) suffix from role labels

### Bug
`role: X (M remaining)` count was computed as `total - visible` in
`_relabel_role_lines` (src/ansible_aom/core/tree_projection.py:754).
Visible = running + pending tasks; completed tasks are dropped from the
tree. So the formula reduced to:

    remaining = total - visible
              = (completed + running + pending) - (running + pending)
              = completed

As tasks completed, "remaining" went **up** instead of down. Reproduced
with 5 tasks, completed_count 0..4 → label progressed
"(4 tasks remaining)" → "(5 tasks remaining)" → "(6 tasks remaining)" →
"(7 tasks remaining)".

The T3 plan (two-level-truncation.md, lines 173-208) defined the math
this way on purpose: the suffix was meant to mirror the inner footer's
"… and N more tasks" count when truncation dropped part of a role's
task list. That's correct in the truncated case. But the same suffix
also appeared in the NON-truncated case, where `visible < total` only
because some tasks had completed — i.e. the suffix displayed "completed
count" with no truncation context. Confusing and wrong.

### Decision (user 2026-06-28)
Drop the `(M remaining)` suffix from role labels entirely. The
`… and N more tasks` inner/outer footers already serve the "hidden work"
purpose in the truncated case. Role labels become a stable `(N tasks)`
total — never changes as the run progresses.

### Fix shape (chosen: Option 1 — surgical, not a gut)
Collapse `_relabel_role_lines` so the `(M remaining)` branch is gone.
Always emit `(N tasks)` (or no count when total is 0). Keep the
post-truncation pass structure intact so future emission changes don't
have to re-introduce it. Don't delete `_build_role_total_tasks` /
`_count_visible_tasks_per_role` — they're still called by
`_recompute_inner_footer_count` for the footers.

### Affected tests
- `tests/unit/test_tree_classify_and_role_labels.py` (lines 198-249)
  → flip `(M remaining)` assertions to `(N tasks)`
- `tests/unit/test_runtime_role_task_count.py` (lines 127-143, 281-327)
  → same
- `tests/unit/test_tree_projection.py` (lines 2100-2257, 2506-2602,
  3549-3600) → assertions on role label `(M tasks remaining)` change to
  `(N tasks)`; the cross-check "role label = inner footer count" goes
  away (was the only contract that tied the two together)

### Verification target
- `uv run pytest tests/ -q` → all green (current 2960 passed baseline)
- `uv run mypy src/ansible_aom/core/tree_projection.py` → clean
- `uv run ruff format && uv run ruff check --fix` → clean

### Things explicitly NOT in scope
- `_more_footer` and the `… and N more tasks` inner/outer footers stay
- The `kind="more"` rendering in `compact/format.py` and
  `tui/widgets/task_tree.py` stays
- Spec doc updates: only update if there's a user-facing sentence about
  the role label suffix
## 2026-06-28 — TDD done

### New regression test (written first, watched fail)
Added `TestRuntimeRoleLabelTaskCountFromDefinitions::test_role_label_count_is_stable_as_tasks_complete`
in `tests/unit/test_tree_classify_and_role_labels.py`. Before the fix it
failed with:
> AssertionError: role label must show total count '(2 tasks)' after 1
> completion; got 'role: webserver (1 task remaining)'
which exactly reproduces the user-reported bug. After the fix it passes.

### Test count delta
- Baseline (full suite, before fix): 2877 passed + 4 pre-existing flakies
  that varied between runs.
- After fix: 2881 passed, 6 skipped. The +4 delta breaks down as:
  - +1 new regression test (`test_role_label_count_is_stable_as_tasks_complete`)
  - −1 removed cross-check test (`test_inner_footer_count_matches_role_label_remaining`)
  - +4 pre-existing flakies that happened to pass on the after-fix run
- Net change in test count: +0. Net change in test names: 1 new, 1 deleted.

### Touched test files
- `tests/unit/test_tree_classify_and_role_labels.py` — flipped
  `test_role_label_shows_total_task_count_not_running_count` to assert
  `(2 tasks)` and added the regression test
  `test_role_label_count_is_stable_as_tasks_complete` (negative assertion
  on `"remaining"` substring too).
- `tests/unit/test_runtime_role_task_count.py` — flipped
  `test_dynamic_role_shows_task_count_in_label` and
  `test_dynamic_role_with_no_preflight_shows_runtime_count`.
- `tests/unit/test_tree_projection.py` — flipped three tests in
  `TestRoleLabelsAfterTruncation`:
  - `test_role_label_shows_total_when_inside_cut` (renamed from
    `test_role_label_shows_remaining_when_inside`),
  - `test_role_label_shows_total_when_all_tasks_visible_after_cut`
    (negative-assertion on "remaining" added),
  - `test_role_label_singular_plural_format` (renamed from
    `test_role_label_remaining_format`).
  - Flipped `test_inner_count_uses_role_remaining_count` and
    `test_inner_footer_does_not_count_upcoming_plays_tasks` to assert
    the (N tasks) form on the role label.
  - **Deleted** `test_inner_footer_count_matches_role_label_remaining`
    (the cross-check that tied the role label and footer together via
    the (M remaining) suffix).
  - Flipped `test_role_label_subtree_total_when_cut_inside_nested`
    (renamed from `..._remaining_...`).
- `tests/tui/test_tree_more_footers.py` — flipped
  `test_tui_role_label_carries_total_in_textual_tree` (renamed from
  `..._remaining_...`), now asserts the role label carries `(N tasks)`
  and does NOT contain "remaining".
- `tests/compact/test_tree_render.py` — flipped the assertion in the
  two-level truncation test from "must contain 'remaining'" to "must
  NOT contain 'remaining'" + "must contain '(33 tasks)'".

### Surprise cross-effects
None in `compact/format.py` or `tui/widgets/task_tree.py` — both files
just render `label` as-is, no substring matching on "(M remaining)".
The TUI widget docstring at `task_tree.py:233,242` still references the
old contract, but per scope (don't touch that file) it stays as
historical context.

Also updated three docstrings inside `src/ansible_aom/core/tree_projection.py`
to reflect the new contract:
- `_relabel_role_lines` — full rewrite describing the new shape and
  explaining why the (M remaining) variant was dropped.
- `_recompute_inner_footer_count` — removed "(M tasks remaining)"
  cross-references; clarified the inner/outer footer counts are the
  source of truth for hidden work.
- `tree_lines` (line 1255) — removed the "(N tasks) ↔ (M remaining)"
  framing.
- `_build_role_total_tasks` (line 833) — removed "misleading
  (N*tasks remaining)" historical reference.

### Final shape of `_relabel_role_lines`

```python
def _relabel_role_lines(self, lines: list[TreeLine]) -> list[TreeLine]:
    play_names = self._visible_play_names(lines)
    role_total_tasks = self._build_role_total_tasks(play_names=play_names)
    _role_visible_tasks = self._count_visible_tasks_per_role(lines)

    result: list[TreeLine] = []
    for ln in lines:
        if ln.kind != "role" or ln.identity is None:
            result.append(ln)
            continue
        r = ln.identity
        total = role_total_tasks.get(r, 0)

        if total == 0:
            new_label = f"role: {r}"
        else:
            plural = "task" if total == 1 else "tasks"
            new_label = f"role: {r} ({total} {plural})"

        result.append(replace(ln, label=new_label))
    return result
```

`_count_visible_tasks_per_role` is still called (kept for the
`_recompute_inner_footer_count` consumer and to preserve the
post-truncation pass structure) but its result is assigned to
`_role_visible_tasks` to mark it as intentionally unused.

### Things that proved useful
- TDD ordering: writing the regression test first made the bug
  reproducible in CI language before touching the production code.
- `_walk_all_nodes` from `tests/tui/test_tree_more_footers.py` is the
  canonical way to walk a Textual Tree and find role nodes — used the
  same pattern in the flipped TUI test.
- The `re` import that wasn't there in `test_tree_render.py` — fell
  back to a literal substring check `(33 tasks)` instead of a regex.
- Plan file (`.sisyphus/plans/two-level-truncation.md`) was NOT
  modified per Work_Context rule (plans are orchestrator-managed,
  read-only for the executor). The spec's request to update T3 was
  overridden by that rule. Tests don't read the plan file so this is
  zero risk.

### Verification matrix (all green)
- `uv run pytest tests/ -q` → **2881 passed, 6 skipped** in ~207s
- `uv run mypy src/ansible_aom/core/tree_projection.py` → clean
- `uv run ruff format --check src/ansible_aom/core/tree_projection.py` → clean
- `uv run ruff check src/ansible_aom/core/tree_projection.py` → clean
- lsp_diagnostics on `src/ansible_aom/core/tree_projection.py` → 0 errors

### Independent hands-on QA (orchestrator)
Re-ran the original bug repro from the diagnostic session against the
fixed code:
- Clean fixture (5 tasks defined, no extras): role label reads
  `(5 tasks)` for done=1..4 and disappears for done=0 or done=5. Stable
  total, no "remaining" suffix anywhere. Bug eliminated.
- Render preview (40-task role, 5 done, 1 running on 2 hosts):
  - budget=12 (truncated): `role: webserver (40 tasks)` +
    `… and 35 more tasks` inner footer + outer footer. Inner/outer
    footers still carry the hidden-work signal as designed.
  - budget=60 (not truncated): `role: webserver (40 tasks)`,
    no spurious suffix, all 35 pending tasks listed explicitly.

All three gate criteria satisfied:
1. Every changed line is explainable.
2. Saw the fix work with own eyes (bug repros pre-fix, clean post-fix).
3. Nothing existing broken — full suite green, mypy/ruff/lsp clean.
