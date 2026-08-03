# TUI Keybindings Config

> 60 nodes · cohesion 0.06

## Key Concepts

- **format.py** (60 connections) — `src/ansible_aom/compact/format.py`
- **PriorRun** (25 connections) — `src/ansible_aom/session/history.py`
- **format_preflight_summary()** (22 connections) — `src/ansible_aom/compact/format.py`
- **test_preflight_summary.py** (15 connections) — `tests/compact/test_preflight_summary.py`
- **collect_tags()** (10 connections) — `src/ansible_aom/compact/format.py`
- **test_prior_run_line.py** (10 connections) — `tests/compact/test_prior_run_line.py`
- **_count_tasks()** (8 connections) — `src/ansible_aom/compact/format.py`
- **_play()** (8 connections) — `tests/compact/test_prior_run_line.py`
- **_td()** (7 connections) — `tests/compact/test_preflight_summary.py`
- **_td_tagged()** (7 connections) — `tests/compact/test_preflight_summary.py`
- **test_invariants_runstate_renderer.py** (7 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **_truncate_visible()** (6 connections) — `src/ansible_aom/compact/format.py`
- **test_format_preflight_summary_counts_role_grouped_tasks()** (6 connections) — `tests/compact/test_preflight_summary.py`
- **test_status_bar_estimated_total.py** (6 connections) — `tests/compact/test_status_bar_estimated_total.py`
- **test_prior_run_loop_totals_injection.py** (6 connections) — `tests/unit/test_prior_run_loop_totals_injection.py`
- **_count_role_group_tasks()** (5 connections) — `src/ansible_aom/compact/format.py`
- **test_collect_tags_handles_role_group_definition()** (5 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_handles_no_resolved_hosts()** (5 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_pluralization()** (5 connections) — `tests/compact/test_preflight_summary.py`
- **test_prior_run_line_prefers_observed_over_preflight_count()** (5 connections) — `tests/compact/test_prior_run_line.py`
- **_bar()** (5 connections) — `tests/compact/test_status_bar_estimated_total.py`
- **TestCompactInjection** (5 connections) — `tests/unit/test_prior_run_loop_totals_injection.py`
- **test_collect_tags_empty_when_no_tags()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_collect_tags_unique_sorted_across_plays()** (4 connections) — `tests/compact/test_preflight_summary.py`
- **test_format_preflight_summary_appends_tag_line_when_tags_present()** (4 connections) — `tests/compact/test_preflight_summary.py`
- *... and 35 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (30 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (8 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (7 shared connections)
- [Property Based Tests](Property_Based_Tests.md) (6 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (6 shared connections)
- [Pause Prompt Heuristic](Pause_Prompt_Heuristic.md) (5 shared connections)
- [Source Hash Version](Source_Hash_Version.md) (5 shared connections)
- [._render_status_panel](_render_status_panel.md) (4 shared connections)
- [Session List View](Session_List_View.md) (4 shared connections)
- [RunState Property Invariants](RunState_Property_Invariants.md) (4 shared connections)
- [Renderer Event Protocol](Renderer_Event_Protocol.md) (4 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (4 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/session/history.py`
- `tests/compact/test_preflight_summary.py`
- `tests/compact/test_prior_run_line.py`
- `tests/compact/test_status_bar_estimated_total.py`
- `tests/unit/test_invariants_runstate_renderer.py`
- `tests/unit/test_prior_run_loop_totals_injection.py`

## Audit Trail

- EXTRACTED: 253 (78%)
- INFERRED: 72 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*