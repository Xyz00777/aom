# Recursive Nesting — Investigation Notes

## Date: 2026-06-23

## User's report
Tree view in TUI shows `angie_ssl_terminator` tasks as a flat list under
`role: podman` instead of a dedicated sub-branch.

## Root cause
1. `core/models.py:167` — `PlayRunState.tasks` is a flat `dict[str, TaskRunState]`.
   No `RoleRunState` / nested role container at runtime.
2. `core/tree.py:1144 _task_role` — uses single-string role assignment.
   Preflight index wins → runtime `angie_ssl_terminator : ` prefix is
   discarded.
3. `core/tree.py:794-861` — `_emit_runtime_play` tracks a single
   `current_role` and emits a new role header only on role change.
4. `core/parser.py:460 group_roles` — only groups one level (consecutive
   same-role tasks in a play). Doesn't recurse into role
   `tasks/main.yml`.
5. `tui/widgets/task_tree.py:184-188` — hardcoded "one level deeper for
   role children". Doesn't recurse for nested roles.

## What the user wants
- Tree depth **structurally unbounded** (no fixed 4-level cap).
- `angie_ssl_terminator` shown as a dedicated `role: angie_ssl_terminator`
  sub-branch under `role: podman`.

## Spec gaps
- `SPECIFICATION.md:1892-1898` hard-caps at
  `Root → Play → [RoleGroup] → Task → Host` (4 levels).
- `TEST_SPECIFICATION.md:3035 TC-324` mentions "Deeply nested roles" as
  an edge case but defines nothing.
- `compact/format.py:317 _compute_tree_budget` is a line-count budget,
  not a depth cap.

## Plan file
`.sisyphus/plans/recursive-nesting.md`

## [2026-06-23] T1: failing tests written

Created `tests/unit/test_tree_nested_roles.py` with 5 tests pinning the
recursive-nesting target shape. **4 fail, 1 passes** on the current
code — proving the bug without false positives.

| Test | Status now | Purpose |
|------|-----------|---------|
| `TestNestedRoleRendersAsSubBranch::test_nested_role_renders_as_sub_branch` | FAIL | User-reported bug: `angie_ssl_terminator` tasks flatten under `role: podman` instead of forming a dedicated sub-branch. |
| `TestArbitraryDepthRendersCorrectly::test_arbitrary_depth_renders_correctly` | FAIL | 5-level deep nesting collapses at the 4-level cap; only role headers at depth 2/3/4/5 and a task at depth=6 will pass. |
| `TestFlatRoleTasksUnchanged::test_regression_flat_role_tasks_unchanged` | PASS | Single non-nested role keeps `depth=2/3/4` layout — regression guard, must keep passing after T2-T7. |
| `TestMixedConsecutiveAndNestedRoles::test_mixed_consecutive_and_nested_roles` | FAIL | Mixed `podman → angie_ssl_terminator (8) → podman-native (2) → helper (3)` must open two sub-branches at consistent depths. |
| `TestTuiWidgetWalksRecursively::test_tui_widget_walks_recursively` | FAIL | `TaskTree.apply_state_icons` only walks one level into role nodes (`task_tree.py:184-188`); nested task nodes never get status updates. |

### Test design notes

- **Drive only the public API**: `TreeProjection.from_run_state(state).tree_lines(budget=N)`.
  No peeking at `_emit_runtime_play`, `_task_role`, or any internals the
  T2-T7 fix will rename/replace.
- **Self-contained state**: each test builds its own `RunState` inline
  (matches `test_tree_projection.py`, `test_tree_ungrouped_roles.py`,
  `test_tree_classify_and_role_labels.py` style — no shared fixtures).
- **Helper functions** (`_play_def`, `_fire_startup`, `_fire_running_task`,
  `_fire_pending_task`, `_line_summary`) eliminate per-test boilerplate
  without abstracting over state-shape knowledge.
- **Free-strategy fixtures**: prefer `v2_runner_on_start` over
  `v2_playbook_on_task_start + v2_runner_on_start` chains where the
  test doesn't care about strategy detection, mirroring the established
  pattern in `TestTreeLinesRolesAndFanOut`.

