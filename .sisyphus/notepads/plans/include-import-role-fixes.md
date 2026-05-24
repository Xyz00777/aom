# Include/Import/Role Counter & Tree Fix Plan

**Status:** Complete — all acceptance criteria met (2026-05-24). See `implementation/learnings.md` for session-by-session details.
**Priority:** High — dynamic `include_tasks`/`include_role` render without correct role grouping and counters undercount
**Branch:** feat/nom-compact-renderer (current)

---

## Problem Statement

Dynamic `include_tasks`, `include_role`, `import_tasks`, `import_role`, and `import_playbook` are partially or incorrectly handled:

1. **Tree view breaks role grouping** — Dynamic children render as bare ungrouped tasks because `_task_role` only indexes preflight flat lists, not `TaskDefinition.children`.
2. **Counters are incorrect** — `count_total_tasks` only sums preflight leaf tasks. Dynamic includes are invisible to the denominator. `count_total_tasks_seen` uses `max(preflight, runtime)` which is jumpy.
3. **No include caching** — Each dynamic task is grafted one-by-one as ansible announces them. We can't pre-populate the tree with "□ pending" entries because we don't know the structure ahead of time.
4. **Missing fixture coverage** — No `include_role` fixture, no nested include fixture, no `import_playbook` handling verification.
5. **No rendering/counter tests** — 8 grafting tests exist, but zero tests for tree output or counter accuracy with includes.

---

## Ansible Include/Import Mechanisms — Coverage Audit

| Mechanism | Expand Method | Preflight Visible? | AOM Handler | Tested? |
|-----------|---------------|--------------------|-------------|---------|
| `import_tasks` | Static (preflight) | Yes — `--list-tasks` expands | `assemble_definitions` → `TaskDefinition` | **No tree/counter tests** |
| `include_tasks` | Dynamic (runtime) | No — `--list-tasks` skips | `_graft_or_match_task` → `children` | 8 grafting tests, **no tree/counter tests** |
| `import_role` | Static (preflight) | Yes — `--list-tasks` expands | `assemble_definitions` → `TaskDefinition` (with `.role`) | **No tests at all** |
| `include_role` | Dynamic (runtime) | No — `--list-tasks` skips | Task arrives as `"role : task_name"`, `_task_role` strips prefix | 5 runtime role count tests, **no counter tests** |
| `import_playbook` | Static (preflight) | Separate plays in `--list-tasks` | Treated as separate plays by ansible JSONL | **No tests at all** |
| `roles:` keyword | Static (preflight) | Yes — `--list-tasks` expands | `assemble_definitions` → `TaskDefinition` with `.role` | Basic role grouping tests |

**Key insight:** `import_tasks` and `import_role` ARE expanded by preflight `--list-tasks`, so `count_total_tasks` should already work for them. But we have **no test confirming this**. The counter bug is specifically `include_tasks` and `include_role` (dynamic, not in preflight).

---

## Root Causes

| Issue | Location | Cause |
|-------|----------|-------|
| A. Role index ignores dynamic children | `tree.py:753-773` | Index built from `play_def.tasks` flat list, never walks `.children` |
| B. `role_total_tasks` ignores dynamic children | `tree.py:507-546` | Only counts from `play_def.tasks`, runtime-only tasks counted separately but `.children` not walked |
| C. Counters ignore dynamic includes | `format.py:661-669` | `count_total_tasks` only walks `play_def.tasks`, never `.children` |
| D. No include caching | `models.py` / preflight | No pre-parsing of included files at any stage |
| E. Missing rendering tests | `tests/` | `test_dynamic_expansion.py` tests grafting API only, not tree output or counters |
| F. Missing fixture coverage | `.sisyphus/test-fixtures/` | No `include_role` fixture, no nested includes |
| G. `import_playbook` untested | `tests/` | No verification that cross-play boundaries are correct |

---

## Implementation Plan

### Phase 0: Include Cache Infrastructure (Priority: High)

**Goal:** Pre-parse `include_tasks` files during preflight (static paths) and cache discovered includes at runtime (dynamic paths) so the tree can show "□ pending" entries and counters can estimate total tasks before each task arrives.

