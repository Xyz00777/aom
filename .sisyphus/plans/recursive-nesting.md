# Plan: Recursive nesting in the tree view (unlimited depth + nested role sub-branches)

## Problem

User pasted a tree from `aom --tui`:

```
main.yml
├─ play: Deploy Keepalived for Proxmox VIP
│  └─ □ Reset connection to refresh interpreter state after firewalld install
├─ play: Setup rootless Podman for Scrutiny web server
│  └─ role: podman (40 tasks)
│     ├─ □ angie_ssl_terminator : Copy certificates to target user directory
│     ├─ □ angie_ssl_terminator : Mark SSL terminator setup complete
│     ├─ □ angie_ssl_terminator : Copy certificates to target user directory
│     ├─ □ angie_ssl_terminator : Ensure firewalld is running
│     ├─ □ angie_ssl_terminator : Open HTTPS port in firewalld (TCP)
│     ├─ □ angie_ssl_terminator : Open HTTPS port in firewalld (UDP for HTTP/3 QUIC)
│     ├─ □ angie_ssl_terminator : Deploy Angie Sidecar Quadlet (host network)
│     └─ □ angie_ssl_terminator : Deploy Angie Sidecar Quadlet (bridge network)
```

Two complaints:

1. **"Is this a depth limit?"** — No hard limit exists, but the structural model is
   fixed at 4 levels (Playbook → Play → [RoleGroup] → Task → Host). The tree literally
   cannot represent role-in-role nesting.

2. **"`angie_ssl_terminator` is a role too — why is it a flat list, not its own
   sub-branch under `role: podman`?"** — Because the runtime data model
   (`PlayRunState.tasks` is a flat dict) and the projection
   (`_emit_runtime_play` tracks a single `current_role`) only allow ONE level of role
   grouping. The preflight index wins role assignment, so the
   `angie_ssl_terminator : ` runtime prefix is discarded in favour of the
   preflight `podman` mapping.

## Goals

- Tree depth is **structurally unbounded**. A role that `include_role`s another role
  is rendered with the inner role as a sub-branch.
- `angie_ssl_terminator` inside `podman` shows up as a dedicated
  `role: angie_ssl_terminator` branch under `role: podman`.
- All existing tests pass (no regression). New tests prove the new behaviour.

## Approach (data-model-first, TDD)

1. **`core/models.py`** — add `parent_role: str | None` to `TaskRunState`. Add
   `parent: str | None` to `RoleGroupDefinition` so roles can nest.
2. **`core/parser.py:460 group_roles()`** — when scanning a role's children
   (for `include_role` / `import_role` / `include_tasks`), recursively
   group them under a child `RoleGroupDefinition`.
3. **`core/includes.py`** — when populating `_role_cache` for a role that
   contains an `include_role`, record the parent role so runtime can set
   `parent_role` correctly.
4. **`core/tree.py`** — replace hardcoded `depth=1/2/3` constants in
   `_emit_runtime_play`, `_emit_pending_play`, and the host-leaves block
   with a computed `parent_depth + 1` approach. Track `current_role_path`
   (a list, not a single string) so role headers open/close correctly at
   every depth.
5. **`tui/widgets/task_tree.py:184-188`** — replace the "one level deeper
   for role children" hardcoded walk with a recursive walk.
6. **Tests** — add unit tests asserting:
   - depth-5 nesting renders with correct depth
   - `angie_ssl_terminator` tasks appear under their own
     `role: angie_ssl_terminator` sub-branch
   - mixed consecutive / interleaved roles still work
7. **Fixtures** — add `.sisyphus/test-fixtures/with_nested_role.yml` (a
   real-playbook integration fixture for the new tree shape).
8. **Spec amendments** — `SPECIFICATION.md:1892-1898` and
   `TEST_SPECIFICATION.md:3035` (TC-324) to make recursive nesting
   explicit.

## Non-goals

- Changing the 5-task grouping threshold (still 5+).
- Changing the budget/pruning algorithm in `_compute_tree_budget` /
  `tree_lines` — the spec's height budget is still the screen-space
  constraint, not a depth cap.
- Performance optimisation of the projection — recursive iteration is
  O(n) and n is small.
- TUI widget animations / styling — pure data-shape change.

## TODOs

- [x] T1: Write failing tests proving the current flat-rendering bug
      (regression guard) and asserting the new nested rendering.
- [x] T2: Add `parent_role: str | None` to `TaskRunState` and
      `parent: str | None` to `RoleGroupDefinition` in `core/models.py`.
      Update `iter_preflight_task_defs` to carry a `role_path: tuple[str, ...]`
      instead of a single `inherited_role` so nested roles are iterable.
- [x] T3: Update `core/parser.py:group_roles()` to recurse into role
      children (parse `tasks/main.yml` of nested roles into a child
      `RoleGroupDefinition`).
- [x] T4: Update `core/includes.py` to record the parent role name in
      `RoleCacheEntry` and propagate it to the runtime graft.
      *(2026-06-23: RoleCacheEntry.parent_role added, _find_nested_role_includes
      walks include_role/import_role in tasks/main.yml, _discover_role
      post-pass registers inner roles with parent_role. _runtime_role_from_task_name
      moved to core/models.py as runtime_role_from_task_name to break the
      tree→models import cycle.)*
