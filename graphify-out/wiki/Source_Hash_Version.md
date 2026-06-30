# Source Hash Version

> 12 nodes · cohesion 0.18

## Key Concepts

- **source_hash()** (6 connections) — `src/ansible_aom/__init__.py`
- **_compute_source_hash()** (4 connections) — `src/ansible_aom/__init__.py`
- **__init__.py** (3 connections) — `src/ansible_aom/__init__.py`
- **.test_cli_version_includes_source_hash()** (3 connections) — `tests/unit/test_cli.py`
- **.test_source_hash_changes_when_source_changes()** (3 connections) — `tests/unit/test_cli.py`
- **.test_source_hash_is_short_stable_hex()** (3 connections) — `tests/unit/test_cli.py`
- **AOM (Ansible Output Monitor) - nom-style terminal interface for ansible-playbook** (1 connections) — `src/ansible_aom/__init__.py`
- **Short stable hash of every .py source file under the package.      Companion to** (1 connections) — `src/ansible_aom/__init__.py`
- **Public wrapper for ``_compute_source_hash``. Cached on first call.** (1 connections) — `src/ansible_aom/__init__.py`
- **``aom --version`` prints version AND source hash.** (1 connections) — `tests/unit/test_cli.py`
- **``source_hash()`` returns a deterministic short hex digest.** (1 connections) — `tests/unit/test_cli.py`
- **A source-file content change must alter the hash.          Verifies the hash act** (1 connections) — `tests/unit/test_cli.py`

## Relationships

- [[CLI Interface Tests]] (3 shared connections)
- [[CLI Main Entry Point]] (1 shared connections)

## Source Files

- `src/ansible_aom/__init__.py`
- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 21 (75%)
- INFERRED: 7 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*