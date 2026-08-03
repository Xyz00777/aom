# Heartbeat Liveness Tracker

> 88 nodes · cohesion 0.03

## Key Concepts

- **JsonlEvent** (66 connections) — `src/ansible_aom/core/event_types.py`
- **._emit_event_log()** (24 connections) — `src/ansible_aom/compact/renderer.py`
- **_wrap()** (19 connections) — `src/ansible_aom/compact/format.py`
- **format_failure_recap()** (16 connections) — `src/ansible_aom/compact/format.py`
- **.update_state()** (12 connections) — `src/ansible_aom/compact/renderer.py`
- **TestFailureRecapColors** (11 connections) — `tests/compact/test_status_bar_colors.py`
- **._flush_ready_summaries()** (10 connections) — `src/ansible_aom/compact/renderer.py`
- **.print_log()** (10 connections) — `src/ansible_aom/compact/renderer.py`
- **._task_dict()** (10 connections) — `src/ansible_aom/compact/renderer.py`
- **._announce_task()** (9 connections) — `src/ansible_aom/compact/renderer.py`
- **._state_with()** (9 connections) — `tests/compact/test_status_bar_colors.py`
- **_truncate_msg()** (8 connections) — `src/ansible_aom/compact/format.py`
- **._bump_task_counters()** (8 connections) — `src/ansible_aom/compact/renderer.py`
- **._emit_task_summary()** (8 connections) — `src/ansible_aom/compact/renderer.py`
- **._format_loop_item_line()** (8 connections) — `src/ansible_aom/compact/renderer.py`
- **._flush_pending_skips()** (7 connections) — `src/ansible_aom/compact/renderer.py`
- **._maybe_flush_completed()** (7 connections) — `src/ansible_aom/compact/renderer.py`
- **is_async_poll_payload()** (7 connections) — `src/ansible_aom/core/_async_poll.py`
- **_verbose_ok_body()** (6 connections) — `src/ansible_aom/compact/format.py`
- **._count_completed_task()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **._event_time()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **._inline_duration_suffix()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **._stale_task_suffix()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **.add()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **.add_warning()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- *... and 63 more nodes in this community*

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (31 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (15 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (14 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (13 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (8 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (7 shared connections)
- [._render_status_panel](_render_status_panel.md) (6 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (5 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (4 shared connections)
- [16-Color Fallback](16-Color_Fallback.md) (4 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (3 shared connections)
- [List-Tasks Failure Handling](List-Tasks_Failure_Handling.md) (3 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`
- `src/ansible_aom/core/_async_poll.py`
- `src/ansible_aom/core/duration.py`
- `src/ansible_aom/core/event_types.py`
- `tests/compact/test_status_bar_colors.py`

## Audit Trail

- EXTRACTED: 350 (84%)
- INFERRED: 67 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*