# Run State Completion Recap

> 240 nodes · cohesion 0.01

## Key Concepts

- **HostRunState** (309 connections) — `src/ansible_aom/core/models.py`
- **PlayRunState** (278 connections) — `src/ansible_aom/core/models.py`
- **TaskRunState** (269 connections) — `src/ansible_aom/core/models.py`
- **TestHostRunState** (23 connections) — `tests/unit/test_models.py`
- **TestPlayRunState** (23 connections) — `tests/unit/test_models.py`
- **TestTaskRunState** (21 connections) — `tests/unit/test_models.py`
- **TestTreeViewHierarchyStructure** (19 connections) — `tests/tui/test_tree_view.py`
- **TestMemoryBounds** (18 connections) — `tests/unit/test_models.py`
- **TestExitCodes** (17 connections) — `tests/integration/test_compact_renderer.py`
- **test_task_progress.py** (15 connections) — `tests/compact/test_task_progress.py`
- **TestTreeViewReactiveUpdates** (15 connections) — `tests/tui/test_tree_view.py`
- **TestExitCode1** (14 connections) — `tests/unit/test_cli.py`
- **TestExitCode2** (14 connections) — `tests/unit/test_cli.py`
- **count_completed_tasks()** (13 connections) — `src/ansible_aom/compact/format.py`
- **TestTreeViewHostDisplay** (13 connections) — `tests/tui/test_tree_view.py`
- **_spur_projection()** (12 connections) — `tests/compact/test_tree_pipe_continuation.py`
- **test_tree_upcoming_plays.py** (12 connections) — `tests/compact/test_tree_upcoming_plays.py`
- **TestSummaryPanelDataAggregation** (12 connections) — `tests/tui/test_panels.py`
- **test_format_tree_block_renders_two_level_truncation()** (11 connections) — `tests/compact/test_tree_render.py`
- **_visible_projection()** (11 connections) — `tests/compact/test_tree_render.py`
- **TestHostRowsCurrentTask** (11 connections) — `tests/unit/test_stale_running_cleanup.py`
- **TestHandleCompletionRecap** (10 connections) — `tests/compact/test_completion_recap.py`
- **_state_first_play_running()** (10 connections) — `tests/compact/test_tree_upcoming_plays.py`
- **_state_with_failure()** (9 connections) — `tests/compact/test_completion_recap.py`
- **_running_state()** (9 connections) — `tests/compact/test_spinner_animation.py`
- *... and 215 more nodes in this community*

## Relationships

- [[Run State Summary Panel]] (146 shared connections)
- [[Role Group Task Models]] (118 shared connections)
- [[Play Definition Tree Population]] (86 shared connections)
- [[Status Bar Warning Panels]] (82 shared connections)
- [[Task Definition Live Refresh]] (67 shared connections)
- [[Compact Renderer Integration Tests]] (55 shared connections)
- [[CLI Interface Tests]] (53 shared connections)
- [[TUI Tree View Tests]] (28 shared connections)
- [[Tree Block Animation]] (23 shared connections)
- [[Data Model Unit Tests]] (18 shared connections)
- [[Failure Recap Formatting]] (16 shared connections)
- [[Host Overview Table]] (15 shared connections)

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
- `tests/tui/test_tree_view.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_dynamic_counters.py`
- `tests/unit/test_json_renderer.py`
- `tests/unit/test_models.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_stale_running_cleanup.py`

## Audit Trail

- EXTRACTED: 601 (34%)
- INFERRED: 1192 (66%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*