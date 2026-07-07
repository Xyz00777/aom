# Compact Renderer Formatters

> 12 nodes · cohesion 0.14

## Key Concepts

- **format.py** (24 connections) — `src/ansible_aom/compact/format.py`
- **_wrap()** (17 connections) — `src/ansible_aom/compact/format.py`
- **collect_tags()** (8 connections) — `src/ansible_aom/compact/format.py`
- **format_status_bar()** (5 connections) — `src/ansible_aom/compact/format.py`
- **_truncate_visible()** (5 connections) — `src/ansible_aom/compact/format.py`
- **_count_cell()** (4 connections) — `src/ansible_aom/compact/format.py`
- **_format_count_cells()** (4 connections) — `src/ansible_aom/compact/format.py`
- **format_host_summary()** (4 connections) — `src/ansible_aom/compact/format.py`
- **_collect_role_group_tags()** (3 connections) — `src/ansible_aom/compact/format.py`
- **test_truncate_visible_plain_mode_emits_no_sgr()** (3 connections) — `tests/compact/test_tree_render.py`
- **Pure formatters for the compact renderer.  Every public function here takes doma** (1 connections) — `src/ansible_aom/compact/format.py`
- **Regression guard: when colorize=False, `_truncate_visible` must     not inject `** (1 connections) — `tests/compact/test_tree_render.py`

## Relationships

- [[Event Log Emission]] (7 shared connections)
- [[Host Overview Table]] (5 shared connections)
- [[Preflight Summary Rendering]] (5 shared connections)
- [[Total Task Counting]] (4 shared connections)
- [[Tree Block Animation]] (3 shared connections)
- [[Check Mode Chip]] (2 shared connections)
- [[Failure Recap Formatting]] (2 shared connections)
- [[Color ASCII Fallback]] (1 shared connections)
- [[Panel Refresh Snapshot]] (1 shared connections)
- [[Run State Completion Recap]] (1 shared connections)
- [[Role Group Task Models]] (1 shared connections)
- [[Play Definition Tree Population]] (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_tree_render.py`

## Audit Trail

- EXTRACTED: 66 (84%)
- INFERRED: 13 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*