### Confirmed bug shape (current code)

```
depth=0  playbook  main.yml
depth=1  play      play: Setup rootless Podman …
depth=2  role      role: podman (5 tasks)         ← only ONE role header
depth=3  task      angie_ssl_terminator : Copy …  ← flattened
depth=4  host      web1
depth=3  task      angie_ssl_terminator : Mark …
...
```

The fix must produce a `role: angie_ssl_terminator (M tasks)` line
at `depth=3` between the podman header and its child tasks.

### Verified pre-existing tests still pass

`uv run pytest tests/unit/test_tree_projection.py tests/unit/test_tree_ungrouped_roles.py tests/unit/test_tree_classify_and_role_labels.py -q`
→ 84 passed in 0.71s. No regression introduced by the new test file.

## [2026-06-23] T2-T3: data model + parser

Completed the data-model-first phase. The data shape now carries full
role paths and parent-role info end-to-end; the projection logic in
T6 can consume it.

### T2 — `core/models.py` changes

1. **`TaskDefinition.parent_role: str | None = None`** — carries the
   enclosing role's name on the definition itself. T5 sets this on
   dynamically grafted tasks.
2. **`RoleGroupDefinition.parent: str | None = None`** and the
   `tasks` field is now `list[TaskDefinition | "RoleGroupDefinition"]`
   (was `list[TaskDefinition]`) so a role group can contain nested
   role groups. T6 walks the nested structure to emit sub-branch
   headers at the right depth.
3. **`TaskRunState.parent_role: str | None = None`** — runtime
   counterpart. T5 sets it when the ``"role : "`` prefix on a
   task name differs from the preflight role assignment.
4. **`iter_preflight_task_defs` signature change**:
   - Old: `iter_preflight_task_defs(entries, inherited_role: str | None = None)`
     yielding `(TaskDefinition, str | None)`.
   - New: `iter_preflight_task_defs(entries, inherited_role_path: tuple[str, ...] = ())`
     yielding `(TaskDefinition, tuple[str, ...])`.
   - Empty tuple means "no role active" (task directly under a play).
   - For an `angie_ssl_terminator` task inside `podman`, the second
     element is `("podman", "angie_ssl_terminator")`.
5. **`role_path_str(role_path) -> str`** helper added — `" > ".join`
   on the path. Returns `""` for empty.

### T2 — call-site updates in `core/tree.py`

Three call sites in `TreeProjection`:
- `_emit_pending_play` (lines 734, 737) — both loops now use
  `role_path[-1] if role_path else None` to take the innermost role
  for the single-string display.
- `_emit_runtime_play` (lines 802, 809) — same pattern; innermost
  for the role counter, ignore role path for the "emitted preflight
  names" set.
