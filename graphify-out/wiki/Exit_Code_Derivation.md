# Exit Code Derivation

> 5 nodes · cohesion 0.50

## Key Concepts

- **JsonRenderer (Renderer Protocol impl)** (4 connections) — `docs/superpowers/plans/2026-05-12-f6-json-output.md`
- **RunSummary (Pydantic schema_version=1)** (4 connections) — `docs/superpowers/plans/2026-05-12-f6-json-output.md`
- **determine_exit_code(state) (compact/renderer.py)** (2 connections) — `docs/superpowers/plans/2026-05-12-f6-json-output.md`
- **HostCounts(ok, changed, failed, unreachable)** (1 connections) — `docs/superpowers/plans/2026-05-12-f6-json-output.md`
- **TaskFailure(host, task, msg)** (1 connections) — `docs/superpowers/plans/2026-05-12-f6-json-output.md`

## Relationships

- [[Rerun CLI Command]] (1 shared connections)
- [[Compact Renderer Module]] (1 shared connections)

## Source Files

- `docs/superpowers/plans/2026-05-12-f6-json-output.md`

## Audit Trail

- EXTRACTED: 11 (92%)
- INFERRED: 1 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*