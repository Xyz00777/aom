# Plan: Static pre-expansion of `include_tasks` (Plan A)

## Problem

User's tree shows role task counts that look right but visible tasks are wrong:

```
main.yml
├─ play: Deploy Keepalived for Proxmox VIP
│  ├─ role: podman (9 tasks)              ← count is correct, only 2 visible
│  │  ├─ ◐ Stop podman socket for user
│  │  ├─ ◐ Install Podman and passt (...)
│  └─ role: angie_ssl_terminator (7 tasks)
│     ├─ □ Deploy TLS certificates for sidecar
│     ├─ □ Get the user ID for {{ ... }}
│     ├─ □ Reload systemd daemon for user
│     ├─ □ Enable and start angie-sidecar service
│     └─ □ Include add_site tasks         ← dangling stub at the bottom
```

Three failure modes:

1. **Static path.** `--list-tasks` does **not** expand `include_tasks`. Ansible only
   expands `import_tasks` statically. So `podman`'s task list shows only its
   literal `tasks/main.yml` tasks; the `include_tasks: site.yml` line surfaces as
   a single stub named `"Include add_site tasks"`.

2. **Runtime graft is wired but pruned.** `_graft_or_match_task()`
   (`core/models.py:626`) is called from the JSONL event handlers and attaches
   included tasks as children of the include stub at runtime. The tree projection
   (`core/tree.py:1331`) drops anything classified as `"completed"`. So children
   briefly appear during execution then vanish as they finish — the user's
   `(9 tasks)` count is correct (it walks `TaskDefinition.children`), but the
   visible list is the running-and-pending subset.

3. **Dead-code mechanisms.** `core/includes.py` (330 lines) already implements:
   - `parse_include_tasks_file()` — YAML → task names
   - `resolve_includes_from_playbook()` — DFS scan of playbook + `block:`/
     `rescue:`/`always:` for `include_tasks:` directives
   - `discover_include_with_runtime_path()` — runtime discovery via
     `task.path` from JSONL (`"file.yml:line_number"`)
   - `_discover_role()` + nested role handling

   …but **nothing calls them from production code**. `run_preflight()`
   (`ansible/preflight.py:159`) ends without invoking
   `resolve_includes_from_playbook()`. `count_total_tasks_seen()`
   (`compact/format.py:713`) reads `state._include_cache.values()` but the cache
   is never populated, so the status bar denominator never benefits.

The result: `podman (9 tasks)` looks accurate only because grafted children are
counted; the user sees a sparse, surprising view; `Include add_site tasks` sits
as a phantom stub with nothing under it.

## Goals

1. **Tree shows every `include_tasks` child before the run starts.** No
   waiting for runtime JSONL to fill it in.
2. **`(N tasks)` and the visible list agree.** Counts and visible items come
   from the same source.
3. **Dangling include stubs disappear.** The `Include X` stub is replaced by
   its resolved children; only the leaves show as task rows.
4. **Role-relative includes resolve correctly.** `include_tasks:` inside
   `roles/<name>/tasks/main.yml` resolves relative to that file, not the
   playbook directory.
5. **Dynamic includes (Jinja paths, loops) still work.** Fall back to
   `discover_include_with_runtime_path()` from the JSONL event handlers, same
   as today.
6. **No regressions.** All existing tests pass. The new behaviour slots into
   TC-094–096 (already in `TEST_SPECIFICATION.md`) plus new TC slots for
   static expansion.
7. **Trust boundary preserved.** AOM stays a monitor; the static parse is
   best-effort and never asserts "this is what ansible will run" — it asserts
   "if ansible's path resolution agrees with ours, here are the candidate
   tasks". Runtime graft remains authoritative for ordering and counts.

## Non-Goals (explicitly out of scope)

- Re-implementing ansible's full include resolution semantics
  (`apply:`, `vars_files:` lookup, `with_first_found`, conditional includes).
  We parse literally what the user wrote; runtime graft fills the gaps.
- Expanding loops (`with_items:`/`loop:`). Loops multiply a task N times at
  runtime; pre-expansion can't know N. The runtime graft will handle them as
  it does today.
