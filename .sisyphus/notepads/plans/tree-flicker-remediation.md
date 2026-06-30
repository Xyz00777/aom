# Tree Flicker and Task Row Stability Remediation Plan

**Status:** Planned, not started. This file is the execution roadmap for the remaining tree flicker and task-row instability seen in real `server-setup` workloads.
**Priority:** Critical. The renderer is usable, but real multi-play workloads still expose incorrect tree identity, row churn, and transient task misattribution.
**Branch:** feat/nom-compact-renderer (current)

---

## Problem Statement

The compact tree still flickers and reorders task rows under hostile real workloads, even after the May 24 fixes for cross-play leakage, sticky fallback, stuck meta tasks, and upcoming-play visibility.

The remaining failures are not cosmetic only. They point to an unstable execution identity model:

1. The renderer still rebuilds projection state too eagerly, so sticky task fallback and row continuity can be lost between events.
2. Runtime task matching is still too name-based, which breaks under duplicate names, handlers, includes, `run_once`, delegation, async completion, and serial replay.
3. Active-play borrowing still allows rows to be sourced from the wrong play in edge windows.
4. Duplicate play names and repeated plays under `serial` need explicit play execution identity, not list position or display name.
5. Upstream `ansible.posix.jsonl` behavior is strategy-dependent and filters implicit tasks unless explicitly opted in, so the model must tolerate partial and asymmetric event streams.

This plan assumes the durable fix belongs in core execution identity and projection lifetime, not in renderer-only heuristics.

---

## Confirmed Findings

1. **Sticky fallback likely does not persist at the right layer**
   The current tree can remember the last running play, but task-row stability is still weak because projection is likely rebuilt from scratch on every event.

2. **Task matching is too name-based**
   Matching by display name is not strong enough for repeated task names, repeated includes, handlers, imported content, or parallel task lifecycles.

3. **Cross-play borrowing still exists as a concept**
   Completed-play leakage was reduced, but the active-play cross-play scan can still borrow rows from the wrong play during transition windows.

4. **Play identity is under-specified**
   Duplicate play names, imported playbooks, and `serial` execution require a stable play execution key. Play name alone is not enough.

5. **JSONL event coverage is incomplete by design**
   `ansible.posix.jsonl` emits different task-start signals by strategy and omits or filters some implicit tasks unless configured for them. The model must handle missing starts, missing finishes, and implicit task surfaces without collapsing row identity.

---

## Root Causes

| Issue | Why it still happens | Consequence |
|------|-----------------------|-------------|
| Projection lifetime is frame-local | Tree rows are derived fresh from current state instead of from a durable projection keyed by execution identity | Sticky fallback can disappear, rows jump, pending and running entries churn |
| Runtime identity is too weak | Matching leans on task name, loose role context, and borrowed scans | Duplicate names map to wrong rows, especially across plays and handlers |
| Play identity is weak | Play name and sequence inference are insufficient for duplicate names and `serial` replay | Rows can attach to the wrong play execution |
| Cross-play borrowing is too permissive | Active plays can still inspect other plays for runtime state | Transition windows can misattribute rows |
| Implicit-task normalization is incomplete | Meta tasks, handlers, async follow-up tasks, delegated results, and include surfaces do not all emit symmetric events | Rows can stick in running state or be remapped late |
| Real-world validation is too narrow | Existing tests cover isolated fixtures better than hostile `server-setup` runs | Regressions survive until interactive smoke testing |

---

## Implementation Plan

### Phase 0: Replay Harness and Repro-First Test Bed (Priority: Critical)

**Goal:** Make the flicker reproducible from recorded event streams before changing identity logic.

**Work:**

1. Add a replay harness that can feed recorded JSONL event streams into `RunState` and the tree projection deterministically, frame by frame.
2. Add snapshot-style assertions for tree row ordering, row identity continuity, and play selection across successive frames.
3. Capture and document minimal repro recordings from the strongest real playbooks listed below.
4. Define row-stability assertions that fail when a task row changes identity without a real lifecycle transition.

**Deliverables:**

- Replay fixture format for hostile event sequences
- Frame-by-frame tree assertions
- Minimal recorded repros for the top real playbooks

**Why first:** Without deterministic replay, every later fix risks becoming another interactive-only patch.

---

### Phase 1: Core Execution Identity Model (Priority: Critical)

**Goal:** Replace fragile name-based matching with durable play and task execution identity in `core/`.

**Work:**

1. Introduce explicit **play execution identity** that distinguishes:
   - repeated play names
   - `serial` batches that re-enter the same logical play
   - imported playbooks that surface similar names
   - handler-only and meta-only execution windows
