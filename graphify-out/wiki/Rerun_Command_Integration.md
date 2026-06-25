# Rerun Command Integration

> 6 nodes · cohesion 0.33

## Key Concepts

- **test_rerun.py** (3 connections) — `tests/integration/test_rerun.py`
- **test_aom_rerun_failed_spawns_with_correct_limit()** (3 connections) — `tests/integration/test_rerun.py`
- **test_aom_rerun_no_failures_exits_1_without_spawning()** (3 connections) — `tests/integration/test_rerun.py`
- **End-to-end integration test for `aom rerun`.  Wires the real ``run_playbook`` ag** (1 connections) — `tests/integration/test_rerun.py`
- **`aom rerun --failed --yes` spawns ansible-playbook with --limit web2,web3.** (1 connections) — `tests/integration/test_rerun.py`
- **When the session has no failures, `--failed` exits 1 and never spawns.** (1 connections) — `tests/integration/test_rerun.py`

## Relationships

- [[Run Config Key Normalization]] (2 shared connections)

## Source Files

- `tests/integration/test_rerun.py`

## Audit Trail

- EXTRACTED: 12 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*