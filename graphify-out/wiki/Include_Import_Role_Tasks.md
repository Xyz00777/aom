# Include Import Role Tasks

> 22 nodes · cohesion 0.11

## Key Concepts

- **_run_aom()** (14 connections) — `tests/integration/test_include_import_role.py`
- **test_include_import_role.py** (11 connections) — `tests/integration/test_include_import_role.py`
- **.test_dynamic_path_include()** (4 connections) — `tests/integration/test_include_import_role.py`
- **TestImportTasksTree** (4 connections) — `tests/integration/test_include_import_role.py`
- **.test_import_tasks_counter()** (4 connections) — `tests/integration/test_include_import_role.py`
- **.test_imported_tasks_appear_in_output()** (4 connections) — `tests/integration/test_include_import_role.py`
- **.test_all_three_levels_visible()** (4 connections) — `tests/integration/test_include_import_role.py`
- **_ansible_collection_paths()** (3 connections) — `tests/integration/test_include_import_role.py`
- **TestDynamicIncludePath** (3 connections) — `tests/integration/test_include_import_role.py`
- **TestNestedInclude** (3 connections) — `tests/integration/test_include_import_role.py`
- **_has_ansible_posix()** (2 connections) — `tests/integration/test_include_import_role.py`
- **Integration tests for include/import/role task variants.  Covers TC-330 through** (1 connections) — `tests/integration/test_include_import_role.py`
- **TC-330 / TC-331: import_tasks tree rendering and counter accuracy.** (1 connections) — `tests/integration/test_include_import_role.py`
- **TC-330: import_tasks are expanded — all task names visible.** (1 connections) — `tests/integration/test_include_import_role.py`
- **TC-331: import_tasks counter = 4 runtime tasks.** (1 connections) — `tests/integration/test_include_import_role.py`
- **TC-333: nested include_tasks — all 3 levels in tree output.** (1 connections) — `tests/integration/test_include_import_role.py`
- **TC-333: verify all 3 nesting levels appear in output.** (1 connections) — `tests/integration/test_include_import_role.py`
- **TC-336: Dynamic path include — ``include_tasks: \"{{ task_file }}\"``.** (1 connections) — `tests/integration/test_include_import_role.py`
- **TC-336: dynamic include path works, tasks grafted one-by-one.** (1 connections) — `tests/integration/test_include_import_role.py`
- **Search-path entries reported by ``ansible-galaxy collection list``.      We repu** (1 connections) — `tests/integration/test_include_import_role.py`
- **True if the ``ansible.posix`` collection is installed and discoverable.** (1 connections) — `tests/integration/test_include_import_role.py`
- **Spawn ``python -m ansible_aom <playbook>`` against a sandboxed HOME.      Extra** (1 connections) — `tests/integration/test_include_import_role.py`

## Relationships

- [[Run Config Key Normalization]] (5 shared connections)
- [[Include Tasks Dynamic Grafting]] (3 shared connections)
- [[Include Role Dynamic Tasks]] (2 shared connections)
- [[Multi-Play Cross Counters]] (2 shared connections)
- [[Static Role Counter]] (2 shared connections)
- [[CLI Help Matrix]] (1 shared connections)

## Source Files

- `tests/integration/test_include_import_role.py`

## Audit Trail

- EXTRACTED: 67 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*