- `_task_role` (line 1162) — innermost for the role index, since
  `_task_role` still returns `str | None` (T6's job to widen).

### T3 — `core/parser.py:group_roles` changes

1. New `parent_role: str | None = None` parameter (default `None`).
2. Every `RoleGroupDefinition` produced gets `parent=parent_role`.
3. **Pass-through for nested `RoleGroupDefinition`**: when iterating
   the input list, an already-grouped child role (i.e. a
   `RoleGroupDefinition` instance) is appended directly to the
   result, with any in-progress group flushed first. Its existing
   `parent` is preserved (set when it was built by an outer
   `group_roles` call).
4. The 5-task threshold is unchanged.

### Knock-on fix — `compact/format.py:collect_tags`

`RoleGroupDefinition.tasks` is now `list[TaskDefinition | RoleGroupDefinition]`,
so the existing `for task in entry.tasks: seen.update(task.tags)`
stopped type-checking (`RoleGroupDefinition` has no `.tags`). Refactored
into a small `_collect_role_group_tags` helper that recurses into nested
role groups. This is required for mypy strict on `core/`, and is
correctness-positive — without it, tags on tasks inside a role-in-role
would have been silently dropped at the call site.

### Knock-on fix — `core/models.py:_iter_leaf_task_defs`

Same issue: previously assumed `entry.tasks` was
`list[TaskDefinition]`. Refactored to a `_leaves_of_role_group` helper
that recurses through nested role groups. Used by `count_leaf_tasks`
and the run-quality `preflight_task_count` persisted to `meta.json`.

### Verification

- `uv run mypy src/ansible_aom` → **Success: no issues found in 69 source files**.
- `uv run pytest tests/unit/test_tree_nested_roles.py
   tests/unit/test_tree_projection.py
   tests/unit/test_tree_ungrouped_roles.py
   tests/unit/test_tree_classify_and_role_labels.py -q` →
  **4 failed, 85 passed** (the 4 expected failures are the
  projection-side tests; the 1 regression test `test_regression_flat_role_tasks_unchanged`
  in the new file still passes).
- `uv run pytest tests/unit/ -q` → **4 failed, 1806 passed**.
- `uv run pytest tests/compact/ tests/tui/test_tree_view.py -q` → **477 passed**.
- `uv run pytest tests/unit/test_models.py tests/unit/test_parser.py
   tests/compact/test_preflight_summary.py -q` → **260 passed**.
- `uv run ruff format` → 2 files reformatted (the 2 files I edited).
- `uv run ruff check` → 2 pre-existing errors on lines I did not
  touch (`core/tree.py:712` unused `idx_before`, `tui/screens/inspect.py:802`
  line too long). Not introduced by this work.

### Notes for T6 (projection refactor)

- `_task_role` still returns `str | None`. It now keys on
  `role_path[-1]` — the innermost role. When T6 widens it to return
  the full path, the 3 call sites that currently use the result
  (role counts, role counters, runtime role derivation) will need
  updating to consume the tuple.
- `RoleGroupDefinition.tasks` is now `list[TaskDefinition | RoleGroupDefinition]`.
  Any consumer that iterates over it expecting only `TaskDefinition`
  must either narrow via `isinstance` or call the new
  `_leaves_of_role_group` / `_collect_role_group_tags` helpers. Found
  in this pass: `compact/format.py:collect_tags`. Other candidates
  for a quick scan in T6: `compact/format.py:_count_tasks`,
  `tests/tui/test_tree_view.py`.
- The pass-through in `group_roles` means the *outer* call never
  inspects the nested `RoleGroupDefinition`'s children. If T4 (includes
  discovery) ever needs the outer `group_roles` to *recurse* into a
  nested role's children, it would have to opt out of the pass-through
  by detecting already-nested structure — flag this if it comes up.

## [2026-06-23 21:03 UTC] T4-T5: includes + graft

Completed the data-source phase. `RoleCacheEntry` now carries
`parent_role`, the runtime side reads it to populate
`TaskRunState.parent_role`, and the dynamic-graft path propagates
`parent_role` onto freshly-created `TaskDefinition` instances. T6 (the
projection refactor) now has everything it needs to render the
sub-branch without needing further data-model changes.

### T4 — `core/includes.py` + `core/models.py`

1. **`RoleCacheEntry.parent_role: str | None = None`** — informational
   only. `None` means "top-level role included from a play"; non-`None`
   is the enclosing role's name (e.g. `"podman"` for
   `angie_ssl_terminator` discovered inside `podman`'s tasks). The
   default keeps every existing call site working without changes
   (verified: `test_include_cache.py:607` constructs with two args,
   still passes).
2. **New helper `_find_nested_role_includes(role_dir) -> list[str]`**
   that walks a role's `tasks/main.yml` and returns names of any
   `include_role:` / `import_role:` inner roles. Accepts three YAML
   forms ansible uses:
   - bare string (`include_role: foo`)
   - kwargs string (`include_role: name=foo` or `name: foo`)
   - mapping (`include_role:\n  name: foo`)
   Jinja-templated values are skipped — they can't be resolved at
   preflight.
3. **`_discover_role` post-processing pass** — after caching the role's
   own tasks, walks the same `tasks/main.yml` for `include_role` /
   `import_role` and registers each inner role with
   `parent_role=<this role>`. Inner cache keys are still the inner
   role's name (lowercased+stripped, matches the existing
   normalisation) so the same role included from multiple parents
   dedupes. First parent to register wins — the field is informational,
   not load-bearing for any decision.
