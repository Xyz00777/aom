# Performance-Improvement Plan: AOM Compact Renderer

**Status:** Proposed — implementation queued after the diagnostics layer.
**Date:** 2026-05-21
**Motivation:** Real 14-host, ~thousands-of-tasks run died with exit 139 (SIGSEGV) after the preflight summary. Independent of crash root-cause (covered in [diagnostics-layer-design](2026-05-21-diagnostics-layer-design.md)), the compact renderer has quadratic-in-run-size compute on the per-event hot path. This plan fixes the verified hot spots in a TDD-first, independently-shippable sequence.

## 1. Verified hot spots

### HS-1: `_render_status_panel` called on every JSONL event
**Location:** `src/ansible_aom/compact/renderer.py:235`, called from `update_state` at line 215.

Every `update_state` call invokes `_render_status_panel`, which:

- Allocates a new `TreeProjection` object
- Iterates all `P × T × H` host states to compute `host_statuses`
- Calls `count_completed_tasks` and `count_total_tasks_seen` (see HS-2)
- Calls `shutil.get_terminal_size` (a syscall)
- Calls `projection.host_rows()` and `projection.tree_lines()` (see HS-3)

**Cost:** O(P × T × H) per event. With 14 hosts and thousands of tasks, this is O(14 × T) on every single JSONL line. `Display.update` at line 324 is throttled at 4 Hz, so the actual terminal write is coalesced, but the heavy compute in `_render_status_panel` runs on every event regardless.

### HS-2: `count_completed_tasks` and `count_total_tasks_seen` — full-state walks per render
**Location:** `src/ansible_aom/compact/format.py:535–573`.

`count_completed_tasks` (line 551): iterates all plays → tasks → hosts; O(P × T × H).
`count_total_tasks_seen` (line 535): walks all `PlayDefinition` tasks plus iterates `state.plays`; O(P × T_def + P × T_runtime).

Called on every event, each independently re-walking the entire state. No memoization, no incremental update.

### HS-3: `TreeProjection.host_rows` and `tree_lines` — full P×T×H traversal per render
**Location:** `src/ansible_aom/core/tree.py:147–200` (host_rows), `212–311` (tree_lines).

`host_rows`: iterates every play → task → host with status classification and `datetime` subtraction for elapsed time; O(P × T × H).
`_tree_lines_unbounded`: iterates every play's tasks, then for each running task iterates all hosts; O(P × T_running × H).

Called every render cycle (up to 4 Hz via `Display.update`), and also every `_render_status_panel` invocation which happens on every event.

`TreeProjection.from_run_state` at line 88 is trivial (just wraps the state reference), but the projection object is re-created per render — discarding the `_role_index` memo on line 85, forcing `_task_role` to rebuild it from scratch on first call.

### HS-4: `_emit_event_log` — `print_log` per host per event, each a full terminal rewrite
**Location:** `src/ansible_aom/compact/renderer.py:747`.

For `v2_runner_on_ok`, `v2_runner_on_failed`, `v2_runner_on_unreachable` events, the loop at lines 811–819, 823–834, 838–849 calls `self._display.print_log(...)` once per host in `event.get("hosts", {})`. Each `print_log` call does a full `_rewind_status` + `_CLEAR_TO_EOS` + rewrite of the full status panel. With H=14 hosts in a single batched event, this triggers 14 ANSI full-panel rewrites back-to-back with no throttle (throttling applies only to `Display.update`, not `Display.print_log`).

**Cost:** O(H) panel rewrites per runner-result event. For a 14-host run, each task completion generates 14 ANSI write sequences. With thousands of tasks, this is the dominant stdout cost.

### HS-5: `_graft_or_match_task` — O(T_def) linear scan per task-start and runner-start event
**Location:** `src/ansible_aom/core/models.py:248`, called at lines 296 and 364.

The inner loop at line 264 calls `_iter_leaf_task_defs(self.definitions)` which materializes a flat list of all leaf `TaskDefinition` objects from all plays, then does a linear scan for a name match. Called on every `v2_playbook_on_task_start` and `v2_runner_on_start` event. With thousands of tasks, `_iter_leaf_task_defs` reallocates a list of T_def entries on every event and then scans it in O(T_def) worst-case.

**Cost:** O(T_def) allocation + scan per task-start event.

### HS-6: `_resolve_play_hosts` — O(P_def) scan per task-start
**Location:** `src/ansible_aom/core/models.py:336`, called from `_handle_v2_playbook_on_task_start` at line 327.