**Storage location:** `RunState` (shared between compact and TUI renderers)

**New data structures:**

```python
# core/models.py

@dataclass
class IncludeCacheEntry:
    path: str                     # resolved absolute path to included file
    task_names: list[str]         # task names (may contain Jinja2 templates)
    task_count: int               # len(task_names)
    role: str | None              # inherited role from parent, if any
    parsed_at: datetime

@dataclass
class RoleCacheEntry:
    """Cached role structure discovered at runtime (include_role)."""
    role_name: str
    task_names: list[str]         # bare names (role prefix stripped)
    task_count: int

@dataclass  
class RunState:
    # ... existing fields ...
    
    # NEW: include/role caches
    _include_cache: dict[str, IncludeCacheEntry] = field(default_factory=dict)
    _role_cache: dict[str, RoleCacheEntry] = field(default_factory=dict)
    _resolved_includes: set[str] = field(default_factory=set)
```

**Cache operations:**

```python
def _discover_include(state: RunState, include_path: str, parent_role: str | None) -> IncludeCacheEntry:
    """Parse an include file and cache its task definitions."""
    # 1. Resolve path relative to playbook or ansible search paths
    # 2. Parse YAML, extract task names (may have templates)
    # 3. Store in _include_cache
    # 4. Return entry
    pass

def _discover_role(state: RunState, role_name: str) -> RoleCacheEntry:
    """Parse a role's tasks/main.yml and cache its task definitions."""
    pass
```

**Where calls happen:**

1. **Preflight** (`core/preflight.py` or new `core/includes.py`):
   - After `assemble_definitions`, scan each `TaskDefinition`:
   - If `--list-tasks` output contains an `include_tasks` task entry (it shows the include directive itself as a task named "Include other tasks"):
   - Look at the source playbook YAML for `include_tasks: somefile.yml`
   - If path is a **static literal** (no `{{ }}`): parse the file immediately, cache in `PreParseResult`
   - If path is **dynamic**: skip, will cache at runtime

2. **Runtime** (`models.py`, in `_handle_v2_playbook_on_task_start`):
   - When a task named "Include other tasks" starts (ansible emits an include directive as a task):
   - If not already in `_include_cache`: parse the file, cache
   - If already cached: mark as "active" for this play
   - Increment `role_total_tasks` and counter denominator from cache

3. **Tree rendering** (`tree.py`):
   - `_emit_runtime_play`: check `_include_cache` for any active include
   - Use cached `task_names` to emit "□ pending" placeholder entries
   - As runtime tasks match the names, update status (pending → running → ok)

**How tree uses cache:**

```python
# In _emit_runtime_play():
for task in play.tasks.values():
    if is_include_task(task.name):  # "Include other tasks"
        cache = state._include_cache.get(resolved_path)
        if cache:
            # Emit cached task names as □ pending entries
            for cached_name in cache.task_names:
                # Look up runtime status (may be RUNNING if already started, PENDING if not)
                runtime = runtime_by_name.get(cached_name)
                items.append((_classify(runtime), cached_name, cache.role, runtime))
```

**Template name handling:**
- Cache stores template names as-is: `"Setup {{ app_name }}"`
- Runtime matching uses existing `_is_template_match` + `strip_role_prefix`
- If template resolves to different name than cache expected, update cache entry
- The cache is for **estimation** (counters, placeholder entries), not for exact matching

---

### Phase 1: Tree Role Index Fix (Priority: High)

**Goal:** Make `_task_role` and `role_total_tasks` aware of dynamic children.

**Changes:**

1. **`tree.py:_task_role` (line 753-773)** — Build index from `play_def.tasks` AND their `.children`:
   - After iterating `play_def.tasks`, recursively walk `TaskDefinition.children` 
   - Add `idx[child.name] = child.role` for each dynamic child
   - Same for `known_roles.add(child.role)`