4. **Import cycle avoided** — moved `_runtime_role_from_task_name` from
   `core/tree.py` to `core/models.py` as `runtime_role_from_task_name`
   (now public, lives next to `strip_role_prefix`). `tree.py` imports
   it. No `# type: ignore` needed.

### T5 — `core/models.py:RunState` graft + runtime paths

1. **`_graft_or_match_task`** — the dynamic graft path now branches on
   whether the runtime prefix role differs from the preflight parent's
   role:
   - If yes: grafted task is from a nested `include_role`. Role is set
     to the inner role (e.g. `angie_ssl_terminator`), `parent_role`
     is the outer role (e.g. `podman`).
   - If no (plain `include_tasks` or matching role): role inherits
     `parent.role`, `parent_role` propagates `parent.parent_role` so
     existing chains survive.
2. **`_handle_v2_playbook_on_task_start` / `_handle_v2_runner_on_start`**
   — new `TaskRunState` instances now set `parent_role` via a small
   `_parent_role_from_cache` helper. The helper reads
   `runtime_role_from_task_name(task_name)`, looks it up in
   `state._role_cache` (lowercased+stripped), and returns the cached
   `parent_role` (or `None` if absent). This is the runtime-side
   counterpart to T4: the cache is the runtime source of truth for
   nested-role relationships.
3. **mypy type-narrowing note** — the graft role/parent_role branch
   required explicit type annotations
   (`graft_role: str | None; graft_parent_role: str | None`) for
   mypy strict to accept the union. Without the annotations, mypy
   infers `str | None` per-branch and then rejects the second
   assignment because the variable appears to be `str`. Easy to miss
   in a non-strict project — flag for future me.

### Verification

- `uv run mypy src/ansible_aom` → **Success: no issues found in 69
  source files**.
- `uv run pytest tests/unit/test_tree_nested_roles.py -q` → **4
  failed, 1 passed** (the 4 still-fail are the expected projection
  failures; the 1 regression test `test_regression_flat_role_tasks_unchanged`
  still passes). Failure messages are unchanged from the T2-T3
  baseline — the data-side fix is correct, projection-side is T6.
- `uv run pytest tests/unit/ tests/compact/ tests/tui/ -q` →
  **4 failed, 2529 passed in 57.92s**. No regressions.
- `uv run ruff check src/` → 2 pre-existing errors
  (`core/tree.py:712 idx_before` unused, `tui/screens/inspect.py:802`
  line too long). Not introduced by this work. The three files I
  edited (`core/models.py`, `core/includes.py`, `core/tree.py` from
  my edits) are clean except for the pre-existing `idx_before`
  warning at line 698.
- `uv run ruff format --check` on changed files → all formatted.

### Notes for T6 (projection refactor)

- **Both graft and runtime paths now populate `parent_role`.** T6 can
  consume `task_run_state.parent_role` to decide whether to render a
  sub-branch. The projection's role-emission loop needs to look at
  this field instead of relying on the preflight index alone.
- **`_task_role` is still the single-string path.** It returns
  `role_path[-1]` (innermost) for preflight and falls back to the
  runtime prefix for unmatched tasks. T6 widens it to return the full
  role path or change the projection loop to walk `parent_role`
  directly.
- **`_find_nested_role_includes` does not recurse.** A role A that
  includes B that includes C will register B under A, then a separate
  discovery of B (if B is ever directly included) would register C
  under B. But C will NOT be transitively discovered from A alone.
  This matches the existing `parse_role_tasks` single-pass behaviour
  — fine for now, flag for a future pass if real playbooks show
  deeper nesting.
- **The runtime cache key normalisation is the source of truth.** Both
  `_discover_role` (storage) and `_parent_role_from_cache` (lookup)
  lowercase + strip before keying. If you ever change one, change the
  other.
- **Test for the new behaviour already exists (and fails correctly).**
  `tests/unit/test_tree_nested_roles.py` has 4 tests that prove the
  bug; they'll start passing once T6's projection uses the data this
  task populated.

### Design note: import_role