- Changing the `--list-tasks` parsing format or adding new ansible flags.
  We work with what `ansible-playbook --list-tasks` emits.

## Approach (TDD-first, surgical)

### Phase 0 — Pin down the data flow (no code change, tests only)

Three integration test playbooks already exist at
`.sisyphus/test-fixtures/`:

- `with_include.yml` — single role with one `include_tasks:` inside
- `with_import.yml` — same shape but `import_tasks` (control case)
- `with_role.yml` — role includes another role (`include_role`)

Add a fourth fixture: `with_nested_include.yml` — role → include_tasks → that
included file contains another `include_tasks:`. Exercises the
`block:`/`rescue:`/`always:` recursion + role-relative path resolution.

**Acceptance:** fixtures run end-to-end against real `ansible-playbook` with
`--list-tasks`; capture stdout into
`tests/integration/fixtures/preflight/with_*.txt` snapshots so the test
asserts AOM's parsing against real output (not synthetic).

### Phase 1 — Add `_graft_include_children()` (pure core function)

**File:** `src/ansible_aom/core/includes.py`

New function (signature only — implement TDD-first):

```python
def graft_include_children(
    *,
    playbook_path: str | Path,
    definitions: list[PlayDefinition],
    cache: dict[str, IncludeCacheEntry],
) -> None:
    """Walk definitions, replace each include_tasks stub with its children.

    For every TaskDefinition whose name matches the literal include_tasks
    pattern ("Include <file>" with no `role : ` prefix), look up the
    resolved path in *cache*. If found, replace the stub with the cached
    task names as children. Jinja-templated include paths are skipped
    (no cache entry to graft from).
    """
```

**Critical detail — path resolution.** The current
`resolve_includes_from_playbook()` resolves include paths relative to the
playbook directory. For role-scoped includes we need role-relative resolution.
Add a parallel scanner:

```python
def _scan_role_tasks_for_includes(
    role_dir: Path,
    cache: dict[str, IncludeCacheEntry],
) -> None:
    """Walk role_dir/tasks/main.yml for include_tasks, resolving paths
    relative to the role directory."""
```

Call it after the playbook scan, for each role referenced by name in
`definitions` (extracted from `TaskDefinition.role`).

**Children carry role inheritance.** Grafted children get:
- `role = parent.role` (they belong to the same role group as the include)
- `parent_role = parent.role` (so `recursive-nesting.md` plan can use it)
- `tags = []` (we don't parse tags from the include file in this phase;
  runtime JSONL will fill them)
- `task_order = parent.task_order + idx / 1000.0` (preserve order, distinguish
  from runtime grafted children which use `-1`)
- `is_dynamic = False` — these are static, we are confident in them

**Tests first** (TC-094a, TC-094b, TC-094c):

- `TC-094a: Static include_tasks graft populates children`
  Pre-populate cache, call `graft_include_children`, assert children appear
  on the right `TaskDefinition`.

- `TC-094b: Role-relative include resolution`
  Include file at `roles/podman/tasks/_includes/site.yml`, referenced as
  `include_tasks: _includes/site.yml` from `roles/podman/tasks/main.yml`.
  Assert the cache key is the role-relative absolute path, not the
  playbook-relative one.

- `TC-094c: Jinja-templated include path is skipped`
  `include_tasks: "{{ var }}.yml"` → cache not populated → graft leaves
  stub untouched.

- `TC-094d: Nested includes graft transitively`
  Include A includes B includes C → A's children include B's, B's include C's.
  Assert depth.

- `TC-094e: block/rescue/always preserves include location`
  `block:` contains `include_tasks:`, children graft under the include
  stub's parent (the `block:` task), not the play root.

### Phase 2 — Wire `resolve_includes_from_playbook()` into preflight

**File:** `src/ansible_aom/ansible/preflight.py`

Two-line change at the end of `run_preflight()` (line 194, after
`assemble_definitions()`):