2. Introduce explicit **task execution identity** that prefers upstream event identifiers and stable ancestry when available, then uses deterministic fallback components rather than raw task name.
3. Track ancestry for task surfaces such as:
   - include/import parent
   - role origin
   - handler origin
   - delegation target
   - async launcher versus async result poller
4. Move identity derivation into core state management so both compact and TUI consumers inherit the same semantics.

**Acceptance intent:** The renderer should be able to ask core, "what execution row is this event for?" without doing fuzzy matching itself.

---

### Phase 2: Durable Projection and Row Leases (Priority: Critical)

**Goal:** Preserve row continuity across events, idle gaps, and partial event coverage.

**Work:**

1. Introduce a durable tree projection object that survives across events instead of being rebuilt as a throwaway derivation each frame.
2. Add **row leases** or similar persistence so a row remains attached to its last known execution identity until a stronger lifecycle signal replaces it.
3. Make sticky fallback live at the projection layer, not only at play selection.
4. Separate these concepts clearly:
   - execution identity
   - projection slot / row identity
   - current visual classification, pending, running, completed
5. Add bounded eviction rules so completed rows age out intentionally, not because projection was rebuilt.

**Key finding addressed:** Sticky fallback is likely lost because projection is rebuilt every event.

---

### Phase 3: Play-Boundary and Active-Play Borrowing Fixes (Priority: High)

**Goal:** Stop task rows from crossing play boundaries during transition windows.

**Work:**

1. Restrict cross-play borrowing to explicitly modeled cases only, preferably handlers with a known owner relationship.
2. Remove generic active-play borrowing that depends on loose task-name scans.
3. Make play selection use play execution identity plus projection state, not "last play with tasks" style heuristics.
4. Add transition tests for:
   - play end to next play start gap
   - duplicate play names
   - `serial` batches
   - imported playbooks that repeat play labels

**Acceptance intent:** No row in play A should appear because play B emitted a similarly named runtime task.

---

### Phase 4: Meta, Handler, Include, Async, and Delegation Normalization (Priority: High)

**Goal:** Normalize the hostile task types that currently destabilize row identity.

**Work:**

1. Define explicit handling for implicit tasks with weak or asymmetric host events:
   - `meta: flush_handlers`
   - `meta: reset_connection`
   - handler starts without normal task-start symmetry
2. Normalize include and import surfaces so parent include rows, expanded children, and runtime task announcements share the same ancestry model.
3. Normalize async tasks so launcher rows and async-status rows do not steal each other's identity.
4. Normalize delegated tasks so host attribution and task identity are separated cleanly.
5. Normalize `run_once` and serial replay so a single logical task can appear across multiple execution windows without row reuse bugs.
6. Audit `ansible.posix.jsonl` assumptions and add explicit notes for what can be relied on under linear, free, and host-pinned strategies.

**Confirmed finding addressed:** Upstream `ansible.posix.jsonl` is strategy-dependent and filters implicit tasks unless opted in.

---

### Phase 5: Regression Shielding and Real-Workload Validation (Priority: High)

**Goal:** Lock the fix down with both deterministic tests and hostile workload validation.

**Work:**

1. Add unit tests for identity derivation, projection leases, and play-boundary ownership.
2. Add replay regression tests for the captured real workloads.
3. Add integration notes for manual validation against the strongest `server-setup` playbooks.
4. Fail tests on row churn, not just wrong final content. Stability across frames is part of correctness.
5. Update relevant notepads with any upstream callback caveats discovered during implementation.

---

## Execution Order

```text
Phase 0: Replay harness and repro fixtures
    ↓
Phase 1: Core execution identity
    ↓
Phase 2: Durable projection and row leases
    ↓
Phase 3: Play-boundary and borrowing fixes
    ↓
Phase 4: Meta / handler / include / async / delegation normalization
    ↓
Phase 5: Regression shielding and real-workload validation
```

**Rationale:**

- Phase 0 makes the bug reproducible.
- Phase 1 defines what a row actually represents.
- Phase 2 keeps that identity alive across frames.
- Phase 3 removes boundary violations once identity exists.
- Phase 4 handles the hostile event shapes.
- Phase 5 keeps future patches from backsliding into heuristics.

---

## Minimal Repro and Validation Matrix

### Top real repro playbooks

1. `/opt/syncthing/sync/ncc1031/git/server-setup/playbooks/identity/deploy_freeipa.yml`
2. `/opt/syncthing/sync/ncc1031/git/server-setup/playbooks/general/update_software.yml`
3. `/opt/syncthing/sync/ncc1031/git/server-setup/playbooks/general/monitoring.yml`
4. `/opt/syncthing/sync/ncc1031/git/server-setup/playbooks/proxmox/deploy_vms.yml`

