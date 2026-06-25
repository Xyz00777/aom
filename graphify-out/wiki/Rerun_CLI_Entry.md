# Rerun CLI Entry

> 10 nodes · cohesion 0.24

## Key Concepts

- **cli.py** (10 connections) — `src/ansible_aom/rerun/cli.py`
- **main()** (9 connections) — `src/ansible_aom/rerun/cli.py`
- **_build_rerun_command()** (4 connections) — `src/ansible_aom/rerun/cli.py`
- **_default_runner()** (4 connections) — `src/ansible_aom/rerun/cli.py`
- **_strip_limit_args()** (3 connections) — `src/ansible_aom/rerun/cli.py`
- **CLI entry point for ``aom rerun``.  Reads a recorded session, derives a host lis** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Drop any pre-existing ``--limit`` / ``-l`` from the args list.      Handles thre** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Construct the (playbook, ansible_args) pair to spawn for the rerun.      The ses** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **Real-world runner: spawn the renderer + run_playbook.      Lazy-imported so unit** (1 connections) — `src/ansible_aom/rerun/cli.py`
- **CLI entry point for ``aom rerun``.      Args:         argv: Argument list. If No** (1 connections) — `src/ansible_aom/rerun/cli.py`

## Relationships

- [[Rerun Host Set Composition]] (2 shared connections)
- [[Rerun Confirmation Prompt]] (2 shared connections)
- [[Rerun CLI Parser]] (2 shared connections)
- [[Ansible Args Validation]] (2 shared connections)
- [[Inspect Session List]] (2 shared connections)
- [[Playbook Run Integration Tests]] (1 shared connections)
- [[Renderer Factory Function]] (1 shared connections)
- [[Inspect CLI Commands]] (1 shared connections)

## Source Files

- `src/ansible_aom/rerun/cli.py`

## Audit Trail

- EXTRACTED: 32 (91%)
- INFERRED: 3 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*