2. **`tree.py:_emit_runtime_play` (line 507-546)** — Include dynamic children in `role_total_tasks`:
   - After counting from `play_def.tasks`, walk `entry.children` for any `TaskDefinition`
   - Add to `role_total_tasks[role]` for each child
   - Dedupe against `emitted_preflight_names` (already done for runtime tasks, extend)

3. **Include cache integration** — When cache is available, add `cache.task_count` to `role_total_tasks`:
   - Read from `state._include_cache`
   - Add to relevant role (from `cache.role` or `_task_role` of include parent)

**Tests:**
- TC-300: Dynamic child under role "nginx" → `_task_role("Dynamic task")` returns "nginx"
- TC-301: Dynamic child inherits parent role in tree output
- TC-302: Role label shows "(5 tasks)" for 3 preflight + 2 dynamic tasks under same role

**Verification:** Tree output shows dynamic children under correct role header, with correct task counts.

---

### Phase 2: Counter Accuracy (Priority: High)

**Goal:** `count_total_tasks`, `count_total_tasks_seen`, `count_completed_tasks` all account for dynamic includes correctly.

**Changes:**

1. **`format.py:count_total_tasks`** — Walk `children` AND use include cache:
   - After summing `_count_tasks(play)`, also sum `len(task.children)` for all tasks with children
   - Also add cached include task counts from `RunState._include_cache`
   - No backward compat concern — the function is internal

2. **`format.py:count_total_tasks_seen`** — Integrate include cache:
   - `max(count_total_tasks(..., include_cache=...), runtime)` 
   - Currently uses `max(preflight, runtime)` — extend to include cached count

3. **`format.py:count_completed_tasks`** — Already walks `state.plays.values()`, should work for dynamic tasks since they're in `play.tasks`. Verify with test.

4. **`compact/renderer.py:_bump_task_counters`** — Add include awareness:
   - When a dynamic task starts (`v2_playbook_on_task_start` for task not in preflight): check include cache, if cached, increment `_tasks_seen` by 1 (not cache size — each task counts individually)
   - Ensure `_completed_task_ids` deduplication still works for dynamic tasks

5. **Remove `count_total_tasks_seen`** — This was a workaround. With the cache, we can compute the correct denominator from `count_total_tasks(include_cache=...)` directly. The `max()` logic becomes unnecessary.

**Tests:**
- TC-310: `count_total_tasks` returns 8 for play with 3 static + 5 cached include tasks
- TC-311: Counter shows `0/8 → 1/8 → 2/8` for include tasks (smooth, not jumpy)
- TC-312: `count_completed_tasks` counts dynamic include children when their hosts are terminal
- TC-313: `count_total_tasks` with nested include (A includes B includes C) counts all leaf tasks
- TC-314: `import_tasks` (static) already counted correctly — confirm with test

**Verification:** Run `with_include.yml` fixture, assert counter denominator is 4 (1 direct + 3 from included_tasks.yml).

---

### Phase 3: Tree Rendering of Dynamic Children (Priority: High)

**Goal:** Dynamic include children appear in tree with correct status, under correct role, with correct host leaves.

**Changes:**

1. **`tree.py:_play_running_and_pending`** — Already handles runtime-only tasks (line 717-724). Extend to emit cached include entries as "pending":
   - After current runtime-only loop, check `state._include_cache` for active includes
   - For each cached task not yet seen in runtime, emit as `("pending", name, role, None)`

2. **`tree.py:_emit_runtime_play`** — Handle cached entries in the item loop:
   - `item_kind == "pending"` with no runtime → draw `□ pending` glyph
   - When runtime becomes available → reuse existing glyph assignment

3. **Cross-play include handling** — Include cache is per-playbook-run, not per-play. Two plays using the same `include_tasks: setup.yml` share the cache. Verify this doesn't double-count (use `_resolved_includes` set).

**Tests:**
- TC-320: Play with `include_tasks` → tree shows □ pending entries for cached tasks before they start
- TC-321: Running include task shows ◐, completed shows ●
- TC-322: Multiple includes from same file share cache (no duplicate parsing)
- TC-323: Nested include (A includes B) → tree shows B's tasks under correct parent
- TC-324: Dynamic path include (`include_tasks: "{{ file }}"`) grafts tasks one-by-one (no cache)

