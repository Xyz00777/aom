
## 2026-06-25 — Bug A & B fixes applied to src/ansible_aom/core/tree.py

### Bug A: Sibling role accumulation in role_stack

Two functions tracked the "current role chain" by appending every
`kind="role"` line to a stack and only clearing it on `play`/`playbook`.
When a play had multiple sibling roles at the same depth (e.g. `podman`
then `angie_ssl_terminator`), the stack accumulated both — every task
under the second sibling credited both roles, inflating
`role_visible_tasks[role_1]` and pulling `last_task_in_stack_role[role_1]`
forward. Net visible effect: the inner "… and N more tasks" footer for
the first sibling role disappeared (visible_count == total_count makes
the relabel emit `(N tasks)` instead of `(M remaining)`).

Fix shape: parallel depth stack + pop-while `top_depth >= ln.depth`.
The `>=` (not `>`) is intentional — same-depth roles are siblings, not
children, so the previous sibling must close out before the new one
opens. Used in both `_count_visible_tasks_per_role` (separate name +
depth lists) and `_recompute_inner_footer_count` (list of `(depth,
name)` tuples).

### Bug B: Footer count included non-task structural lines

`_count_domain_entities` returned
`sum(1 for ln in lines if ln.kind in ("play", "role", "task"))` but
the footer label reads `"… and N more tasks"`. Plays and roles in the
hidden tail inflated the count. Changed to count only `kind == "task"`.
Also updated the `_more_footer` docstring so the contract on `count`
matches the new behavior.

### Verification
- `uv run pytest tests/ -q` → **2957 passed, 6 skipped, 1 xfailed** (225.5s)
- `uv run mypy src/ansible_aom/core/tree.py` → clean
- `uv run ruff format --check src/ansible_aom/core/tree.py` → clean
- `uv run ruff check` on the file surfaces one pre-existing F841 at
  line 1282 (`idx_before` unused) in `_tree_lines_unbounded` — outside
  the three-function scope of this fix, intentionally left alone.

### Pattern to remember
Whenever a tree-walking algorithm needs an "ancestor chain" keyed by
node kind, pair it with a depth stack and pop-while-`>=`. The `>=` is
the sibling-pop semantic; `>` alone would still leak sibling credit
into the new role's subtree.

### Bug C: Parent-stub double counting in tree.py preflight passes (2026-06-25)

`iter_preflight_task_defs` yields both parent `include_tasks` stubs and
their children. When counting "leaf tasks", callers must skip entries
where `entry.children` is non-empty. This was fixed in
`_count_tasks` (compact/format.py) in Round 2 but two more sites in
tree.py still double-counted.

**Site 1**: `_build_role_total_tasks` preflight pass (line ~790). The
old loop unconditionally credited each yielded task to every role in
its role path. After fix: `if entry.children: continue` skips parent
stubs. Effect: a role that has both a parent stub (`include_tasks`)
and a sibling leaf task now counts only the leaf, not both. This
changes e.g. `theforeman.operations.installer (3 tasks)` →
`(2 tasks)` in the fixture where `install_parent` had 1 dynamic child.

**Site 2**: `_recompute_inner_footer_count` outer footer's
`total_unique_tasks` (line ~1091). The old expression counted every
yielded entry. After fix: `if not tdef.children` filters out stubs.
Effect: the outer footer count matches the visible/inner math
correctly when the tree is truncated, because the inner footer counts
via `_build_role_total_tasks` and the outer footer must agree.

**Why not touch `iter_preflight_task_defs`**: other callers in tree.py
need parent stubs (e.g. `_emit_runtime_play`, `_iter_preflight_task_defs`
output for name-set building at line 800). Changing the iterator would
break those callers. The skip rule belongs at the counting sites.

**Test impact**: only one test was affected by the change —
`tests/unit/test_tree_projection.py::TestTreeLinesGroupedRoleNestedChildren::test_grouped_role_children_are_indexed_emitted_and_keep_previous_play_hidden`.
The role label assertion `(3 tasks)` → `(2 tasks)` because the
fixture's `install_parent` (1 dynamic child) is now correctly skipped.
`count_leaf_tasks` from models.py still returns 4 (it counts
`_iter_task_def_tree` which yields both parent and children); only the
role-label projection narrowed.

**Flaky test observation**: `tests/compact/test_per_task_timing.py::TestPreviousTaskSummary::test_summary_drops_duration_for_single_host_task`
flaked once in the full-suite run but passed in isolation and on retry.
Pre-existing timing-sensitive test, unrelated to this fix.


## 2026-06-25 — TUI tree-view projection-based refresh (Bug D)

