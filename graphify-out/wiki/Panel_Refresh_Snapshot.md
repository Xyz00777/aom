# Panel Refresh Snapshot

> 11 nodes · cohesion 0.18

## Key Concepts

- **._render_status_panel()** (14 connections) — `src/ansible_aom/compact/renderer.py`
- **._capture_panel_snapshot()** (7 connections) — `src/ansible_aom/compact/renderer.py`
- **_compute_tree_budget()** (6 connections) — `src/ansible_aom/compact/format.py`
- **._render_status_bar()** (3 connections) — `src/ansible_aom/compact/renderer.py`
- **.tick()** (3 connections) — `src/ansible_aom/compact/renderer.py`
- **test_compute_tree_budget_math()** (2 connections) — `tests/compact/test_tree_render.py`
- **Tree height budget in lines.      Baseline ~½ of terminal rows; +1 line per 3 ac** (1 connections) — `src/ansible_aom/compact/format.py`
- **Refresh the status panel without processing an event.          The runner calls** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Compute and push the current panel (status bar + tree + hosts).          Compose** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Deprecated alias — kept for any test references that still call         the old** (1 connections) — `src/ansible_aom/compact/renderer.py`
- **Render the current tree and host overview as static lines.          Returns a ``** (1 connections) — `src/ansible_aom/compact/renderer.py`

## Relationships

- [[Compact Renderer Implementation]] (4 shared connections)
- [[Event Log Emission]] (3 shared connections)
- [[Tree Render Snapshot Tests]] (2 shared connections)
- [[Host Overview Table]] (2 shared connections)
- [[Tree Block Animation]] (2 shared connections)
- [[Total Task Counting]] (2 shared connections)
- [[Play Definition Tree Population]] (2 shared connections)
- [[Color ASCII Fallback]] (2 shared connections)
- [[Compact Renderer Formatters]] (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`
- `tests/compact/test_tree_render.py`

## Audit Trail

- EXTRACTED: 26 (65%)
- INFERRED: 14 (35%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*