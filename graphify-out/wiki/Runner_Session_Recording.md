# Runner Session Recording

> 22 nodes · cohesion 0.16

## Key Concepts

- **TestTemplateVariableNameMismatch** (19 connections) — `tests/unit/test_template_variable_names.py`
- **_play_def()** (11 connections) — `tests/unit/test_template_variable_names.py`
- **_td()** (11 connections) — `tests/unit/test_template_variable_names.py`
- **test_template_variable_names.py** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_completed_template_task_dropped_from_tree()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_empty_skeleton_does_not_swallow_unrelated_task()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_host_leaf_under_resolved_template_task()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_no_duplicate_for_template_and_resolved_name()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_template_variable_in_middle_with_punctuation()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_template_variable_in_role_task()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_template_variable_with_punctuation_prefix()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **.test_template_variable_with_punctuation_suffix()** (6 connections) — `tests/unit/test_template_variable_names.py`
- **Regression tests for Jinja2 template variable names in preflight tasks.  ansible** (1 connections) — `tests/unit/test_template_variable_names.py`
- **Host leaves must appear under a running task whose preflight         name has {{** (1 connections) — `tests/unit/test_template_variable_names.py`
- **A task with {{ variable }} in preflight must not appear twice         in the tre** (1 connections) — `tests/unit/test_template_variable_names.py`
- **A role task with {{ variable }} must match the resolved runtime         name and** (1 connections) — `tests/unit/test_template_variable_names.py`
- **A preflight task with {{ variable }} that has completed at         runtime must** (1 connections) — `tests/unit/test_template_variable_names.py`
- **Regression: preflight name `Ensure {{ user }}'s home exists` must         match** (1 connections) — `tests/unit/test_template_variable_names.py`
- **Regression: preflight name `Deploy for {{ user }}!` must match         runtime n** (1 connections) — `tests/unit/test_template_variable_names.py`
- **Preflight tasks with {{ variable }} must match resolved runtime names.** (1 connections) — `tests/unit/test_template_variable_names.py`
- **Two template variables with no extra punctuation still match —         guards ag** (1 connections) — `tests/unit/test_template_variable_names.py`
- **Regression: a preflight task whose name is entirely a Jinja         template (e.** (1 connections) — `tests/unit/test_template_variable_names.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (24 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (2 shared connections)
- [Hide State Gating Tests](Hide_State_Gating_Tests.md) (2 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [tree.py](tree.py.md) (1 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)

## Source Files

- `tests/unit/test_template_variable_names.py`

## Audit Trail

- EXTRACTED: 90 (86%)
- INFERRED: 15 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*