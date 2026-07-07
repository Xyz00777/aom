# Host Overview Table

> 20 nodes · cohesion 0.26

## Key Concepts

- **format_host_rows()** (26 connections) — `src/ansible_aom/compact/format.py`
- **_strip_sgr()** (16 connections) — `src/ansible_aom/compact/format.py`
- **test_host_table.py** (15 connections) — `tests/compact/test_host_table.py`
- **_state()** (14 connections) — `tests/compact/test_host_table.py`
- **_add_results()** (13 connections) — `tests/compact/test_host_table.py`
- **test_failed_host_shows_failed_task_in_suffix()** (8 connections) — `tests/compact/test_host_table.py`
- **test_failed_host_shows_X_in_ascii_mode()** (8 connections) — `tests/compact/test_host_table.py`
- **test_running_host_shows_current_task()** (8 connections) — `tests/compact/test_host_table.py`
- **test_unreachable_host_shows_unreachable_task_in_suffix()** (8 connections) — `tests/compact/test_host_table.py`
- **test_columns_align_across_rows()** (6 connections) — `tests/compact/test_host_table.py`
- **test_header_row_present()** (6 connections) — `tests/compact/test_host_table.py`
- **test_idle_host_shows_idle_marker()** (6 connections) — `tests/compact/test_host_table.py`
- **test_skipped_column_hidden_when_no_skipped()** (6 connections) — `tests/compact/test_host_table.py`
- **test_skipped_column_visible_when_any_host_has_skipped()** (6 connections) — `tests/compact/test_host_table.py`
- **test_unreachable_column_hidden_when_no_unreachable()** (6 connections) — `tests/compact/test_host_table.py`
- **test_unreachable_column_visible_when_any_host_has_unreachable()** (6 connections) — `tests/compact/test_host_table.py`
- **_rows()** (3 connections) — `tests/compact/test_host_table.py`
- **Per-host overview renders as a column-aligned table rather than a flat row of co** (1 connections) — `tests/compact/test_host_table.py`
- **Synthesise OK/CHANGED/SKIPPED/FAILED/UNREACHABLE results for a host.** (1 connections) — `tests/compact/test_host_table.py`
- **Split rows on whitespace runs after stripping SGR — coarse but     enough to ass** (1 connections) — `tests/compact/test_host_table.py`

## Relationships

- [[Run State Completion Recap]] (15 shared connections)
- [[Compact Renderer Formatters]] (5 shared connections)
- [[Tree Render Snapshot Tests]] (5 shared connections)
- [[Panel Refresh Snapshot]] (2 shared connections)
- [[Running Animation Frames]] (1 shared connections)
- [[Tree Block Animation]] (1 shared connections)
- [[Play Definition Tree Population]] (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_host_table.py`

## Audit Trail

- EXTRACTED: 94 (57%)
- INFERRED: 70 (43%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*