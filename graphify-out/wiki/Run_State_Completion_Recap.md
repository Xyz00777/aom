# Run State Completion Recap

> 189 nodes · cohesion 0.01

## Key Concepts

- **HostRunState** (308 connections) — `src/ansible_aom/core/models.py`
- **PlayRunState** (279 connections) — `src/ansible_aom/core/models.py`
- **TaskRunState** (266 connections) — `src/ansible_aom/core/models.py`
- **TestHostRunState** (22 connections) — `tests/unit/test_models.py`
- **TestPlayRunState** (22 connections) — `tests/unit/test_models.py`
- **TestTaskRunState** (20 connections) — `tests/unit/test_models.py`
- **TestMemoryBounds** (17 connections) — `tests/unit/test_models.py`
- **test_task_progress.py** (15 connections) — `tests/compact/test_task_progress.py`
- **TestExitCodes** (15 connections) — `tests/integration/test_compact_renderer.py`
- **TestExitCode1** (14 connections) — `tests/unit/test_cli.py`
- **TestExitCode2** (14 connections) — `tests/unit/test_cli.py`
- **count_completed_tasks()** (12 connections) — `src/ansible_aom/compact/format.py`
- **_spur_projection()** (12 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_tree_upcoming_plays.py** (12 connections) — `tests/compact/test_tree_upcoming_plays.py`
- **test_format_tree_block_renders_two_level_truncation()** (11 connections) — `tests/compact/test_tree_render.py`
- **_visible_projection()** (11 connections) — `tests/compact/test_tree_render.py`
- **TestSummaryPanelDataAggregation** (11 connections) — `tests/tui/test_panels.py`
- **TestHandleCompletionRecap** (10 connections) — `tests/compact/test_completion_recap.py`
- **_state_first_play_running()** (10 connections) — `tests/compact/test_tree_upcoming_plays.py`
- **_state_with_failure()** (9 connections) — `tests/compact/test_completion_recap.py`
- **_running_state()** (9 connections) — `tests/compact/test_spinner_animation.py`
- **_two_plays_with_running_tasks()** (9 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_completed_tasks_counts_dynamic_children()** (9 connections) — `tests/unit/test_dynamic_counters.py`
- **TestHostRowsCurrentTask** (9 connections) — `tests/unit/test_stale_running_cleanup.py`
- **test_count_total_tasks_grows_with_runtime_announced_tasks()** (8 connections) — `tests/compact/test_task_progress.py`
- *... and 164 more nodes in this community*

## Relationships

- [[Role Group Task Models]] (108 shared connections)
- [[Run State Summary Panel]] (84 shared connections)
- [[Status Bar Warning Panels]] (82 shared connections)
- [[Play Definition Tree Population]] (63 shared connections)
- [[Compact Renderer Integration Tests]] (55 shared connections)
- [[CLI Interface Tests]] (53 shared connections)
- [[Task Definition Live Refresh]] (52 shared connections)
- [[Tree Block Animation]] (23 shared connections)
- [[Data Model Unit Tests]] (18 shared connections)
- [[Failure Recap Formatting]] (16 shared connections)
- [[Host Overview Table]] (15 shared connections)
- [[JSON Renderer]] (10 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/core/models.py`
- `tests/compact/test_completion_recap.py`
- `tests/compact/test_spinner_animation.py`
- `tests/compact/test_task_progress.py`
- `tests/compact/test_tree_pipe_continuation.py`
- `tests/compact/test_tree_render.py`
- `tests/compact/test_tree_upcoming_plays.py`
- `tests/integration/test_compact_renderer.py`
- `tests/tui/test_panels.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_dynamic_counters.py`
- `tests/unit/test_json_renderer.py`
- `tests/unit/test_models.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_stale_running_cleanup.py`

## Audit Trail

- EXTRACTED: 503 (31%)
- INFERRED: 1137 (69%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*