Iterates all `PlayDefinition` entries to match by play name. Called on every `v2_playbook_on_task_start`. Low individual cost but entirely redundant — the mapping is static from preflight and changes only when `set_definitions` is called.

**Cost:** O(P_def) per task-start event.

### HS-7: `_format_per_host_lines` in `handle_completion` — O(P×T×H) full walk at teardown
**Location:** `src/ansible_aom/compact/renderer.py:571`. Not on the hot path but worth noting — a huge state with millions of `HostRunState` entries (per spec limits: up to 1,000,000 total) is walked entirely at completion time to recompute counts from scratch rather than reading cached aggregates.

### HS-8: `_render_status_panel` — triple-nested host status scan with dict-of-dict allocation
**Location:** `src/ansible_aom/compact/renderer.py:256–270`.

The loop to build `host_statuses` (lines 258–262) iterates P × T × H and allocates a new `dict[str, Status]` on every call. This is separate from the `count_completed_tasks` walk — the same data is traversed independently by two code paths per render cycle.

## 2. Proposed fixes

### Fix for HS-1, HS-8: Dirty-flag gating on `_render_status_panel`

**Mechanism:** Add a boolean `_panel_dirty` flag to `CompactRenderer`. Set it to `True` in `update_state` and `set_definitions`. In `_render_status_panel`, if `_panel_dirty` is `False` and the elapsed-time change is < 1s since the last render, return immediately. Reset the flag after a successful render.

This is a *compute-throttle* that matches `Display.update`'s write-throttle. Since `Display.update` already coalesces writes, the goal is to avoid spending CPU on the panel computation for events that will produce no visible output. A dirty flag is simpler and safer than a full version counter because state mutations are not atomic — adding a counter would need care around `definitions` vs `plays` mutations.

**Alternative rejected:** threading a version counter through `RunState`. It would require `core/` to carry rendering-concerns scaffolding, violating the architecture. A flag on `CompactRenderer` is infrastructure-only.

**Parallelism note:** This is explicitly *not* the answer. The bottleneck is main-thread CPU on small Python dict operations (HS-2, HS-3, HS-5). Threading a renderer would not help — state mutations happen in the main thread and Python's GIL would serialize any concurrent render anyway. Async I/O does not help either; this is CPU compute, not I/O wait.

### Fix for HS-2: Incremental task counters on `CompactRenderer`

**Mechanism:** Maintain two `int` counters `_tasks_seen` and `_tasks_completed` directly on `CompactRenderer`. Bump them inside event handlers rather than re-walking the state on every render:

- `v2_playbook_on_task_start` → `_tasks_seen += 1`
- Terminal result events (ok/failed/skipped/unreachable) where all hosts are done → `_tasks_completed += 1`

`count_total_tasks_seen` and `count_completed_tasks` in `format.py` remain unchanged; the compact renderer simply stops calling them on every render and reads its own counters instead. The functions still exist for the TUI and tests.

**Where it lives:** Counters on `CompactRenderer` (infrastructure), not `core/`. They are a rendering artifact, not a domain fact.

### Fix for HS-3: Persistent `TreeProjection` with explicit invalidation

**Mechanism:** Keep a single `TreeProjection` instance as `self._projection` on `CompactRenderer` rather than calling `TreeProjection.from_run_state(state)` per render. Invalidate `_projection` (set to `None`) whenever `update_state` processes an event that could change the visible tree (task_start, runner events, stats). Re-create lazily at the top of `_render_status_panel` only when dirty.

Additionally, `_role_index` in `TreeProjection` (line 85) is already memoized per-instance. By keeping the same instance alive across renders, this memo survives between renders during steady-state ticks — the `_task_role` O(P_def × T_def) build cost is paid only once after a task-start event, not on every tick.

**Where it lives:** `CompactRenderer` (infrastructure). `TreeProjection` itself is `core/` and stays unchanged.

### Fix for HS-4: Batch per-host log lines into one `print_log` per event

**Mechanism:** In `_emit_event_log`, collect all per-host result strings for a runner event into a single `"\n".join(lines)` and call `print_log` once instead of once per host. This reduces panel-rewrite count from H per event to 1 per event.

**Before:** H calls to `print_log`, each doing `_rewind_status + _CLEAR_TO_EOS + rewrite`.
**After:** 1 call to `print_log` with a multiline string; `Display.print_log` writes one `_rewind_status + _CLEAR_TO_EOS + all_lines + rewrite`.

`Display.print_log` already accepts multi-line strings (the `message.endswith("\n")` check at line 289 is the only branching point). No change to `Display` is needed.

