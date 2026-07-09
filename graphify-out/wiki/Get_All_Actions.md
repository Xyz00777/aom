# Get All Actions

> 18 nodes · cohesion 0.20

## Key Concepts

- **test_tree_event_replay.py** (11 connections) — `tests/compact/test_tree_event_replay.py`
- **_setup_state()** (10 connections) — `tests/compact/test_tree_event_replay.py`
- **test_tree_after_each_task_completion()** (8 connections) — `tests/compact/test_tree_event_replay.py`
- **test_tree_after_completion_no_race_window()** (7 connections) — `tests/compact/test_tree_event_replay.py`
- **test_tree_shrinks_under_budget_during_replay()** (7 connections) — `tests/compact/test_tree_event_replay.py`
- **_play_event()** (4 connections) — `tests/compact/test_tree_event_replay.py`
- **_runner_ok_event()** (4 connections) — `tests/compact/test_tree_event_replay.py`
- **_task_start_event()** (4 connections) — `tests/compact/test_tree_event_replay.py`
- **_list_tasks_event()** (2 connections) — `tests/compact/test_tree_event_replay.py`
- **_stats_event()** (2 connections) — `tests/compact/test_tree_event_replay.py`
- **tree_has_task()** (2 connections) — `tests/compact/test_tree_event_replay.py`
- **Tree correctness under incremental event replay.  Unlike synthetic-state tests t** (1 connections) — `tests/compact/test_tree_event_replay.py`
- **Check if a task name appears in the rendered tree block.** (1 connections) — `tests/compact/test_tree_event_replay.py`
- **Replay a 100-task linear playbook event stream, checking the tree for     comple** (1 connections) — `tests/compact/test_tree_event_replay.py`
- **Specifically test the window between last runner_on_ok and next     task_start:** (1 connections) — `tests/compact/test_tree_event_replay.py`
- **As tasks complete during event replay, the rendered tree should     shrink once** (1 connections) — `tests/compact/test_tree_event_replay.py`
- **Simulate start-of-run event with preflight task list.** (1 connections) — `tests/compact/test_tree_event_replay.py`
- **Create RunState with preflight definitions matching events we'll replay.** (1 connections) — `tests/compact/test_tree_event_replay.py`

## Relationships

- [Pause Prompt Heuristic](Pause_Prompt_Heuristic.md) (3 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (1 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (1 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)
- [Hide State Gating Tests](Hide_State_Gating_Tests.md) (1 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (1 shared connections)

## Source Files

- `tests/compact/test_tree_event_replay.py`

## Audit Trail

- EXTRACTED: 63 (93%)
- INFERRED: 5 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*