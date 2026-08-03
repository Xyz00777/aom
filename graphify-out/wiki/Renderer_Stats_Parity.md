# Renderer Stats Parity

> 16 nodes · cohesion 0.20

## Key Concepts

- **count_completed_tasks()** (12 connections) — `src/ansible_aom/compact/format.py`
- **test_incremental_counters.py** (8 connections) — `tests/compact/test_incremental_counters.py`
- **.test_perf_030_counters_track_oracle()** (7 connections) — `tests/compact/test_incremental_counters.py`
- **_renderer()** (5 connections) — `tests/compact/test_incremental_counters.py`
- **TestIncrementalCounters** (5 connections) — `tests/compact/test_incremental_counters.py`
- **.test_completed_counter_not_double_counted()** (5 connections) — `tests/compact/test_incremental_counters.py`
- **_task_start()** (4 connections) — `tests/compact/test_incremental_counters.py`
- **.test_perf_031_dynamic_include_task_still_counts()** (4 connections) — `tests/compact/test_incremental_counters.py`
- **_runner_ok()** (3 connections) — `tests/compact/test_incremental_counters.py`
- **test_count_completed_tasks_empty_state()** (3 connections) — `tests/compact/test_task_progress.py`
- **_runner_failed()** (2 connections) — `tests/compact/test_incremental_counters.py`
- **Count tasks across all plays whose hosts have all reached terminal state.      T** (1 connections) — `src/ansible_aom/compact/format.py`
- **TC-PERF-030..031 — incremental task counters on CompactRenderer.  ``count_comple** (1 connections) — `tests/compact/test_incremental_counters.py`
- **After each event the incremental counter matches count_completed_tasks.** (1 connections) — `tests/compact/test_incremental_counters.py`
- **A task that arrives without preflight registration still increments.** (1 connections) — `tests/compact/test_incremental_counters.py`
- **Re-arriving terminal events for the same task don't double-count.** (1 connections) — `tests/compact/test_incremental_counters.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (3 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (3 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (2 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (2 shared connections)
- [._render_status_panel](_render_status_panel.md) (2 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (2 shared connections)
- [RunState Renderer Invariants](RunState_Renderer_Invariants.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `tests/compact/test_incremental_counters.py`
- `tests/compact/test_task_progress.py`

## Audit Trail

- EXTRACTED: 51 (81%)
- INFERRED: 12 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*