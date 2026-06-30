# Preflight Env Subprocess

> 6 nodes · cohesion 0.40

## Key Concepts

- **preflight.py** (6 connections) — `src/ansible_aom/ansible/preflight.py`
- **_preflight_env()** (3 connections) — `src/ansible_aom/ansible/preflight.py`
- **_spawn_one()** (3 connections) — `src/ansible_aom/ansible/preflight.py`
- **Pre-flight: parallel `--list-tasks` + `--list-hosts` orchestration.  This module** (1 connections) — `src/ansible_aom/ansible/preflight.py`
- **Spawn a single ansible-playbook invocation; return (exit_code, stdout, stderr).** (1 connections) — `src/ansible_aom/ansible/preflight.py`
- **Environment for preflight subprocesses.      `ANSIBLE_NOCOLOR=1` forces ansible-** (1 connections) — `src/ansible_aom/ansible/preflight.py`

## Relationships

- [[Preflight Definition Assembly]] (2 shared connections)
- [[Parallel Pre-flight Runner]] (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/preflight.py`

## Audit Trail

- EXTRACTED: 15 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*