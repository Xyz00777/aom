# ._render_status_panel

> 41 nodes · cohesion 0.06

## Key Concepts

- **._render_status_panel()** (18 connections) — `src/ansible_aom/compact/renderer.py`
- **count_total_tasks()** (17 connections) — `src/ansible_aom/compact/format.py`
- **test_task_progress.py** (17 connections) — `tests/compact/test_task_progress.py`
- **.handle_completion()** (13 connections) — `src/ansible_aom/compact/renderer.py`
- **count_total_tasks_seen()** (12 connections) — `src/ansible_aom/compact/format.py`
- **run_state_status_counts()** (10 connections) — `src/ansible_aom/core/tree.py`
- **test_count_total_tasks_grows_with_runtime_announced_tasks()** (8 connections) — `tests/compact/test_task_progress.py`
- **test_handle_completion_keeps_runtime_grown_denominator()** (8 connections) — `tests/compact/test_task_progress.py`
- **_compute_tree_budget()** (7 connections) — `src/ansible_aom/compact/format.py`
- **._capture_panel_snapshot()** (7 connections) — `src/ansible_aom/compact/renderer.py`
- **_task()** (7 connections) — `tests/compact/test_task_progress.py`
- **test_count_total_tasks_seen_falls_back_to_preflight_before_any_announce()** (6 connections) — `tests/compact/test_task_progress.py`
- **test_renderer_status_bar_reflects_task_progress()** (5 connections) — `tests/compact/test_task_progress.py`
- **._cached_count_total_tasks()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **._task_total_with_prior()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **test_count_total_tasks_sums_across_plays()** (4 connections) — `tests/compact/test_task_progress.py`
- **._render_status_bar()** (3 connections) — `src/ansible_aom/compact/renderer.py`
- **.tick()** (3 connections) — `src/ansible_aom/compact/renderer.py`
- **test_format_status_bar_omits_tasks_when_total_zero()** (3 connections) — `tests/compact/test_task_progress.py`
- **test_format_status_bar_task_progress_defaults_to_zero()** (3 connections) — `tests/compact/test_task_progress.py`
- **test_total_tasks_empty_definitions()** (3 connections) — `tests/unit/test_dynamic_counters.py`
- **test_count_total_tasks_empty()** (2 connections) — `tests/compact/test_task_progress.py`
- **test_format_status_bar_includes_task_progress_when_total_set()** (2 connections) — `tests/compact/test_task_progress.py`
- **Tree height budget in lines.      Baseline ~½ of terminal rows; +1 line per 3 ac** (1 connections) — `src/ansible_aom/compact/format.py`
- **Sum of leaf tasks across all preflight play definitions.      Used for the statu** (1 connections) — `src/ansible_aom/compact/format.py`
- *... and 16 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (22 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (9 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (9 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (7 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (6 shared connections)
- [Renderer Event Protocol](Renderer_Event_Protocol.md) (5 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (4 shared connections)
- [Four-Layer Redaction System](Four-Layer_Redaction_System.md) (2 shared connections)
- [RunState Property Invariants](RunState_Property_Invariants.md) (2 shared connections)
- [Pause Prompt Heuristic](Pause_Prompt_Heuristic.md) (2 shared connections)
- [Renderer Stats Parity](Renderer_Stats_Parity.md) (2 shared connections)
- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (2 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`
- `src/ansible_aom/core/tree.py`
- `tests/compact/test_task_progress.py`
- `tests/unit/test_dynamic_counters.py`

## Audit Trail

- EXTRACTED: 125 (68%)
- INFERRED: 59 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*