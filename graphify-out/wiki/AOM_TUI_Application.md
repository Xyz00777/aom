# AOM TUI Application

> 32 nodes · cohesion 0.11

## Key Concepts

- **_play_start()** (15 connections) — `tests/unit/test_runner_event_fallback.py`
- **_task_start()** (15 connections) — `tests/unit/test_runner_event_fallback.py`
- **TestTaskStartHostSynthesisFallback** (10 connections) — `tests/unit/test_runner_event_fallback.py`
- **TestTerminalEventFallbackAttribution** (10 connections) — `tests/unit/test_runner_event_fallback.py`
- **test_runner_event_fallback.py** (9 connections) — `tests/unit/test_runner_event_fallback.py`
- **TestTreeReflectsPartialCompletion** (7 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_tree_shows_per_host_status_when_subset_completed()** (7 connections) — `tests/unit/test_runner_event_fallback.py`
- **TestUnmatchedEventCounter** (7 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_preflight_resolved_hosts_still_win()** (6 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_no_synthesis_under_free_strategy()** (5 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_removed_hosts_excluded_from_synthesis()** (5 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_second_task_synthesises_hosts_from_prior_task()** (5 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_synthesised_hosts_purged_when_strategy_flips_to_free()** (5 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_failed_with_unknown_task_id_matches_by_name()** (5 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_name_fallback_prefers_running_task()** (5 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_ok_with_stale_play_id_lands_via_task_ownership()** (5 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_ok_with_unknown_task_id_matches_by_name()** (5 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_ok_with_unknown_task_id_matches_by_path()** (5 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_fully_unmatched_terminal_event_is_counted()** (4 connections) — `tests/unit/test_runner_event_fallback.py`
- **.test_matched_events_do_not_count_as_unmatched()** (4 connections) — `tests/unit/test_runner_event_fallback.py`
- **Terminal runner events must update host state even when ids mismatch.  Real-worl** (1 connections) — `tests/unit/test_runner_event_fallback.py`
- **The fallback must cover every terminal handler, not just ok.** (1 connections) — `tests/unit/test_runner_event_fallback.py`
- **An ok carrying a play.id we never saw must still land on the         task that o** (1 connections) — `tests/unit/test_runner_event_fallback.py`
- **Two same-named tasks in one play: the fallback must pick the         one still r** (1 connections) — `tests/unit/test_runner_event_fallback.py`
- **No preflight definitions (or no name match): the second         task_start under** (1 connections) — `tests/unit/test_runner_event_fallback.py`
- *... and 7 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (27 shared connections)
- [Hide State Gating Tests](Hide_State_Gating_Tests.md) (5 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (4 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)

## Source Files

- `tests/unit/test_runner_event_fallback.py`

## Audit Trail

- EXTRACTED: 135 (89%)
- INFERRED: 16 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*