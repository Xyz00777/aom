# Rerun CLI Command

> 14 nodes · cohesion 0.16

## Key Concepts

- **main() — orchestrate resolve → load → compose → confirm → run** (11 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **run_playbook(playbook, ansible_args, renderer)** (5 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **_create_parser() — argparse builder for 'aom rerun'** (3 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **_default_runner() — lazy-import renderer + run_playbook** (3 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **_build_rerun_command(session, hosts)** (2 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **cli.py: aom rerun dispatcher branch (sys.argv[1]=='rerun')** (2 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **_require_ansible_args(session, session_id) — schema-1.1 guard** (2 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **tests/unit/test_rerun_cli.py** (2 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **tests/integration/test_rerun.py** (2 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **meta.json: ansible_args field (schema v1.1)** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **_confirm(playbook, args, host_count, assume_yes, input_fn)** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **src/ansible_aom/rerun/cli.py** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **_resolve_session_id(state_dir, session_id)** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`
- **_strip_limit_args(args)** (1 connections) — `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`

## Relationships

- [[Host Set Collection]] (2 shared connections)
- [[Shell Completion Installation]] (1 shared connections)
- [[Compact Renderer Module]] (1 shared connections)
- [[Exit Code Derivation]] (1 shared connections)
- [[JSONL Line Stream]] (1 shared connections)
- [[Compact Display Sizing]] (1 shared connections)

## Source Files

- `docs/superpowers/plans/2026-05-12-f4-rerun-failed.md`

## Audit Trail

- EXTRACTED: 29 (78%)
- INFERRED: 8 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*