```python
definitions = assemble_definitions(plays=plays, play_hosts=play_hosts)

# Plan A: pre-expand static include_tasks before returning so the runner
# sees the full task list from frame 0.
include_cache: dict[str, IncludeCacheEntry] = {}
resolve_includes_from_playbook(playbook, definitions, include_cache)
graft_include_children(
    playbook_path=playbook,
    definitions=definitions,
    cache=include_cache,
)

return PreParseResult(
    plays=plays,
    play_hosts=play_hosts,
    definitions=definitions,
    errors=errors,
    include_cache=include_cache,  # NEW field
)
```

`PreParseResult` gains an `include_cache` field. Downstream: runner hands it
to `RunState._include_cache` (line 386 of models.py).

**Tests:**
- `TC-094f: run_preflight populates include_cache`
  Use `fake_executable` pattern (already in `test_preflight.py`).
  Inject a playbook fixture with `include_tasks: site.yml` and a
  `site.yml` in the same dir. Assert `result.include_cache` has the
  resolved path and the expected task names.

- `TC-094g: run_preflight passes include_cache through to definitions`
  Assert that `result.definitions` contains the grafted children
  (count them, assert structure).

### Phase 3 — Wire `discover_include_with_runtime_path()` into runtime handlers

**File:** `src/ansible_aom/core/models.py`

In `_handle_v2_playbook_on_task_start` (line 734) and
`_handle_v2_runner_on_start` (line 850), the existing call is:

```python
self._graft_or_match_task(task_id, task_name, task_path)
```

Extend the call site (NOT the function — keep `_graft_or_match_task` pure)
to first attempt a runtime include discovery:

```python
# Plan A: if this task's path matches an include_tasks file we
# discovered at runtime but missed at preflight (e.g. Jinja path
# or loop-resolved filename), populate the cache now. Best-effort;
# silently no-ops if the path doesn't resolve.
if task_path and ":" in task_path:
    discover_include_with_runtime_path(self, task_path, parent_role)

self._graft_or_match_task(task_id, task_name, task_path)
```

This adds a single I/O call per JSONL event whose path has a colon. Cheap
because `_discover_include` short-circuits on cache hit (line 237).

**Tests:**
- `TC-094h: Runtime graft populates cache from task.path`
  Simulate JSONL event with `task.path == "dynamic_include.yml:5"`,
  cache missing for that path → call → assert cache populated.

- `TC-094i: Runtime graft reuses preflight cache`
  Same path, cache pre-populated → call → assert no re-parse.

### Phase 4 — Hide the include stub in the tree

**File:** `src/ansible_aom/core/tree.py`

After grafting, the include stub is no longer needed as a visible row. Two
options:

**Option X (preferred): skip include stubs in `_emit_preflight_entries`**

In `_emit_preflight_entries()` (line 1271), add a guard before the
`items.append(...)`:

```python
# Plan A: skip the include_tasks stub row when it has grafted children.
# The children themselves will render as task rows.
if (
    kind != "running"
    and not entry.children
    and entry.name.startswith("Include ")
    and ":" not in entry.name  # safety: don't hide real tasks named "Include"
):
    continue
```

This collapses `"Include add_site tasks"` into its children. The
`(7 tasks)` count is unaffected (still walks `TaskDefinition.children`).

**Tests:**
- `TC-094j: Include stub with children is hidden`
  Build a play definition where the include stub has children → render →
  assert the stub name does not appear but the children do.

- `TC-094k: Include stub without children stays visible`
  Defensive case: Jinja-path include with no grafted children → render →
  assert stub still appears (so the user sees *something* and knows there's
  a runtime include).

### Phase 5 — Pre-flight denormalization for `count_total_tasks_seen`

**File:** `src/ansible_aom/compact/format.py`

`count_total_tasks_seen()` (line 699) already reads `state._include_cache`.
Once the runner hands the preflight cache into `RunState._include_cache`,
the denominator starts including include children from frame 0. **No code
change needed** — this just works.

But the function currently uses `max(preflight, runtime, cached)`. After
Plan A, `preflight` already includes include children via the graft, so
`max(preflight, cached)` is redundant but not wrong. Leave the `max()` for
defensive coverage of the runtime-only-dynamic case.

**Tests:** `test_dynamic_counters.py` already covers this. Re-run and verify
no regression.

## Files Touched

