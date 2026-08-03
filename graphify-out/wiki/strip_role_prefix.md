# strip_role_prefix

> 19 nodes · cohesion 0.12

## Key Concepts

- **strip_role_prefix()** (15 connections) — `src/ansible_aom/core/models.py`
- **._graft_or_match_task()** (11 connections) — `src/ansible_aom/core/run_state.py`
- **._graft_role_pending_siblings()** (8 connections) — `src/ansible_aom/core/run_state.py`
- **_is_template_match()** (8 connections) — `src/ansible_aom/core/tree_projection.py`
- **._task_role()** (7 connections) — `src/ansible_aom/core/tree_projection.py`
- **._bump_tree_revision()** (5 connections) — `src/ansible_aom/core/run_state.py`
- **.add()** (3 connections) — `src/ansible_aom/core/run_state.py`
- **_extract_role_from_include_stub()** (3 connections) — `src/ansible_aom/core/run_state.py`
- **.test_empty_skeleton_against_itself_returns_false()** (3 connections) — `tests/unit/test_template_variable_names.py`
- **.test_empty_skeleton_is_template_match_returns_false()** (3 connections) — `tests/unit/test_template_variable_names.py`
- **Strip the ``"role : "`` prefix that ansible adds to task names at     runtime. P** (1 connections) — `src/ansible_aom/core/models.py`
- **Advance the private tree-shape revision counter.          TreeProjection instanc** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Extract the target role from an ``include_role`` / ``import_role`` stub name.** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Update the dynamic-expansion cursor for an arriving task.          Matches the r** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Graft every other task of *role_name* as a sibling of the         just-grafted c** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Return True if ``runtime_name`` could be a resolved version of     ``preflight_n** (1 connections) — `src/ansible_aom/core/tree_projection.py`
- **Return the full role path a task belongs to, or ``()``.          Preflight ``--l** (1 connections) — `src/ansible_aom/core/tree_projection.py`
- **Direct unit test: ``_is_template_match("{{ var }}", "Plain task A")``         mu** (1 connections) — `tests/unit/test_template_variable_names.py`
- **Direct unit test: ``_is_template_match("{{ var }}", "{{ var }}")``         must** (1 connections) — `tests/unit/test_template_variable_names.py`

## Relationships

- [TreeProjection](TreeProjection.md) (11 shared connections)
- [RunState](RunState.md) (6 shared connections)
- [tree.py](tree.py.md) (5 shared connections)
- [json.py](json.py.md) (3 shared connections)
- [_discover_role](_discover_role.md) (2 shared connections)
- [TaskDefinition](TaskDefinition.md) (2 shared connections)
- [TestTemplateVariableNameMismatch](TestTemplateVariableNameMismatch.md) (2 shared connections)
- [IncludeCacheEntry](IncludeCacheEntry.md) (1 shared connections)
- [HostRunState](HostRunState.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/run_state.py`
- `src/ansible_aom/core/tree_projection.py`
- `tests/unit/test_template_variable_names.py`

## Audit Trail

- EXTRACTED: 71 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*