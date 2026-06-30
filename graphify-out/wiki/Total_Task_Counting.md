# Total Task Counting

> 29 nodes · cohesion 0.08

## Key Concepts

- **count_total_tasks()** (16 connections) — `src/ansible_aom/compact/format.py`
- **count_total_tasks_seen()** (13 connections) — `src/ansible_aom/compact/format.py`
- **test_dynamic_counters.py** (11 connections) — `tests/unit/test_dynamic_counters.py`
- **.handle_completion()** (9 connections) — `src/ansible_aom/compact/renderer.py`
- **_count_tasks()** (7 connections) — `src/ansible_aom/compact/format.py`
- **test_total_tasks_seen_includes_include_cache()** (7 connections) — `tests/unit/test_dynamic_counters.py`
- **test_total_tasks_with_role_group_and_dynamic_children()** (6 connections) — `tests/unit/test_dynamic_counters.py`
- **test_total_tasks_counts_dynamic_children()** (5 connections) — `tests/unit/test_dynamic_counters.py`
- **test_total_tasks_counts_import_tasks_as_static()** (5 connections) — `tests/unit/test_dynamic_counters.py`
- **test_total_tasks_multi_play_with_dynamic_children()** (5 connections) — `tests/unit/test_dynamic_counters.py`
- **test_total_tasks_no_dynamic_children()** (5 connections) — `tests/unit/test_dynamic_counters.py`
- **with_nested_include.yml (NEW)** (4 connections) — `.sisyphus/test-fixtures/with_nested_include.yml`
- **test_total_tasks_empty_definitions()** (3 connections) — `tests/unit/test_dynamic_counters.py`
- **Recursively count leaf tasks inside a ``RoleGroupDefinition``.      ``RoleGroupD** (2 connections) — `src/ansible_aom/compact/format.py`
- **test_count_total_tasks_empty()** (2 connections) — `tests/compact/test_task_progress.py`
- **with_dynamic_include.yml (NEW)** (2 connections) — `.sisyphus/test-fixtures/with_dynamic_include.yml`
- **Handle playbook completion (success/failure/crash).          Shows final status** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **dynamic_target.yml** (1 connections) — `.sisyphus/test-fixtures/dynamic_target.yml`
- **nested_level1.yml (NEW)** (1 connections) — `.sisyphus/test-fixtures/nested_level1.yml`
- **nested_level2.yml (NEW)** (1 connections) — `.sisyphus/test-fixtures/nested_level2.yml`
- **with_include_role.yml (NEW)** (1 connections) — `.sisyphus/test-fixtures/with_include_role.yml`
- **Unit tests for dynamic counter accuracy (TC-310–TC-317).  Tests that ``_count_ta** (1 connections) — `tests/unit/test_dynamic_counters.py`
- **import_tasks are expanded by --list-tasks — they appear as regular     static Ta** (1 connections) — `tests/unit/test_dynamic_counters.py`
- **A play with RoleGroupDefinition entries and a TaskDefinition that     has dynami** (1 connections) — `tests/unit/test_dynamic_counters.py`
- **3 static + 5 dynamic children under one parent → total = 8.** (1 connections) — `tests/unit/test_dynamic_counters.py`
- *... and 4 more nodes in this community*

## Relationships

- [[Play Definition Tree Population]] (9 shared connections)
- [[Run State Completion Recap]] (9 shared connections)
- [[Task Definition Live Refresh]] (6 shared connections)
- [[Compact Renderer Formatters]] (4 shared connections)
- [[Include Role Discovery]] (3 shared connections)
- [[Panel Refresh Snapshot]] (2 shared connections)
- [[Run State Summary Panel]] (2 shared connections)
- [[Compact Renderer Implementation]] (2 shared connections)
- [[Preflight Summary Rendering]] (1 shared connections)
- [[RunState Renderer Invariants]] (1 shared connections)
- [[Failure Recap Formatting]] (1 shared connections)
- [[Run History Mining]] (1 shared connections)

## Source Files

- `.sisyphus/test-fixtures/dynamic_target.yml`
- `.sisyphus/test-fixtures/nested_level1.yml`
- `.sisyphus/test-fixtures/nested_level2.yml`
- `.sisyphus/test-fixtures/with_dynamic_include.yml`
- `.sisyphus/test-fixtures/with_include_role.yml`
- `.sisyphus/test-fixtures/with_nested_include.yml`
- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`
- `tests/compact/test_task_progress.py`
- `tests/unit/test_dynamic_counters.py`

## Audit Trail

- EXTRACTED: 65 (57%)
- INFERRED: 50 (43%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*