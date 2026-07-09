# Limit Args Merging

> 23 nodes · cohesion 0.09

## Key Concepts

- **F2 — `aom replay <session-id>`** (12 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **F3 — `--no-record`** (7 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **2026-05-12-f2-replay-and-no-record.md** (3 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **F2 Replay + F3 `--no-record` Implementation Plan** (3 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **File Structure** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Self-Review** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Sequencing** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 10: `meta.json["status"]` drives completion state** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 11: Ctrl+C mid-replay → `(130, "crashed")`** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 12: Add `replay` subcommand dispatch in `cli.main`** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 13: Implement `replay.cli_main` with argparse + renderer factory** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 14: Update `aom --help` epilog to mention `replay`** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 15: Integration test — record → replay round-trip** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 16: Full-suite verification + lint** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 1: Add `record` parameter to `run_playbook`** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 2: Add `--no-record` flag to CLI parser** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 3: Thread `record` through `_run_compact`** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 4: Thread `record` through `AOMApp` and `_run_tui`** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 5: Integration test — `--no-record` produces no session dir** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 6: Update CLI help epilog for `--no-record`** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 7: Define `replay_session` skeleton + load-events test** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 8: Pacing — `--speed 0` no sleeps, normal speed scales delta** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`
- **Task 9: Negative-delta guard test** (1 connections) — `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`

## Relationships

- No strong cross-community connections detected

## Source Files

- `docs/superpowers/plans/2026-05-12-f2-replay-and-no-record.md`

## Audit Trail

- EXTRACTED: 44 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*