# Task Tree Navigation

> 10 nodes · cohesion 0.33

## Key Concepts

- **TaskTreeNode** (18 connections) — `src/ansible_aom/core/inspect_model.py`
- **._failure_pairs()** (7 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._focus_failure_at()** (6 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._add_node()** (5 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.action_next_failure()** (4 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **.action_prev_failure()** (4 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._current_failure_index()** (4 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._iter_failures()** (3 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **._should_auto_expand()** (3 connections) — `src/ansible_aom/tui/screens/inspect.py`
- **Hierarchical view of a session's tasks.      Levels: run → play → group → task →** (1 connections) — `src/ansible_aom/core/inspect_model.py`

## Relationships

- [[Three-Pane Inspect App]] (9 shared connections)
- [[Inspect TUI Widget Data]] (7 shared connections)
- [[Inspect Data Model Builders]] (3 shared connections)
- [[Inspect Text Golden Tests]] (2 shared connections)
- [[Session List View]] (2 shared connections)
- [[Pane Focus Navigation]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `src/ansible_aom/tui/screens/inspect.py`

## Audit Trail

- EXTRACTED: 48 (87%)
- INFERRED: 7 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*