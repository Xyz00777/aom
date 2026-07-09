# App Configuration Settings

> 124 nodes · cohesion 0.02

## Key Concepts

- **CompactRenderer** (314 connections) — `src/ansible_aom/compact/renderer.py`
- **TestCompactModePasswordFlow** (11 connections) — `tests/compact/test_password.py`
- **TestCompactRendererInteractivePrompt** (10 connections) — `tests/unit/test_interactive_prompt.py`
- **test_renderer_stats.py** (9 connections) — `tests/compact/test_renderer_stats.py`
- **test_warning_visibility.py** (7 connections) — `tests/compact/test_warning_visibility.py`
- **test_long_output_cap.py** (6 connections) — `tests/compact/test_long_output_cap.py`
- **test_unknown_event_hint.py** (5 connections) — `tests/compact/test_unknown_event_hint.py`
- **_ok_event()** (4 connections) — `tests/compact/test_renderer_stats.py`
- **_empty_state()** (4 connections) — `tests/compact/test_unknown_event_hint.py`
- **test_completion_no_hint_when_all_known()** (4 connections) — `tests/compact/test_unknown_event_hint.py`
- **test_item_failed_msg_truncated_above_cap()** (3 connections) — `tests/compact/test_long_output_cap.py`
- **test_one_megabyte_failed_msg_truncated()** (3 connections) — `tests/compact/test_long_output_cap.py`
- **test_short_msg_not_truncated()** (3 connections) — `tests/compact/test_long_output_cap.py`
- **.test_render_handle_password_prompt_returns_empty_on_cancel()** (3 connections) — `tests/compact/test_password.py`
- **.test_render_handle_password_prompt_returns_password()** (3 connections) — `tests/compact/test_password.py`
- **.test_render_handle_password_prompt_starts_display_after_input()** (3 connections) — `tests/compact/test_password.py`
- **.test_render_handle_password_prompt_starts_display_even_on_error()** (3 connections) — `tests/compact/test_password.py`
- **.test_render_handle_password_prompt_stop_before_start_order()** (3 connections) — `tests/compact/test_password.py`
- **.test_render_handle_password_prompt_stops_display_before_input()** (3 connections) — `tests/compact/test_password.py`
- **.test_render_handle_password_prompt_uses_finally_for_restart()** (3 connections) — `tests/compact/test_password.py`
- **test_collect_stats_returns_snapshot()** (3 connections) — `tests/compact/test_renderer_stats.py`
- **test_stop_publishes_last_renderer_stats()** (3 connections) — `tests/compact/test_renderer_stats.py`
- **test_update_state_increments_render_calls()** (3 connections) — `tests/compact/test_renderer_stats.py`
- **test_completion_no_hint_when_state_is_none()** (3 connections) — `tests/compact/test_unknown_event_hint.py`
- **test_completion_prints_unknown_event_hint()** (3 connections) — `tests/compact/test_unknown_event_hint.py`
- *... and 99 more nodes in this community*

## Relationships

- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (49 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (27 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (15 shared connections)
- [Inspect CLI Commands](Inspect_CLI_Commands.md) (14 shared connections)
- [Event Log Emission](Event_Log_Emission.md) (14 shared connections)
- [Preflight Summary Rendering](Preflight_Summary_Rendering.md) (9 shared connections)
- [Playbook Run Integration Tests](Playbook_Run_Integration_Tests.md) (8 shared connections)
- [Renderer Parity Invariant](Renderer_Parity_Invariant.md) (7 shared connections)
- [Unicode Support Detection](Unicode_Support_Detection.md) (7 shared connections)
- [Crash Recovery Panels](Crash_Recovery_Panels.md) (6 shared connections)
- [Inspect Debug Diagnostics](Inspect_Debug_Diagnostics.md) (6 shared connections)
- [Tree Expansion Icons](Tree_Expansion_Icons.md) (6 shared connections)

## Source Files

- `src/ansible_aom/compact/renderer.py`
- `tests/compact/test_long_output_cap.py`
- `tests/compact/test_password.py`
- `tests/compact/test_renderer_stats.py`
- `tests/compact/test_unknown_event_hint.py`
- `tests/compact/test_warning_visibility.py`
- `tests/integration/test_compact_renderer.py`
- `tests/unit/test_interactive_prompt.py`

## Audit Trail

- EXTRACTED: 294 (49%)
- INFERRED: 300 (51%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*