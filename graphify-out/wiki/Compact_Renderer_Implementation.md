# Compact Renderer Implementation

> 102 nodes · cohesion 0.02

## Key Concepts

- **CompactRenderer** (288 connections) — `src/ansible_aom/compact/renderer.py`
- **TestCompactRendererInteractivePrompt** (10 connections) — `tests/unit/test_interactive_prompt.py`
- **test_renderer_stats.py** (9 connections) — `tests/compact/test_renderer_stats.py`
- **.start()** (8 connections) — `src/ansible_aom/compact/renderer.py`
- **TestPauseSecondsLogged** (8 connections) — `tests/unit/test_compact_pause_visibility.py`
- **test_warning_visibility.py** (7 connections) — `tests/compact/test_warning_visibility.py`
- **.stop()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **test_long_output_cap.py** (6 connections) — `tests/compact/test_long_output_cap.py`
- **renderer.py** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **_pause_task_event()** (5 connections) — `tests/unit/test_compact_pause_visibility.py`
- **.collect_stats()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **.handle_interactive_prompt()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **.handle_password_prompt()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **_ok_event()** (4 connections) — `tests/compact/test_renderer_stats.py`
- **.test_pause_short_action_name_also_caught()** (4 connections) — `tests/unit/test_compact_pause_visibility.py`
- **.test_pause_with_string_seconds_handled()** (4 connections) — `tests/unit/test_compact_pause_visibility.py`
- **.test_pause_without_seconds_does_not_emit_sleeping_line()** (4 connections) — `tests/unit/test_compact_pause_visibility.py`
- **test_short_msg_not_truncated()** (3 connections) — `tests/compact/test_long_output_cap.py`
- **test_collect_stats_returns_snapshot()** (3 connections) — `tests/compact/test_renderer_stats.py`
- **test_stop_publishes_last_renderer_stats()** (3 connections) — `tests/compact/test_renderer_stats.py`
- **test_update_state_increments_render_calls()** (3 connections) — `tests/compact/test_renderer_stats.py`
- **test_add_warning_counter_still_bumps()** (3 connections) — `tests/compact/test_warning_visibility.py`
- **test_add_warning_dedupes_repeated_messages()** (3 connections) — `tests/compact/test_warning_visibility.py`
- **test_add_warning_message_is_prefixed_for_classification()** (3 connections) — `tests/compact/test_warning_visibility.py`
- **.test_handle_completion_accepts_exit_code_and_state()** (3 connections) — `tests/integration/test_compact_renderer.py`
- *... and 77 more nodes in this community*

## Relationships

- [[Compact Renderer Integration Tests]] (39 shared connections)
- [[Event Log Emission]] (22 shared connections)
- [[CLI Interface Tests]] (17 shared connections)
- [[Task Summary Count Tests]] (14 shared connections)
- [[Hide State Gating Tests]] (13 shared connections)
- [[Run State Completion Recap]] (9 shared connections)
- [[Loop Item Line Tests]] (7 shared connections)
- [[Loop Item Stream Tests]] (7 shared connections)
- [[Renderer Set Definitions]] (7 shared connections)
- [[Color ASCII Fallback]] (6 shared connections)
- [[Runner Event Batching]] (6 shared connections)
- [[Renderer ETA Wiring]] (6 shared connections)

## Source Files

- `src/ansible_aom/compact/renderer.py`
- `tests/compact/test_long_output_cap.py`
- `tests/compact/test_renderer_stats.py`
- `tests/compact/test_warning_visibility.py`
- `tests/integration/test_compact_renderer.py`
- `tests/unit/test_compact_pause_visibility.py`
- `tests/unit/test_interactive_prompt.py`

## Audit Trail

- EXTRACTED: 279 (52%)
- INFERRED: 262 (48%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*