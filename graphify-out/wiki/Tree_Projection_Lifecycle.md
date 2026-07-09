# Tree Projection Lifecycle

> 18 nodes · cohesion 0.11

## Key Concepts

- **Key design decisions** (8 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **v1 Verbosity — Learnings (Phase 8 / Task 8.4: concurrency test)** (7 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Critical gotcha** (5 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **1. In-process `threading.Thread`, not a subprocess + SIGKILL** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **1. The test would NOT pass against a `load_session` that calls `json.loads` on the trailing partial line** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **2. Reader driven from the main thread, not a separate thread** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **2. The writer must `touch()` the events file before the reader's first open** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **3. 5 ms reader sleep, 2 s writer duration** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **3. The `next_tick` pacing pattern is critical for the rate guarantee** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **4. `Event.wait(timeout)` is the right sleep primitive in the writer loop** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **4. The 6 assertions map to 6 distinct regression modes** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **5. The "no truncated line" assertion is the load-bearing one** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **6. Tests live in `tests/integration/`, not `tests/unit/`** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **7. The reader uses `load_session` for the lower-layer test, not direct file I/O** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Followups (out of scope for Phase 8.4 — wired by later tasks)** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Test count tally for Phase 8 (updated)** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Verification log** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **What was built** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`

## Relationships

- [Runtime Event Handlers](Runtime_Event_Handlers.md) (1 shared connections)

## Source Files

- `.sisyphus/notepads/v1-verbosity/learnings.md`

## Audit Trail

- EXTRACTED: 35 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*