### Validation matrix

| Playbook | Constructs to cover | Why it matters | Expected validation |
|---------|---------------------|----------------|---------------------|
| `deploy_freeipa.yml` | duplicate task names, handlers, meta tasks, likely serial or staged play flow | Good stress case for play identity and implicit-task stability | No row flicker at play boundaries, no borrowed handler rows, meta rows settle correctly |
| `update_software.yml` | handlers, includes, package-task repetition, host variance | Repeated task labels can expose name-based matching bugs | Stable row continuity for repeated names, include children stay attached to the right parent |
| `monitoring.yml` | role-heavy flow, delegation or service orchestration, repeated service tasks | Good role and delegation identity stress case | Role grouping remains stable, delegated task rows do not steal normal task rows |
| `deploy_vms.yml` | async work, delegation, long-running tasks, multi-play orchestration | Best async and transition stress case | Async launcher and async result rows remain distinct, no cross-play churn during waits |

### Targeted fixture additions for repo-local testing

| Fixture type | Purpose |
|-------------|---------|
| Duplicate play names with `serial` | Prove play execution identity is stronger than play name |
| Repeated task names across adjacent plays | Prove task rows do not cross-play borrow |
| Handler-only transition window | Prove active-play borrowing is bounded and explicit |
| Meta task with zero host events | Prove implicit tasks keep stable terminal rows |
| Include plus repeated child names | Prove ancestry-aware matching beats name matching |
| Async launch plus async status polling | Prove two related task surfaces do not share one row |
| Delegated task plus non-delegated twin | Prove host attribution does not collapse execution identity |

---

## Acceptance Criteria

- [ ] Recorded replay tests reproduce the current flicker before the fix and pass after the fix.
- [ ] Tree projection is durable across events. It is not rebuilt as a stateless frame-only structure.
- [ ] Sticky fallback for task rows survives quiet frames and transition windows.
- [ ] Runtime task matching no longer depends primarily on bare task name.
- [ ] Duplicate play names and `serial` replay are distinguished by explicit play execution identity.
- [ ] Active-play cross-play borrowing is either removed or reduced to explicit owner-linked cases only.
- [ ] Meta tasks, handlers, includes, async tasks, delegated tasks, and `run_once` flows keep stable row identity.
- [ ] The four named `server-setup` repro playbooks no longer show visible tree flicker or task-row instability during manual validation.
- [ ] New regression tests assert frame-to-frame row continuity, not just final tree contents.
- [ ] Future renderer code can consume identity and projection from core without re-implementing fuzzy ownership logic.

---

## Out of Scope

- Full redesign of the compact panel visual layout
- Broad TUI feature work unrelated to execution identity
- Upstream changes to `ansible.posix.jsonl`
- Perfect reconstruction of task intent when upstream never emits enough information to distinguish two identical surfaces
- Performance micro-optimizations before identity correctness is stable

---

## Open Questions

1. Which upstream event fields are strong enough to form task execution identity across all supported strategies?
2. Should play execution identity be attached at preflight assembly time, runtime play-start time, or both?
3. For `serial`, should each batch become a distinct play execution or a child execution window of one logical play?
4. How much cross-play borrowing is still truly needed once handlers and implicit tasks have explicit ownership?
5. Should durable projection live in `RunState`, a tree-specific projection model in `core/`, or a renderer-facing adapter that still preserves identity across frames?
6. What is the right eviction policy for completed rows so stability is preserved without letting the tree grow forever?
7. Do we need explicit callback opt-in or config guidance for implicit tasks that upstream filters by default?

---

## Related Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/tree.py`
- `src/ansible_aom/core/preflight.py`
- `src/ansible_aom/compact/renderer.py`
- `src/ansible_aom/compact/format.py`
- `tests/unit/`
- `tests/integration/`
- `.sisyphus/notepads/implementation/learnings.md`
- `.sisyphus/notepads/implementation/issues.md`
- `.sisyphus/notepads/impl-gaps/learnings.md`

---

## Estimated Effort

| Phase | Effort | Risk |
|------|--------|------|
| 0. Replay harness and repro fixtures | 4 to 6 hours | Medium |
| 1. Core execution identity | 6 to 10 hours | High |
| 2. Durable projection and row leases | 4 to 8 hours | High |
| 3. Play-boundary fixes | 3 to 5 hours | Medium |
| 4. Normalization of hostile task types | 5 to 8 hours | High |
| 5. Regression shielding and validation | 3 to 5 hours | Medium |

**Total:** about 25 to 42 hours

**Critical path:** Phase 0 → Phase 1 → Phase 2