### Bug: `apply_state_icons` never removes completed task nodes

The TUI's `TaskTree` widget used `populate_from_definitions` (first call)
followed by `apply_state_icons` (every call), which mutated node labels
in place but never removed nodes. Completed tasks stayed in the tree
forever — the T6 plan intended `populate_from_projection` to replace
this path but the wiring was never landed.

### Fix: Projection-based rebuild in `MainScreen.update_from_state`

Replaced the two-branch block:

```python
if run_state.definitions and not list(tree.root.children):
    tree.populate_from_definitions(run_state.definitions)
if run_state.plays:
    tree.apply_state_icons(run_state)
```

With:

```python
if self._projection is None or self._projection._state is not run_state:
    self._projection = TreeProjection.from_run_state(run_state)
raw_height = tree.size.height
budget = max(8, min(60, raw_height if raw_height > 0 else 20))
if self._projection.is_tree_visible():
    tree.populate_from_projection(self._projection, budget=budget)
elif run_state.definitions:
    tree.populate_from_definitions(run_state.definitions)
```

Key design decisions:
- **Projection caching**: mirrors `compact/renderer.py:620-621` —
  create once, reuse when `RunState` pointer matches, recreate on change.
- **Budget derivation**: `tree.size.height` with fallback to 20 (unmounted
  widget), clamped to `[8, 60]` matching `_compute_tree_budget`.
- **Fallback to definitions**: when `is_tree_visible()` is False (no
  tasks in any play, e.g. preflight-only state), fall back to
  `populate_from_definitions` so the skeleton is visible before any
  play starts.
- **Trade-off**: full rebuild loses expand/collapse state every tick.
  Accepted per T6 plan ("the TUI tree is short-lived per render").

### Tests updated

- `test_update_from_state_drops_completed_tasks` — PASSES (was failing)
- `test_update_from_state_keeps_running_task_visible` — PASSES (was failing)
- `TestEndToEndThreeTasks::test_three_task_starts_appear_in_tree` — updated
  assertion from `len == 3` to `len == 1`. Under linear strategy, each
  `v2_playbook_on_task_start` auto-completes the previous RUNNING task,
  so after 3 starts only the last (Task 2) remains RUNNING. The projection
  correctly drops the two completed tasks.
- `TestPeriodicRefresh::test_tick_refreshes_widgets_after_event` — already
  PASSES with the `is_tree_visible()` guard (definitions-only state falls
  back to `populate_from_definitions`).

### Verification
- `uv run pytest tests/ -q` → **2959 passed, 6 skipped, 1 xfailed**
- `uv run mypy src/ansible_aom/tui/` → clean
- `uv run ruff format` and `uv run ruff check` → clean

## 2026-06-25 — Regression fix: post-completion icons reset to PENDING

### Bug: `populate_from_definitions` in the else branch reset icons to PENDING

The previous fix (Bug D) switched `update_from_state` to use
`populate_from_projection` when `is_tree_visible()` is True and
`populate_from_definitions` as fallback. After `end_time` is set,
`is_tree_visible()` returns False, so the else branch ran
`populate_from_definitions` which calls `root.remove_children()` and
rebuilds from scratch — all icons reset to PENDING (□), losing the
final completion state.

The original code before Bug D used two steps: `populate_from_definitions`
once (first call, when tree is empty) and `apply_state_icons` every call
(to mutate labels in place). The Bug D fix replaced both with projection
but dropped the `apply_state_icons` path entirely.

### Fix: hybrid two-mode refresh

```python
if self._projection.is_tree_visible():
    tree.populate_from_projection(self._projection, budget=budget)
else:
    if run_state.definitions and not list(tree.root.children):
        tree.populate_from_definitions(run_state.definitions)
    if run_state.plays:
        tree.apply_state_icons(run_state)
```

- **During run** (`is_tree_visible()` True): projection-based rebuild
  drops completed tasks, shows only running/pending.
- **Before run or after completion** (`is_tree_visible()` False):
  original two-step — skeleton once, icons mutated every call. This
  preserves `●` (OK), `✖` (FAILED), etc. after the playbook finishes.

### Test added

`TestMainScreenTreeIntegration::test_update_from_state_shows_ok_icon_after_completion`
— drives a state with `end_time` set and a task in `Status.OK`, asserts
the tree's task label contains `●` (not `□`).

### Verification
- `uv run pytest tests/ -q` → **2960 passed, 6 skipped, 1 xfailed**
- `uv run mypy src/ansible_aom/tui/` → clean
- `uv run ruff format` and `uv run ruff check` → clean
