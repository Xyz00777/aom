# Runtime Event Handlers

> 16 nodes · cohesion 0.33

## Key Concepts

- **test_full_completion_summary.py** (14 connections) — `tests/compact/test_full_completion_summary.py`
- **_logged()** (8 connections) — `tests/compact/test_full_completion_summary.py`
- **_renderer()** (8 connections) — `tests/compact/test_full_completion_summary.py`
- **_summary_lines()** (7 connections) — `tests/compact/test_full_completion_summary.py`
- **test_cancel_flushes_incomplete_task_with_partial_count()** (7 connections) — `tests/compact/test_full_completion_summary.py`
- **test_completed_task_summary_emitted_once()** (7 connections) — `tests/compact/test_full_completion_summary.py`
- **_start()** (6 connections) — `tests/compact/test_full_completion_summary.py`
- **test_free_strategy_summary_counts_all_targets_not_fast_cohort()** (6 connections) — `tests/compact/test_full_completion_summary.py`
- **test_purely_inflight_task_gets_no_summary_at_cancel()** (6 connections) — `tests/compact/test_full_completion_summary.py`
- **_ok()** (5 connections) — `tests/compact/test_full_completion_summary.py`
- **test_free_strategy_summary_lands_after_later_task_header()** (5 connections) — `tests/compact/test_full_completion_summary.py`
- **_play_def()** (3 connections) — `tests/compact/test_full_completion_summary.py`
- **Per-task summary fires on FULL play completion, not on the next task.  Under a f** (1 connections) — `tests/compact/test_full_completion_summary.py`
- **A task with zero terminal results at cancel produces no summary —     a bare ``—** (1 connections) — `tests/compact/test_full_completion_summary.py`
- **A task summarised mid-run is not re-emitted at cancel/stats.** (1 connections) — `tests/compact/test_full_completion_summary.py`
- **A task that never completes on all hosts (run cancelled) still gets     a summar** (1 connections) — `tests/compact/test_full_completion_summary.py`

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (3 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (1 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (1 shared connections)

## Source Files

- `tests/compact/test_full_completion_summary.py`

## Audit Trail

- EXTRACTED: 86 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*