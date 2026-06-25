# Host Set Collection

> 5 nodes · cohesion 0.60

## Key Concepts

- **_compose_host_set(session, failed, unreachable, changes_only)** (4 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **src/ansible_aom/core/session.py — pure helpers** (4 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **collect_changed_hosts(session) -> set[str]** (2 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **collect_failed_hosts(session) -> set[str]** (2 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **collect_unreachable_hosts(session) -> set[str]** (2 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`

## Relationships

- [[Rerun CLI Command]] (2 shared connections)

## Source Files

- `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`

## Audit Trail

- EXTRACTED: 8 (57%)
- INFERRED: 6 (43%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*