# build_verbose_lines

> 16 nodes · cohesion 0.21

## Key Concepts

- **build_verbose_lines()** (14 connections) — `src/ansible_aom/core/inspect_model.py`
- **task_ids_by_play()** (13 connections) — `src/ansible_aom/core/inspect_model.py`
- **query_verbose()** (11 connections) — `src/ansible_aom/session/index.py`
- **test_inspect_model_verbose.py** (7 connections) — `tests/unit/test_inspect_model_verbose.py`
- **test_build_verbose_lines_uses_precomputed_memberships()** (7 connections) — `tests/unit/test_inspect_model_verbose.py`
- **._render_verbose_placeholder()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **_session_with_verbose_events()** (5 connections) — `tests/unit/test_inspect_model_verbose.py`
- **test_task_ids_by_play_from_prebuilt_tree()** (4 connections) — `tests/unit/test_inspect_model_verbose.py`
- **test_build_verbose_lines_filters_by_scope()** (3 connections) — `tests/unit/test_inspect_model_verbose.py`
- **test_build_verbose_lines_ignores_unmatched_play_task_lines()** (3 connections) — `tests/unit/test_inspect_model_verbose.py`
- **Return ``play_name -> task_id`` membership from an already-built tree.      Call** (1 connections) — `src/ansible_aom/core/inspect_model.py`
- **Build the verbose-panel body for one session dict and focus scope.      In-memor** (1 connections) — `src/ansible_aom/core/inspect_model.py`
- **Verbose lines for a focus scope, filtered inside sqlite.      The WHERE clauses** (1 connections) — `src/ansible_aom/session/index.py`
- **MonkeyPatch** (1 connections)
- **Unit tests for verbose-panel session filtering.** (1 connections) — `tests/unit/test_inspect_model_verbose.py`
- **With ``play_task_ids`` supplied, the task tree is NOT rebuilt.** (1 connections) — `tests/unit/test_inspect_model_verbose.py`

## Relationships

- [inspect_model.py](inspect_model.py.md) (6 shared connections)
- [text.py](text.py.md) (6 shared connections)
- [index.py](index.py.md) (6 shared connections)
- [TaskTreeNode](TaskTreeNode.md) (4 shared connections)
- [inspect.py](inspect.py.md) (3 shared connections)
- [StatusCounts](StatusCounts.md) (3 shared connections)
- [InspectApp](InspectApp.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `src/ansible_aom/session/index.py`
- `src/ansible_aom/tui/screens/inspect.py`
- `tests/unit/test_inspect_model_verbose.py`

## Audit Trail

- EXTRACTED: 79 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*