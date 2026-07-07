# Preflight Summary Rendering

> 26 nodes · cohesion 0.14

## Key Concepts

- **format_preflight_summary()** (20 connections) — `src/ansible_aom/compact/format.py`
- **test_preflight_summary.py** (14 connections) — `tests/compact/test_preflight_summary.py`
- **_td()** (7 connections) — `tests/compact/test_preflight_summary.py`
- **_td_tagged()** (7 connections) — `tests/compact/test_preflight_summary.py`
- **_play()** (7 connections) — `tests/compact/test_prior_run_line.py`
- **test_format_preflight_summary_counts_role_grouped_tasks()** (6 connections) — `tests/compact/test_preflight_summary.py`
- **test_prior_run_line.py** (6 connections) — `tests/compact/test_prior_run_line.py`
- **test_collect_tags_handles_role_group_definition()** (5 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_handles_no_resolved_hosts()** (5 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_pluralization()** (5 connections) — `tests/compact/test_preflight_summary.py`
- **test_collect_tags_empty_when_no_tags()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_collect_tags_unique_sorted_across_plays()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_appends_tag_line_when_tags_present()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_multi_play()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_omits_tag_line_when_no_tags()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_single_play()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_prior_run_line_hours_format()** (4 connections) — `tests/compact/test_prior_run_line.py`
- **test_prior_run_line_seconds_only_under_a_minute()** (4 connections) — `tests/compact/test_prior_run_line.py`
- **test_prior_run_line_shown_when_prior_exists()** (4 connections) — `tests/compact/test_prior_run_line.py`
- **test_prior_run_line_is_omitted_when_none()** (3 connections) — `tests/compact/test_prior_run_line.py`
- **test_format_preflight_summary_empty_returns_none()** (2 connections) — `tests/compact/test_preflight_summary.py`
- **Tests for format_preflight_summary — startup tree preview.** (1 connections) — `tests/compact/test_preflight_summary.py`
- **When --list-hosts failed for a play, resolved_hosts is empty.** (1 connections) — `tests/compact/test_preflight_summary.py`
- **1 host vs N hosts; 1 task vs N tasks.** (1 connections) — `tests/compact/test_preflight_summary.py`
- **RoleGroupDefinition should contribute its inner task count.** (1 connections) — `tests/compact/test_preflight_summary.py`
- *... and 1 more nodes in this community*

## Relationships

- [[Play Definition Tree Population]] (12 shared connections)
- [[Compact Renderer Formatters]] (5 shared connections)
- [[Task Definition Live Refresh]] (3 shared connections)
- [[Run History Mining]] (3 shared connections)
- [[Duration Formatting Helpers]] (2 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Total Task Counting]] (1 shared connections)
- [[Event Log Emission]] (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_preflight_summary.py`
- `tests/compact/test_prior_run_line.py`

## Audit Trail

- EXTRACTED: 82 (64%)
- INFERRED: 46 (36%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*