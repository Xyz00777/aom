# Warning Pattern Detection

> 22 nodes · cohesion 0.15

## Key Concepts

- **test_real_ansible.py** (9 connections) — `tests/integration/test_real_ansible.py`
- **_run_aom()** (8 connections) — `tests/integration/test_real_ansible.py`
- **_parse_jsonl_through_core()** (6 connections) — `tests/integration/test_real_ansible.py`
- **Path** (6 connections)
- **TestRealAnsibleSmoke** (6 connections) — `tests/integration/test_real_ansible.py`
- **.test_simple_playbook_localhost_appears_exactly_once_in_summary()** (6 connections) — `tests/integration/test_real_ansible.py`
- **.test_simple_playbook_runs_and_records_session()** (6 connections) — `tests/integration/test_real_ansible.py`
- **_find_session()** (5 connections) — `tests/integration/test_real_ansible.py`
- **.test_syntax_error_playbook_returns_nonzero()** (4 connections) — `tests/integration/test_real_ansible.py`
- **_ansible_collection_paths()** (3 connections) — `tests/integration/test_real_ansible.py`
- **_has_ansible_posix()** (2 connections) — `tests/integration/test_real_ansible.py`
- **CompletedProcess** (1 connections)
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

- [Three-Pane Inspect App](Three-Pane_Inspect_App.md) (2 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/integration/test_real_ansible.py`

## Audit Trail

- EXTRACTED: 70 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*