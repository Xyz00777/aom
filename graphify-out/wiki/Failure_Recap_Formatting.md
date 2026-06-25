# Failure Recap Formatting

> 13 nodes · cohesion 0.24

## Key Concepts

- **format_failure_recap()** (14 connections) — `src/ansible_aom/compact/format.py`
- **TestFormatFailureRecap** (13 connections) — `tests/compact/test_completion_recap.py`
- **TestFailureRecapColors** (12 connections) — `tests/compact/test_status_bar_colors.py`
- **._state_with()** (9 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_empty_state_returns_no_lines()** (3 connections) — `tests/compact/test_completion_recap.py`
- **.test_failed_label_is_visible()** (3 connections) — `tests/compact/test_completion_recap.py`
- **.test_failure_recap_names_host_and_task()** (3 connections) — `tests/compact/test_completion_recap.py`
- **.test_no_failures_returns_no_lines()** (3 connections) — `tests/compact/test_completion_recap.py`
- **.test_unreachable_is_recapped_separately_from_failed()** (3 connections) — `tests/compact/test_completion_recap.py`
- **.test_failed_label_is_red()** (3 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_no_color_by_default()** (3 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_unreachable_label_is_magenta()** (3 connections) — `tests/compact/test_status_bar_colors.py`
- **Recap line labels carry the same colour as the per-host count.** (1 connections) — `tests/compact/test_status_bar_colors.py`

## Relationships

- [[Run State Completion Recap]] (16 shared connections)
- [[Run State Summary Panel]] (5 shared connections)
- [[Role Group Task Models]] (3 shared connections)
- [[Compact Renderer Formatters]] (2 shared connections)
- [[Compact Renderer Implementation]] (2 shared connections)
- [[Total Task Counting]] (1 shared connections)
- [[Status Bar Color Tests]] (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_completion_recap.py`
- `tests/compact/test_status_bar_colors.py`

## Audit Trail

- EXTRACTED: 40 (55%)
- INFERRED: 33 (45%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*