| File | Change |
|---|---|
| `src/ansible_aom/core/includes.py` | Add `graft_include_children()`, `_scan_role_tasks_for_includes()` |
| `src/ansible_aom/core/models.py` | Extend two event handler call sites to invoke `discover_include_with_runtime_path()` before `_graft_or_match_task` |
| `src/ansible_aom/core/tree.py` | Add include-stub skip in `_emit_preflight_entries()` (Option X) |
| `src/ansible_aom/core/parser.py` | Add `IncludeCacheEntry` and `include_cache` field to `PreParseResult` |
| `src/ansible_aom/ansible/preflight.py` | Call `resolve_includes_from_playbook()` + `graft_include_children()` after `assemble_definitions()` |
| `tests/unit/test_include_cache.py` | New tests TC-094a through TC-094e |
| `tests/unit/test_preflight.py` | New tests TC-094f, TC-094g |
| `tests/unit/test_tree_projection.py` | New tests TC-094j, TC-094k |
| `tests/unit/test_event_processing.py` | New tests TC-094h, TC-094i |
| `.sisyphus/test-fixtures/with_nested_include.yml` | New fixture for nested include |
| `TEST_SPECIFICATION.md` | Document TC-094a through TC-094k in section 5.2 |

## Sequencing & Dependencies

```
Phase 0 (fixtures)               ──┐
                                   ├── independent, run anytime
Phase 1 (graft function + tests) ──┘
                                   │
                                   ▼
Phase 2 (wire preflight) ── depends on Phase 1
                                   │
                                   ▼
Phase 3 (wire runtime)   ── depends on Phase 1 (uses graft's call site shape)
                                   │
                                   ▼
Phase 4 (hide stub)      ── depends on Phase 2 (needs grafted children to hide)
                                   │
                                   ▼
Phase 5 (counters)       ── depends on Phase 2 (cache must be populated)
```