**Verification:** Tree output has correct hierarchy: play → role → include parent → include children.

---

### Phase 4: Fixture Expansion (Priority: Medium)

**Goal:** Cover all include/import/role variants with real playbooks.

**New fixtures:**
| Fixture | Description | Exercises |
|---------|-------------|-----------|
| `with_include_role.yml` | Uses `include_role: test_role` dynamically | Dynamic role task counting, role prefix stripping |
| `with_import_role.yml` | Uses `import_role: test_role` | Static role in preflight, counter verification |
| `with_nested_include.yml` | A includes B includes C | Multi-level include depth |
| `with_dynamic_include.yml` | `include_tasks: "{{ task_file }}"` | Template-based include paths |
| `with_import_playbook.yml` | Uses `import_playbook: another.yml` | Cross-play import, play boundary verification |

**Extend existing:**
- `with_include.yml` — add second level include (include_tasks that includes more tasks)
- `with_role.yml` — add `include_role` in tasks block (currently only `roles:` keyword)
- `included_tasks.yml` — add more tasks for better counter visibility

---

### Phase 5: Integration Tests (Priority: Medium)

**Goal:** End-to-end tests with real ansible for all include/import/role variants.

**New test file:** `tests/integration/test_include_import_role.py`

| Test | Fixture | Validates |
|------|---------|-----------|
| TC-330 | `with_import.yml` | Static import: counter starts at correct total (4 tasks) |
| TC-331 | `with_import.yml` | Static import: tree shows import_tasks inline (no grafting) |
| TC-332 | `with_include.yml` | Dynamic include: cached tasks shown as pending, counter rises smoothly |
| TC-333 | `with_nested_include.yml` | Nested include: all levels visible in tree |
| TC-334 | `with_include_role.yml` | Dynamic role: task counting and tree grouping |
| TC-335 | `with_import_role.yml` | Static role: counter verification |
| TC-336 | `with_dynamic_include.yml` | Dynamic path: tasks graft one-by-one, counter updates per task |
| TC-337 | `with_import_playbook.yml` | Import playbook: cross-play counter + tree correct |
| TC-338 | `with_role.yml` | Static `roles:` keyword: counter + tree correct |
| TC-339 | `with_include.yml` | Completion: final counter equals total runtime tasks |

---

## Execution Order

```
Phase 0 (Include Cache) ──── required by all phases
        │
        ├──► Phase 1 (Tree Role Index) ──► Phase 4 (Fixtures)
        │                                         │
        ├──► Phase 2 (Counters) ──────────────────┤
        │                                         │
        └──► Phase 3 (Tree Rendering) ────────────┤
                                                  │
                           Phase 5 (Integration Tests) ←───┘
```

**Rationale:**
- Phase 0 is the foundation — the cache is needed by all subsequent work
- Phases 1/2/3 can run in parallel after Phase 0
- Phase 4 (fixtures) enables Phase 5 (integration tests)
- Phase 5 runs last, validating the full stack

---

## Acceptance Criteria

- [x] `include_tasks` tasks cached on first encounter (static paths preflight, dynamic runtime)
- [x] Dynamic children render under correct role header (not bare)
- [x] Role headers show correct task count including dynamics: `(N tasks)`
- [x] Counter progression smooth: `0/8 → 1/8 → 2/8` not `0/4 → 1/5 → 2/6`
- [x] `import_tasks` counted correctly (should already work, confirmed by test)
- [x] `include_role` tasks counted and role-grouped correctly
- [x] `import_role` tasks counted correctly (preflight path)
- [x] `import_playbook` play boundaries respected (separate plays in tree)
- [x] 66+ new unit tests (TC-300+ in `test_include_cache.py`, `test_dynamic_counters.py`, `test_tree_classify_and_role_labels.py`)
- [x] 9 new integration tests (TC-330 to TC-339 in `test_include_import_role.py`)
- [x] 6 new test fixtures (`with_include_role.yml`, `with_import_role.yml`, `with_nested_include.yml`, `with_dynamic_include.yml`, `dynamic_target.yml`, `nested_level1.yml`, `nested_level2.yml`)
- [x] All 2255 existing tests pass (including 66 new from implementation)

