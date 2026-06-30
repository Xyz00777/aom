# Real Ansible Integration

> 20 nodes · cohesion 0.14

## Key Concepts

- **_run_aom()** (8 connections) — `tests/integration/test_real_ansible.py`
- **test_real_ansible.py** (7 connections) — `tests/integration/test_real_ansible.py`
- **_parse_jsonl_through_core()** (6 connections) — `tests/integration/test_real_ansible.py`
- **TestRealAnsibleSmoke** (6 connections) — `tests/integration/test_real_ansible.py`
- **.test_simple_playbook_localhost_appears_exactly_once_in_summary()** (6 connections) — `tests/integration/test_real_ansible.py`
- **.test_simple_playbook_runs_and_records_session()** (6 connections) — `tests/integration/test_real_ansible.py`
- **_find_session()** (5 connections) — `tests/integration/test_real_ansible.py`
- **.test_syntax_error_playbook_returns_nonzero()** (4 connections) — `tests/integration/test_real_ansible.py`
- **_ansible_collection_paths()** (3 connections) — `tests/integration/test_real_ansible.py`
- **_has_ansible_posix()** (2 connections) — `tests/integration/test_real_ansible.py`
- **Real-ansible smoke tests.  Every other "integration" test in this suite uses a f** (1 connections) — `tests/integration/test_real_ansible.py`
- **Return the lone session directory under ``home_dir`` or fail loudly.** (1 connections) — `tests/integration/test_real_ansible.py`
- **Feed each recorded line through ``JsonLineStream``.      This is the same code p** (1 connections) — `tests/integration/test_real_ansible.py`
- **Live ansible-playbook integration — fixtures that work with ``-c local``.      O** (1 connections) — `tests/integration/test_real_ansible.py`
- **Happy-path: simple.yml exits 0, writes a parseable session.** (1 connections) — `tests/integration/test_real_ansible.py`
- **For a single-host run, ``localhost`` shows up once in stats.** (1 connections) — `tests/integration/test_real_ansible.py`
- **A YAML syntax error in the playbook must surface as a non-zero exit.          an** (1 connections) — `tests/integration/test_real_ansible.py`
- **Search-path entries reported by ``ansible-galaxy collection list``.      The out** (1 connections) — `tests/integration/test_real_ansible.py`
- **True if the ``ansible.posix`` collection is installed and discoverable.      We** (1 connections) — `tests/integration/test_real_ansible.py`
- **Spawn ``python -m ansible_aom <playbook>`` against a sandboxed HOME.      Using** (1 connections) — `tests/integration/test_real_ansible.py`

## Relationships

- [[Run Config Key Normalization]] (6 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[CLI Help Matrix]] (1 shared connections)

## Source Files

- `tests/integration/test_real_ansible.py`

## Audit Trail

- EXTRACTED: 61 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*