`_find_nested_role_includes` matches both `include_role` and
`import_role`. `import_role` is fully expanded at preflight (so it
should already appear in `parse_list_tasks_output` with a proper role
mapping), but if it ever appears at runtime (e.g. dynamic vars), we
want to discover it the same way. Belt-and-braces; costs nothing.

## [2026-06-24] NEW BUG: `_emit_pending_play` emits duplicate role headers

### Reported by user
After the previous fix (aggressive collapse applied as final pass in
`_extend_role_path`), a different duplicate role header bug remains. The
play has `RoleGroupDefinition(role="angie_ssl_terminator")` and emits
two stacked `role: angie_ssl_terminator` headers with mismatched
children.

### Root cause
`_emit_pending_play` (`src/ansible_aom/core/tree.py:756-829`) iterates
`iter_preflight_task_defs` directly and uses the raw `role_path` to
emit role headers (lines 790-817). It does NOT call `_extend_role_path`
or apply `_collapse_role_path_aggressive` to the preflight paths.

When a `TaskDefinition` inside a `RoleGroupDefinition` has the SAME
role as the enclosing group, `iter_preflight_task_defs` yields a
length-2 path with both elements equal to the role name (e.g.
`("angie_ssl_terminator", "angie_ssl_terminator")`). The renderer
walks this path element-by-element and emits two role headers.

The runtime path (`_emit_runtime_play`) is unaffected because it
constructs `play_items` via `_extend_role_path` which applies the
aggressive collapse as the final pass, dropping the duplicate.

### Reproduction (synthetic, matches user output verbatim)
```python
state = RunState(playbook="site.yml")
state.definitions = [
    PlayDefinition(
        id="p1", name="Deploy Keepalived for Proxmox VIP",
        hosts="all", resolved_hosts=["web1"],
        tasks=[
            RoleGroupDefinition(
                role="angie_ssl_terminator",
                tasks=[
                    TaskDefinition(name="Set sidecar user config",
                                   role="angie_ssl_terminator", ...),
                    TaskDefinition(name="Include setup tasks (...)",
                                   role="angie_ssl_terminator", ...),
                ],
            ),
            TaskDefinition(name="Deploy TLS certificates for sidecar",
                           role=None, ...),
            TaskDefinition(name="Get the user ID for {{ ... }}",
                           role=None, ...),
            TaskDefinition(name="Reload systemd daemon for user",
                           role=None, ...),
            TaskDefinition(name="Enable and start angie-sidecar service",
                           role=None, ...),
            TaskDefinition(name="Include add_site tasks",
                           role=None, ...),
        ],
    )
]
```

Output:
```
play: Deploy Keepalived for Proxmox VIP  (depth=1)
  role: angie_ssl_terminator (2 tasks)  (depth=2)
    role: angie_ssl_terminator (2 tasks)  (depth=3)  ← DUPLICATE
      Set sidecar user config  (depth=4)
      Include setup tasks (...)  (depth=4)
  Deploy TLS certificates for sidecar  (depth=2)
  Get the user ID for {{ ... }}  (depth=2)
  Reload systemd daemon for user  (depth=2)
  Enable and start angie-sidecar service  (depth=2)
  Include add_site tasks  (depth=2)
```

### Exact file:line
`src/ansible_aom/core/tree.py:790-817` — the `_emit_pending_play`
role-emission loop. The preflight paths are read straight from
`iter_preflight_task_defs` without any collapse.

### Proposed fix approach
Apply `_collapse_role_path_aggressive` (or at least the consecutive
`_collapse_role_path`) to `role_path` in the `_emit_pending_play` loop
BEFORE the `role_path_list != current_role_path` check. The simplest
patch: replace `for tdef, role_path in iter_preflight_task_defs(...)`
with a loop that does
`role_path = _collapse_role_path_aggressive(role_path)` (or wrap the
iterator with `((tdef, _collapse_role_path_aggressive(rp)) for tdef, rp in iter_preflight_task_defs(...))`).

Even better: have `iter_preflight_task_defs` yield collapsed paths so
both `_emit_pending_play` and any future caller benefit, and so the
contract becomes "the second element is always a normalised role path".