---

## What We're NOT Doing (Out of Scope)

- **Dynamic include path pre-parsing**: `include_tasks: "{{ var }}"` with Jinja2 in the path is inherently unknown until resolution. Cache on first runtime encounter only.
- **Cross-run include caching**: Session persistence of includes across runs. Stale-include risk. Out of scope.
- **`import_playbook` tree integration**: `import_playbook` creates separate plays in ansible's output. AOM already handles multi-play runs. Verify don't fix.
- **`v2_playbook_on_include` event handler**: Ansible-core 2.21+ emits this. Worth adding a handler for future compatibility but not blocking for current fix.

---

## Open Questions

1. **Include file path resolution**: Where do we look? Relative to playbook? Relative to CWD? Ansible roles paths? Current plan: relative to playbook directory, same as ansible.

2. **YAML parsing for include files**: Do we need a full Ansible playbook parser or can we use simple `yaml.safe_load`? Tasks inside include files are standard `tasks:` lists — `yaml.safe_load` should suffice.

3. **Cache eviction**: Same include might be called differently by different plays (with different variables). Should cache per resolved path only, or also per play context? Current plan: per resolved path. If different plays use different template variable values, the actual resolved task names will differ — grafting handles this.

4. **TaskDefinition.children vs cache**: Should we keep the grafting approach (`.children` on parent `TaskDefinition`) alongside the new cache? Yes — cache provides estimation and placeholder entries; grafting provides actual runtime linkage. Both coexist.

---

## Related Files

- `src/ansible_aom/core/models.py` — RunState, `_graft_or_match_task`, IncludeCacheEntry
- `src/ansible_aom/core/tree.py` — `_emit_runtime_play`, `_task_role`, `_play_running_and_pending`
- `src/ansible_aom/compact/format.py` — `count_total_tasks`, `count_total_tasks_seen`, `count_completed_tasks`
- `src/ansible_aom/compact/renderer.py` — `_bump_task_counters`, `_render_status_panel`
- `src/ansible_aom/core/preflight.py` — `assemble_definitions` (extend for static include scanning)
- `src/ansible_aom/core/includes.py` — **NEW** — `_discover_include`, `_discover_role`, YAML parsing
- `.sisyphus/test-fixtures/with_include.yml` — extend
- `.sisyphus/test-fixtures/with_role.yml` — extend
- `.sisyphus/test-fixtures/with_include_role.yml` — **NEW**
- `.sisyphus/test-fixtures/with_import_role.yml` — **NEW**
- `.sisyphus/test-fixtures/with_nested_include.yml` — **NEW**
- `.sisyphus/test-fixtures/with_dynamic_include.yml` — **NEW**
- `.sisyphus/test-fixtures/with_import_playbook.yml` — **NEW**
- `tests/unit/test_dynamic_expansion.py` — extend for rendering tests
- `tests/unit/test_dynamic_tree_rendering.py` — **NEW**
- `tests/unit/test_dynamic_counters.py` — **NEW**
- `tests/unit/test_include_cache.py` — **NEW**
- `tests/integration/test_include_import_role.py` — **NEW**
- `TEST_SPECIFICATION.md` — add TC-300 to TC-339

---

## Estimated Effort

| Phase | Effort | Risk |
|-------|--------|------|
| 0: Include Cache | 4-6 hours | Medium — new module, YAML parsing |
| 1: Tree Role Index | 2-3 hours | Low — extends existing patterns |
| 2: Counter Accuracy | 3-4 hours | Medium — touches `_bump_task_counters` |
| 3: Tree Rendering | 3-4 hours | Medium — pending placeholder entries |
| 4: Fixtures | 1-2 hours | Low — YAML playbooks |
| 5: Integration Tests | 3-4 hours | High — requires ansible-core installed |

**Total:** ~16-23 hours
**Critical path:** Phase 0 → Phase 2 (counters needed before fixtures validated by integration tests)