**Where it lives:** `compact/renderer.py:_emit_event_log`. Pure rendering decision; no `core/` change.

### Fix for HS-5: Precomputed name → `TaskDefinition` index on `RunState`

**Mechanism:** Add a private `_task_def_index: dict[str, TaskDefinition]` to `RunState`, populated lazily when `definitions` is set (or when first accessed). `_graft_or_match_task` consults the index instead of calling `_iter_leaf_task_defs` + linear scan.

**Where it lives:** `core/models.py`. This is pure domain logic — `_graft_or_match_task` is already in `core/` and the index is a memoization of a pure computation over `self.definitions`.

**Implementation note:** Populate the index in `_rebuild_task_def_index()` called from `_graft_or_match_task` when `_task_def_index is None`. Invalidate (set to `None`) whenever `self.definitions` is reassigned. Since `set_definitions` happens once before any events flow, in practice the index is built once.

### Fix for HS-6: Precomputed play-name → `PlayDefinition` index

**Mechanism:** Add `_play_def_by_name: dict[str, PlayDefinition]` populated alongside the task-def index. `_resolve_play_hosts` does a single dict lookup instead of an O(P_def) scan.

**Where it lives:** `core/models.py`.

## 3. Sequence and dependencies

Phase ordering is driven by two rules: (1) no change should break a currently-green test, and (2) riskier changes (ones that touch both the hot path and the rendering output) come last.

**Phase A — Safe, independent (can land in parallel):**

- **A1:** Fix HS-4 — batch `print_log` per event. Touches only `_emit_event_log`; no state changes; trivial to test with snapshot assertions.
- **A2:** Fix HS-5+HS-6 — add `_task_def_index` and `_play_def_by_name` to `RunState`. Pure `core/` change; tested in isolation by existing and new unit tests.

**Phase B — Depends on A2:**

- **B1:** Fix HS-3 — persistent `TreeProjection` on `CompactRenderer`. Depends on A2 completing cleanly (no regressions in `_graft_or_match_task`) so the projection can safely be invalidated only on task-start/runner events.

**Phase C — Depends on B1:**

- **C1:** Fix HS-2 — incremental task counters. Depends on B1 (persistent projection confirms which events mutate visible state) so we can pick exactly which event types to hook for counter bumps without missing any.
- **C2:** Fix HS-1+HS-8 — dirty-flag gating on `_render_status_panel`. Depends on C1 (the counters remove the need for the full-scan in the panel path, making the dirty-flag actually cheap to act on).

## 4. Tests to write first

Test file naming follows the existing convention: unit tests in `tests/unit/`, compact-renderer tests in `tests/compact/`.

### A1 tests — `tests/compact/test_emit_event_log_batching.py`

- `TC-PERF-001`: Given a `v2_runner_on_ok` event with 14 hosts, assert `Display.print_log` is called exactly once (not 14 times). Patch `Display.print_log` with a spy.
- `TC-PERF-002`: Assert the single `print_log` call's argument contains all 14 host lines joined by `"\n"`. Output correctness regression test.

### A2 tests — `tests/unit/test_run_state_index.py`

- `TC-PERF-010`: After `state.definitions = [...]`, assert `state._task_def_index` matches a manually-built dict of `{task.name: task}` for all leaf definitions.
- `TC-PERF-011`: Given 1000 preflight `TaskDefinition` objects, `_graft_or_match_task` for a known task name resolves in O(1) — assert `_iter_leaf_task_defs` is NOT called (mock it to raise and verify no exception).
- `TC-PERF-012`: `_resolve_play_hosts` with 50 plays resolves by name in O(1) via `_play_def_by_name`.

### B1 tests — `tests/compact/test_tree_projection_lifecycle.py`

- `TC-PERF-020`: After `update_state` with a `v2_playbook_on_task_start` event, assert `renderer._projection is None` (invalidated). After `_render_status_panel`, assert `renderer._projection is not None` (rebuilt).
- `TC-PERF-021`: Two consecutive `tick()` calls with no intervening `update_state` use the same projection instance (object identity check).

### C1 tests — `tests/compact/test_incremental_counters.py`

- `TC-PERF-030`: Feed a sequence of task_start + runner_on_ok events; assert `renderer._tasks_completed` matches `count_completed_tasks(state)` after each event.
- `TC-PERF-031`: Dynamic `include_tasks` event (unknown task arriving after a known parent) still increments `_tasks_seen` correctly.

