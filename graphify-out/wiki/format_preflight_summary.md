# format_preflight_summary

> 23 nodes · cohesion 0.17

## Key Concepts

- **format_preflight_summary()** (22 connections) — `src/ansible_aom/compact/format.py`
- **test_preflight_summary.py** (15 connections) — `tests/compact/test_preflight_summary.py`
- **collect_tags()** (10 connections) — `src/ansible_aom/compact/format.py`
- **_td()** (7 connections) — `tests/compact/test_preflight_summary.py`
- **_td_tagged()** (7 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_counts_role_grouped_tasks()** (6 connections) — `tests/compact/test_preflight_summary.py`
- **test_collect_tags_handles_role_group_definition()** (5 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_handles_no_resolved_hosts()** (5 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_pluralization()** (5 connections) — `tests/compact/test_preflight_summary.py`
- **test_collect_tags_empty_when_no_tags()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_collect_tags_unique_sorted_across_plays()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_appends_tag_line_when_tags_present()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_multi_play()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_omits_tag_line_when_no_tags()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_single_play()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **_collect_role_group_tags()** (3 connections) — `src/ansible_aom/compact/format.py`
- **Render a one-shot startup summary of plays/tasks/hosts from preflight.      Prin** (2 connections) — `src/ansible_aom/compact/format.py`
- **test_format_preflight_summary_empty_returns_none()** (2 connections) — `tests/compact/test_preflight_summary.py`
- **Unique tags across every leaf TaskDefinition, alphabetically sorted.      Used f** (1 connections) — `src/ansible_aom/compact/format.py`
- **Tests for format_preflight_summary — startup tree preview.** (1 connections) — `tests/compact/test_preflight_summary.py`
- **When --list-hosts failed for a play, resolved_hosts is empty.** (1 connections) — `tests/compact/test_preflight_summary.py`
- **1 host vs N hosts; 1 task vs N tasks.** (1 connections) — `tests/compact/test_preflight_summary.py`
- **RoleGroupDefinition should contribute its inner task count.** (1 connections) — `tests/compact/test_preflight_summary.py`

## Relationships

- [PlayDefinition](PlayDefinition.md) (13 shared connections)
- [TaskDefinition](TaskDefinition.md) (6 shared connections)
- [renderer.py](renderer.py.md) (5 shared connections)
- [PriorRun](PriorRun.md) (5 shared connections)
- [format_age](format_age.md) (2 shared connections)
- [HostRunState](HostRunState.md) (2 shared connections)
- [._emit_event_log](_emit_event_log.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_preflight_summary.py`

## Audit Trail

- EXTRACTED: 95 (81%)
- INFERRED: 23 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*