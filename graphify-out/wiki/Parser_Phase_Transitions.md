# Parser Phase Transitions

> 22 nodes · cohesion 0.25

## Key Concepts

- **test_skipped_collapsing.py** (10 connections) — `tests/compact/test_skipped_collapsing.py`
- **_logged()** (10 connections) — `tests/compact/test_skipped_collapsing.py`
- **_renderer()** (10 connections) — `tests/compact/test_skipped_collapsing.py`
- **_skipped()** (9 connections) — `tests/compact/test_skipped_collapsing.py`
- **_task_start()** (9 connections) — `tests/compact/test_skipped_collapsing.py`
- **TestAllSkippedCollapsing** (7 connections) — `tests/compact/test_skipped_collapsing.py`
- **.test_collapse_at_stats_for_final_task()** (7 connections) — `tests/compact/test_skipped_collapsing.py`
- **.test_ok_then_skipped_only_flushed_at_transition()** (7 connections) — `tests/compact/test_skipped_collapsing.py`
- **.test_collapsing_state_does_not_leak_to_next_task()** (7 connections) — `tests/compact/test_skipped_collapsing.py`
- **.test_skipped_then_ok_expands_skipped_lines()** (6 connections) — `tests/compact/test_skipped_collapsing.py`
- **.test_compressed_line_is_cyan()** (5 connections) — `tests/compact/test_skipped_collapsing.py`
- **.test_many_hosts_shows_count_only()** (5 connections) — `tests/compact/test_skipped_collapsing.py`
- **.test_single_skipped_host_singular_form()** (5 connections) — `tests/compact/test_skipped_collapsing.py`
- **.test_three_or_fewer_hosts_lists_names()** (5 connections) — `tests/compact/test_skipped_collapsing.py`
- **_ok()** (4 connections) — `tests/compact/test_skipped_collapsing.py`
- **TestMixedTaskExpandsIndividually** (4 connections) — `tests/compact/test_skipped_collapsing.py`
- **TestStateResetBetweenTasks** (3 connections) — `tests/compact/test_skipped_collapsing.py`
- **_stats()** (2 connections) — `tests/compact/test_skipped_collapsing.py`
- **Tests for skipped-task collapsing.  When a task produces only ``skipped`` result** (1 connections) — `tests/compact/test_skipped_collapsing.py`
- **The very last task can't be flushed by a next task_start;         the stats even** (1 connections) — `tests/compact/test_skipped_collapsing.py`
- **ok arrives first, then skipped — those skipped land at the         next task tra** (1 connections) — `tests/compact/test_skipped_collapsing.py`
- **All-skipped task A followed by mixed task B: B must         flush its own skips** (1 connections) — `tests/compact/test_skipped_collapsing.py`

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (5 shared connections)

## Source Files

- `tests/compact/test_skipped_collapsing.py`

## Audit Trail

- EXTRACTED: 116 (97%)
- INFERRED: 3 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*