### C2 tests — `tests/compact/test_render_dirty_flag.py`

- `TC-PERF-040`: Two consecutive `update_state` calls within one throttle window result in exactly one `_render_status_panel` panel computation. Spy on `TreeProjection.host_rows` to count calls.
- `TC-PERF-041`: `tick()` called while `_panel_dirty` is `False` skips the projection compute entirely.

## 5. Layer assignment for new logic

| New component | File | Layer | Justification |
|---|---|---|---|
| `_task_def_index: dict[str, TaskDefinition]` | `core/models.py` | `core/` | Pure memoization of existing domain state. `_graft_or_match_task` is already in `core/`. |
| `_play_def_by_name: dict[str, PlayDefinition]` | `core/models.py` | `core/` | Same — pure memoization, no I/O. |
| `_rebuild_task_def_index()` | `core/models.py` | `core/` | Called only from `_graft_or_match_task` and `_resolve_play_hosts`; no infra deps. |
| `_tasks_seen`, `_tasks_completed` counters | `compact/renderer.py` | `compact/` | Rendering artifact — reflects what the compact view has *emitted*, not the authoritative domain count (which remains in `format.count_completed_tasks`). |
| `_projection: TreeProjection \| None` | `compact/renderer.py` | `compact/` | Lifecycle optimization for the renderer; `TreeProjection` is already `core/`. |
| `_panel_dirty: bool` | `compact/renderer.py` | `compact/` | Pure rendering throttle; no domain semantics. |
| Batched log-line assembly | `compact/renderer.py:_emit_event_log` | `compact/` | String joining for terminal output is an infrastructure concern. |

The `format.count_completed_tasks` and `format.count_total_tasks_seen` functions in `compact/format.py` are NOT removed — they remain as the test oracle for the incremental counters (TC-PERF-030) and are still used by `handle_completion` which runs only once.

## 6. Out of scope / explicit non-goals

- **TUI-side parity.** `AOMApp.update_state` has no rendering hot path to speak of (it just increments `_dirty` and lets Textual's event loop handle refresh). No TUI changes in this round.
- **Async I/O or threading.** The bottleneck is CPU on Python dict/list iteration, not I/O wait. Adding threads would introduce GIL contention and new synchronization bugs with no throughput gain.
- **Switching compact mode to Textual.** Not motivated by this data.
- **Memory bounds enforcement.** `state_machine.py` defines `MAX_TOTAL_HOST_RUN_STATES = 1_000_000` but nothing enforces it. The SIGSEGV at 14 hosts × "thousands of tasks" is well inside that bound (~14,000 entries), so the crash is not a memory-limit issue and enforcement is outside this plan's scope.
- **Session sink write batching.** `sink.record_event` is called per event but disk I/O is already best-effort. Profile-guided batching would help in extreme cases but is not the primary bottleneck identified here.
- **`format.py` function removals.** All existing pure formatters stay as-is for TUI, replay, and test-oracle use.
- **`_row_count` regex cost.** Called on every `print_log` and `update` in `display.py`. The compiled `_ANSI_ESCAPE_RE` is a module-level singleton; cost is linear in panel text length. Not a priority for this round.

## 7. Open questions

**OQ-1: Counter reset on replay.** When `aom replay` re-drives a `CompactRenderer`, `_tasks_seen` and `_tasks_completed` must reset between runs. Is there an explicit "reset" lifecycle method, or should counters be initialized in `start()`? Confirm whether `start()` is guaranteed to be called before `update_state` on every re-use of a renderer instance.

**OQ-2: `definitions` mutation after `set_definitions`.** The plan assumes `_task_def_index` needs to be built only once per run, because `set_definitions` fires once before events flow. Confirm this is invariant — if `add_definitions` or partial-streaming-preflight is ever added, the index invalidation strategy needs to be revisited.

**OQ-3: Dirty-flag granularity for `print_log` path.** `print_log` calls `_render_status_panel` indirectly (it re-emits the panel content via `Display.print_log`, not `Display.update`). Should the dirty flag apply only to the `Display.update` path, or should log-line batching (HS-4, A1) be treated as the mechanism that removes the per-host computation cost on the `print_log` path? This affects C2 scope.

**OQ-4: Profiler baseline.** Before committing to phase ordering, a 5-minute cProfile run against a replayed large session would quantify whether HS-4 (H × `print_log` per event) or HS-2+HS-3 (O(P×T×H) panel recompute) is the larger absolute wall-clock cost. Does a representative `events.jsonl` from the failing 14-host run exist in the session store?
