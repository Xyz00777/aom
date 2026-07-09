# Small Terminal Handling

> 15 nodes · cohesion 0.13

## Key Concepts

- **Key design decisions** (7 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **v1 Verbosity — Learnings (Phase 5 / Task 5.3: auto-set ANSIBLE_CALLBACK_PLUGINS)** (6 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **What was built** (4 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **1. Two-package split: `callbacks/` vs `ansible/callback/`** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **2. Connection-callback dir listed FIRST in the search path** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **3. `os.pathsep` not hard-coded `:`** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **4. Non-fatal: missing connection-callback dir doesn't fail the run** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **5. No user-visible flag — auto-load only** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **6. Tests are pre-5.3 contract + new 5.3 contract** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Changes to `src/ansible_aom/ansible/runner.py`** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Changes to `tests/unit/test_callback_env.py`** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Changes to `tests/unit/test_posix_callback.py`** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Followups (out of scope for Phase 5.3)** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Test count tally for Phase 5** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Verification log** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`

## Relationships

- [Runtime Event Handlers](Runtime_Event_Handlers.md) (1 shared connections)

## Source Files

- `.sisyphus/notepads/v1-verbosity/learnings.md`

## Audit Trail

- EXTRACTED: 29 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*