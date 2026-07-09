# Terminal Capability Detection

> 20 nodes · cohesion 0.10

## Key Concepts

- **F4 — `aom rerun` Implementation Plan** (19 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **2026-05-12-f4-rerun-failed.md** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **File Structure** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Risks & Caveats** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Self-Review** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 10: Validate session has `ansible_args` (refuse old sessions cleanly)** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 11: argparse — wire up `aom rerun [<session-id>] [--failed] [--unreachable] [--changes-only] [--yes]`** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 12: `main` entry point — orchestrate resolve → load → compose → confirm → run** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 13: Hook `aom rerun` into the top-level CLI dispatch** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 14: End-to-end integration test — fake session → rerun → real runner** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 15: Final polish — type-check + format + full suite** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 1: Bump `meta.json` schema with `ansible_args`** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 2: Thread `ansible_args` through `_SessionSink`** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 3: Pure helper — `collect_failed_hosts(session) -> set[str]`** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 4: Pure helper — `collect_unreachable_hosts(session) -> set[str]`** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 5: Pure helper — `collect_changed_hosts(session) -> set[str]`** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 6: Resolve session ID — pick the latest when omitted** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 7: Compose the host set from CLI flags** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 8: Build the ansible-playbook command line** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **Task 9: Confirmation prompt — print plan, host count, idempotency warning** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`

## Relationships

- No strong cross-community connections detected

## Source Files

- `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`

## Audit Trail

- EXTRACTED: 38 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*