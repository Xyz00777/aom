# CompactRenderer

> 116 nodes · cohesion 0.02

## Key Concepts

- **CompactRenderer** (338 connections) — `src/ansible_aom/compact/renderer.py`
- **test_renderer_stats.py** (11 connections) — `tests/compact/test_renderer_stats.py`
- **TestCompactModePasswordFlow** (10 connections) — `tests/compact/test_password.py`
- **TestCompactRendererInteractivePrompt** (9 connections) — `tests/unit/test_interactive_prompt.py`
- **test_warning_visibility.py** (8 connections) — `tests/compact/test_warning_visibility.py`
- **test_long_output_cap.py** (7 connections) — `tests/compact/test_long_output_cap.py`
- **test_prior_run_loop_totals_injection.py** (5 connections) — `tests/unit/test_prior_run_loop_totals_injection.py`
- **TestCompactInjection** (5 connections) — `tests/unit/test_prior_run_loop_totals_injection.py`
- **_ok_event()** (4 connections) — `tests/compact/test_renderer_stats.py`
- **test_renderer_status_bar_reflects_outcome_tally()** (4 connections) — `tests/compact/test_status_tally_bar.py`
- **.test_tick_refreshes_status_bar_without_an_event()** (4 connections) — `tests/integration/test_compact_renderer.py`
- **.test_handle_password_prompt_returns_string()** (4 connections) — `tests/integration/test_compact_renderer.py`
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
- *... and 91 more nodes in this community*

## Relationships

- [HostRunState](HostRunState.md) (69 shared connections)
- [._emit_event_log](_emit_event_log.md) (31 shared connections)
- [Inspect CLI Commands](Inspect_CLI_Commands.md) (14 shared connections)
- [Event Log Emission](Event_Log_Emission.md) (14 shared connections)
- [renderer.py](renderer.py.md) (8 shared connections)
- [_BoundedSet](_BoundedSet.md) (8 shared connections)
- [create_renderer](create_renderer.md) (8 shared connections)
- [Playbook Run Integration Tests](Playbook_Run_Integration_Tests.md) (8 shared connections)
- [Renderer Parity Invariant](Renderer_Parity_Invariant.md) (7 shared connections)
- [test_renderer_set_definitions.py](test_renderer_set_definitions.py.md) (7 shared connections)
- [PriorRun](PriorRun.md) (6 shared connections)
- [Tree Expansion Icons](Tree_Expansion_Icons.md) (6 shared connections)

## Source Files

- `src/ansible_aom/compact/renderer.py`
- `tests/compact/test_long_output_cap.py`
- `tests/compact/test_password.py`
- `tests/compact/test_renderer_stats.py`
- `tests/compact/test_status_tally_bar.py`
- `tests/compact/test_warning_visibility.py`
- `tests/integration/test_compact_renderer.py`
- `tests/unit/test_interactive_prompt.py`
- `tests/unit/test_prior_run_loop_totals_injection.py`

## Audit Trail

- EXTRACTED: 394 (65%)
- INFERRED: 216 (35%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*