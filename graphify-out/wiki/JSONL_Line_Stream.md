# JSONL Line Stream

> 4 nodes · cohesion 0.83

## Key Concepts

- **JsonLineStream (carries partial JSONL lines)** (4 connections) — `docs/superpowers/plans/2026-05-12-r1-jsonl-carry-buffer.md`
- **_CARRY_LIMIT = 1_000_000 bytes** (3 connections) — `docs/superpowers/plans/2026-05-12-r1-jsonl-carry-buffer.md`
- **JsonLineStream.feed_line(line) -> list[dict]** (2 connections) — `docs/superpowers/plans/2026-05-12-r1-jsonl-carry-buffer.md`
- **RunState.handle_event (unknown event fall-through pin)** (2 connections) — `docs/superpowers/plans/2026-05-12-r1-jsonl-carry-buffer.md`

## Relationships

- [[Rerun CLI Command]] (1 shared connections)

## Source Files

- `docs/superpowers/plans/2026-05-12-r1-jsonl-carry-buffer.md`

## Audit Trail

- EXTRACTED: 6 (55%)
- INFERRED: 5 (45%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*