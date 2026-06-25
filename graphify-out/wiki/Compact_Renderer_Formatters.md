# Compact Renderer Formatters

> 18 nodes · cohesion 0.14

## Key Concepts

- **format.py** (23 connections) — `src/ansible_aom/compact/format.py`
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
- **Format the status bar for compact mode display.      Args:         playbook: Pat** (1 connections) — `src/ansible_aom/compact/format.py`
- **Render non-zero status count cells.      Order: ok, changed, skipped, failed, un** (1 connections) — `src/ansible_aom/compact/format.py`
- **Format a host summary line with status icons.      Only includes non-zero counts** (1 connections) — `src/ansible_aom/compact/format.py`
- **Right-align ``value`` in a fixed-width cell; dim zero values.      A literal zer** (1 connections) — `src/ansible_aom/compact/format.py`
- **``text`` wrapped in an SGR sequence, or plain ``text`` if not colorising.** (1 connections) — `src/ansible_aom/compact/format.py`
- **Truncate to `width` visible chars while preserving any open SGR     state by app** (1 connections) — `src/ansible_aom/compact/format.py`
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

- EXTRACTED: 71 (85%)
- INFERRED: 13 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*