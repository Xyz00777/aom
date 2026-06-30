# Template Name Regression

> 16 nodes · cohesion 0.21

## Key Concepts

- **TestTemplateVariableNameMismatch** (15 connections) — `tests/unit/test_template_variable_names.py`
- **_play_def()** (7 connections) — `tests/unit/test_template_variable_names.py`
- **_td()** (7 connections) — `tests/unit/test_template_variable_names.py`
- **.test_completed_template_task_dropped_from_tree()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_host_leaf_under_resolved_template_task()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_no_duplicate_for_template_and_resolved_name()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_template_variable_in_role_task()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_template_variable_resolved()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **test_template_variable_names.py** (4 connections) — `tests/unit/test_template_variable_names.py`
- **Regression tests for Jinja2 template variable names in preflight tasks.  ansible** (1 connections) — `tests/unit/test_template_variable_names.py`
- **Host leaves must appear under a running task whose preflight         name has {{** (1 connections) — `tests/unit/test_template_variable_names.py`
- **A task with {{ variable }} in preflight must not appear twice         in the tre** (1 connections) — `tests/unit/test_template_variable_names.py`
- **A role task with {{ variable }} must match the resolved runtime         name and** (1 connections) — `tests/unit/test_template_variable_names.py`
- **A preflight task with {{ variable }} that has completed at         runtime must** (1 connections) — `tests/unit/test_template_variable_names.py`
- **Preflight tasks with {{ variable }} must match resolved runtime names.** (1 connections) — `tests/unit/test_template_variable_names.py`
- **A preflight task 'Get ID for {{ user }}' must match the runtime         task 'Ge** (1 connections) — `tests/unit/test_template_variable_names.py`

## Relationships

- [[Play Definition Tree Population]] (7 shared connections)
- [[Run State Summary Panel]] (6 shared connections)
- [[Task Definition Live Refresh]] (2 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Run State Completion Recap]] (2 shared connections)
- [[Tree Projection Logic]] (1 shared connections)

## Source Files

- `tests/unit/test_template_variable_names.py`

## Audit Trail

- EXTRACTED: 56 (80%)
- INFERRED: 14 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*