Phase 0 + 1 can land together (fixtures don't break the test suite).
Phase 2 + 3 are independent of each other and can be parallelized.
Phase 4 + 5 are post-wiring cleanup.

Total: 6 PRs or 6 commits in dependency order, if you want atomic landing.
Realistically: 3 PRs (core/wiring/runtime | tree-presentation | polish).

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Role-relative path resolution disagrees with ansible | Med | Med | Test against `.sisyphus/test-fixtures/` integration runs; runtime graft remains fallback |
| Include file uses Jinja vars in `name:` fields | High | Low | Children inherit `name` literally; tree projection already handles `{{ }}` in names |
| Deeply nested includes blow up tree depth | Low | Med | Apply `_play_running_and_pending`'s existing depth heuristic; or cap at 4 levels (configurable later) |
| `apply:` scoping makes variables invisible to grafted children | Med | Low | Phase 1 grafts without `apply`; comment explicitly that runtime graft + JSONL is authoritative for tag/var resolution |
| Pre-flight adds 50–200ms latency | Med | Low | All YAML parsing is local fs reads, no subprocess; benchmark with `time aom site.yml` before/after |
| Cache key collisions between playbook-relative and role-relative paths | Low | High | Both scanners use `Path.resolve()` — same logical file → same absolute key |
| `recursive-nesting.md` plan depends on `parent_role` field we're setting | Low | Low | Coordinate: this plan sets `parent_role = role` on grafted children, which is what recursive-nesting reads |

## Test Specification Updates

Insert into `TEST_SPECIFICATION.md` section 5.2 (after existing TC-096):

```
### TC-094a: Static include_tasks graft populates children
**Category:** unit
**Priority:** high
**Description:** After resolve_includes_from_playbook + graft_include_children,
                include_tasks stubs have their included file's tasks as .children
**Test:** parent.children contains one TaskDefinition per parsed name with
         parent.role == include_stub.role
**Fixture/Setup:** tmp_path playbook with `include_tasks: site.yml`,
                  site.yml in same dir

### TC-094b: Role-relative include resolution
**Category:** unit
**Priority:** high
**Description:** `include_tasks: _includes/foo.yml` inside
                `roles/<name>/tasks/main.yml` resolves relative to role dir
**Test:** cache key == (role_dir / "_includes" / "foo.yml").resolve()
**Fixture/Setup:** tmp_path roles/podman/tasks/{main.yml, _includes/foo.yml}

### TC-094c: Jinja-templated include path is skipped
**Category:** unit
**Priority:** medium
**Description:** include_tasks: "{{ var }}.yml" leaves the stub ungrafted
**Test:** cache empty for that path; stub .children unchanged
**Fixture/Setup:** Jinja-templated include in tmp_path playbook

### TC-094d: Nested includes graft transitively
**Category:** unit
**Priority:** high
**Description:** include A includes B includes C → A.children include B's
                tasks, B's include C's
**Test:** Walk children at depth 2 and 3; assert names match
**Fixture/Setup:** Three-level include chain in tmp_path

### TC-094e: block/rescue/always preserves include location
**Category:** unit
**Priority:** medium
**Description:** `block: [include_tasks: foo.yml, ...]` grafts foo's tasks
                under the block task, not the play root
**Test:** The block TaskDefinition.children contains the grafted tasks
**Fixture/Setup:** Playbook with `block:` containing include_tasks

### TC-094f: run_preflight populates include_cache
**Category:** unit
**Priority:** high
**Description:** run_preflight calls resolve_includes_from_playbook and
                returns include_cache in PreParseResult
**Test:** result.include_cache contains resolved paths for literal
         include_tasks directives
**Fixture/Setup:** fake ansible-playbook executable; tmp_path playbook

### TC-094g: run_preflight passes include_cache through to definitions
**Category:** unit
**Priority:** high
**Description:** Definitions returned by run_preflight include grafted
                children on include_tasks stubs
**Test:** For each include_tasks stub in result.definitions, assert
         children count > 0
**Fixture/Setup:** As TC-094f

### TC-094h: Runtime graft populates cache from task.path
**Category:** unit
**Priority:** high
**Description:** When JSONL event has task.path pointing to a not-yet-cached
                include file, the cache is populated before graft
**Test:** Cache contains the path after the handler runs
**Fixture/Setup:** Build event with task.path = "site.yml:5"; site.yml in tmp_path

### TC-094i: Runtime graft reuses preflight cache
**Category:** unit
**Priority:** medium
**Description:** Same path seen twice → cache populated once
**Test:** Mock parse_include_tasks_file; assert called once
**Fixture/Setup:** Pre-populate cache; fire event twice

### TC-094j: Include stub with children is hidden
**Category:** unit
**Priority:** high
**Description:** Tree projection skips include_tasks stubs that have
                grafted children; children render as task rows
**Test:** Stub name not in rendered output; children names are
**Fixture/Setup:** Build PlayDefinition with grafted include

### TC-094k: Include stub without children stays visible
**Category:** unit
**Priority:** medium
**Description:** Defensive: include_tasks with Jinja path (no graft) still
                renders so the user sees *something*
**Test:** Stub name in rendered output
**Fixture/Setup:** Build PlayDefinition with bare include stub
```

## Out-of-scope follow-ups (parking lot)

- **TC-094l**: `apply:` scoping — apply vars from include_tasks to grafted children. Defer until a real playbook demands it.
- **TC-094m**: `vars_files:` resolution — parse `vars_files:` directives from included files. Same defer.
- **TC-094n**: Static loop expansion — `with_items` with a literal list (`with_items: [a, b, c]`). Mechanical to graft N times. Defer.
- **Plan A+**: Pre-compute the role tree shape (which roles contain which roles) for the recursive-nesting plan. Coordination, not duplication.

## Acceptance Criteria

Plan A is complete when:

1. `uv run pytest tests/unit/ -q` passes (all old + new tests)
2. `uv run pytest tests/integration/ -q` passes (real ansible-playbook against fixtures)
3. `uv run mypy src/ansible_aom` passes with no new `# type: ignore`
4. `uv run ruff check src/ansible_aom` clean
5. End-to-end smoke test:
   ```bash
   uv run aom .sisyphus/test-fixtures/with_include.yml
   ```
   Shows the `podman` role with all its children visible from frame 0
   (before any task starts), and `(9 tasks)` matches the visible list
   count exactly.
6. `aom inspect <session-id> --tree` on a recorded run shows the same
   expanded tree (post-mortem view agrees with live view).