- [x] T5: Update `core/models.py:RunState._graft_or_match_task` to set
      `parent_role` on the new `TaskRunState` (and on the grafted
      `TaskDefinition`) when the runtime prefix differs from the preflight
      role.
      *(2026-06-23: graft path branches on runtime-vs-preflight role
      difference; new _parent_role_from_cache helper sets TaskRunState.parent_role
      from role_cache in both task_start and runner_on_start handlers.)*
- [ ] T6: Refactor `core/tree.py:_emit_runtime_play` /
      `_emit_pending_play` to track `current_role_path: list[str]` and
      compute depth as `parent_depth + 1`. Update
      `_task_role` to return the full role path, not just the
      innermost role.
- [ ] T7: Update `tui/widgets/task_tree.py` to walk role children
      recursively (replacing the "one level deeper" hardcoded walk).
- [ ] T8: Add `.sisyphus/test-fixtures/with_nested_role.yml` (a minimal
      `include_role` inside a role).
- [ ] T9: Update `SPECIFICATION.md:1892-1898` to specify recursive
      nesting (or remove the hard "Root → Play → RoleGroup → Task → Host"
      cap). Add a sentence: "Role nodes may nest arbitrarily deep; each
      level of nesting adds one tree depth."
- [ ] T10: Update `TEST_SPECIFICATION.md:3035` (TC-324) to define
      "deeply nested roles" concretely: e.g. "play → role A → role B → role C
      (5 tasks) renders all three role branches".
- [ ] F1: Run `uv run pytest tests/ -q`, `uv run mypy src/ansible_aom`,
      `uv run ruff check --fix`. Manual smoke: render an `aom` run on
      the new `with_nested_role.yml` fixture and confirm
      `angie_ssl_terminator` appears as its own sub-branch.
- [ ] F2: Final Verification Wave — code review (review-work), security
      (no new attack surface), performance (recursive iteration is O(n)),
      hands-on QA (run on real playbook).

## Verification (F1)

- `uv run pytest tests/unit/ -q`: all pass (with new tests)
- `uv run pytest tests/ -q`: all pass (no regressions)
- `uv run mypy src/ansible_aom`: Success
- `uv run ruff check src/ tests/`: All checks passed
- Manual: `uv run aom .sisyphus/test-fixtures/with_nested_role.yml`
  renders the inner role as a sub-branch

## Open questions

- Should the role-path be exposed via the CLI / inspect view (e.g.
  `role: podman > angie_ssl_terminator` in the task label)? Defer to
  follow-up — out of scope for this plan.
- Should the role header still say `(40 tasks)` to reflect the total
  subtree, or the direct count? Defer — out of scope. Keep current
  behaviour (total under the role) to preserve spec text on TC-123.

## Status

- **T1: failing tests written** — `tests/unit/test_tree_nested_roles.py`
  added (5 tests). Result on current code: **4 fail, 1 passes**.
  - Passing: `test_regression_flat_role_tasks_unchanged` (regression guard
    for the common single-role case — must keep passing after T2-T7).
  - Failing: `test_nested_role_renders_as_sub_branch`,
    `test_arbitrary_depth_renders_correctly`,
    `test_mixed_consecutive_and_nested_roles`,
    `test_tui_widget_walks_recursively`.
  - Confirmed bug shape: `angie_ssl_terminator : …` tasks flatten under
    `role: podman` at depth=3 instead of forming a `role:
    angie_ssl_terminator` sub-branch at depth=3 with tasks at depth=4.
  - Pre-existing tree tests still pass: `uv run pytest
    tests/unit/test_tree_projection.py
    tests/unit/test_tree_ungrouped_roles.py
    tests/unit/test_tree_classify_and_role_labels.py -q` → 84 passed.
- **T2-T3 complete (2026-06-23):** `core/models.py` carries full role
  paths (`TaskDefinition.parent_role`, `RoleGroupDefinition.parent`,
  `TaskRunState.parent_role`); `iter_preflight_task_defs` now yields
  `(TaskDefinition, tuple[str, ...])`; `role_path_str` helper added;
  `core/parser.py:group_roles()` accepts `parent_role=…` and
  pass-throughs nested `RoleGroupDefinition`. mypy clean; unit suite
  1806 pass, 4 still-fail (expected — projection is T6's work).
- **T4-T5 complete (2026-06-23):** `RoleCacheEntry.parent_role`
  populated by `core/includes.py:_discover_role` after a post-processing
  pass that walks `tasks/main.yml` for `include_role` / `import_role`
  directives. Runtime side reads it via a small
  `_parent_role_from_cache` helper to set `TaskRunState.parent_role`
  on every new task; the dynamic-graft path now branches on
  runtime-vs-preflight role difference to populate
  `TaskDefinition.parent_role` on grafted children. Function
  `_runtime_role_from_task_name` moved from `core/tree.py` to
  `core/models.py` as `runtime_role_from_task_name` (public, next to
  `strip_role_prefix`) to break the `tree→models` import cycle that
  would have arisen from `models.py` importing back. mypy clean; unit
  suite 2529 pass, 4 still-fail with identical messages (expected —
  projection is T6's work).
