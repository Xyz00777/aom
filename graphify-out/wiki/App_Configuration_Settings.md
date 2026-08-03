# App Configuration Settings

> 139 nodes · cohesion 0.02

## Key Concepts

- **CompactRenderer** (344 connections) — `src/ansible_aom/compact/renderer.py`
- **test_renderer_set_definitions.py** (11 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_renderer_stats.py** (11 connections) — `tests/compact/test_renderer_stats.py`
- **TestCompactModePasswordFlow** (10 connections) — `tests/compact/test_password.py`
- **TestCompactRendererInteractivePrompt** (9 connections) — `tests/unit/test_interactive_prompt.py`
- **test_warning_visibility.py** (8 connections) — `tests/compact/test_warning_visibility.py`
- **test_long_output_cap.py** (7 connections) — `tests/compact/test_long_output_cap.py`
- **_build_definitions()** (7 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_unknown_event_hint.py** (7 connections) — `tests/compact/test_unknown_event_hint.py`
- **test_unmatched_event_hint.py** (6 connections) — `tests/compact/test_unmatched_event_hint.py`
- **test_set_definitions_called_before_start_is_safe()** (4 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_set_definitions_prints_summary_above_status_panel()** (4 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_set_definitions_unions_hosts_across_plays()** (4 connections) — `tests/compact/test_renderer_set_definitions.py`
- **test_set_definitions_updates_initial_hosts_total_in_status_bar()** (4 connections) — `tests/compact/test_renderer_set_definitions.py`
- **_ok_event()** (4 connections) — `tests/compact/test_renderer_stats.py`
- **test_renderer_status_bar_reflects_outcome_tally()** (4 connections) — `tests/compact/test_status_tally_bar.py`
- **_empty_state()** (4 connections) — `tests/compact/test_unknown_event_hint.py`
- **test_completion_no_hint_when_all_known()** (4 connections) — `tests/compact/test_unknown_event_hint.py`
- **_empty_state()** (4 connections) — `tests/compact/test_unmatched_event_hint.py`
- **.test_tick_refreshes_status_bar_without_an_event()** (4 connections) — `tests/integration/test_compact_renderer.py`
- **.test_handle_password_prompt_returns_string()** (4 connections) — `tests/integration/test_compact_renderer.py`
- **test_item_failed_msg_truncated_above_cap()** (3 connections) — `tests/compact/test_long_output_cap.py`
- **test_one_megabyte_failed_msg_truncated()** (3 connections) — `tests/compact/test_long_output_cap.py`
- **test_short_msg_not_truncated()** (3 connections) — `tests/compact/test_long_output_cap.py`
- **.test_render_handle_password_prompt_returns_empty_on_cancel()** (3 connections) — `tests/compact/test_password.py`
- *... and 114 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (59 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (31 shared connections)
- [Inspect CLI Commands](Inspect_CLI_Commands.md) (14 shared connections)
- [Event Log Emission](Event_Log_Emission.md) (14 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (10 shared connections)
- [._render_status_panel](_render_status_panel.md) (9 shared connections)
- [Preflight Summary Rendering](Preflight_Summary_Rendering.md) (9 shared connections)
- [Playbook Run Integration Tests](Playbook_Run_Integration_Tests.md) (8 shared connections)
- [Renderer Parity Invariant](Renderer_Parity_Invariant.md) (7 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (6 shared connections)
- [Tree Expansion Icons](Tree_Expansion_Icons.md) (6 shared connections)
- [Mitogen Event Robustness](Mitogen_Event_Robustness.md) (6 shared connections)

## Source Files

- `src/ansible_aom/compact/renderer.py`
- `tests/compact/test_long_output_cap.py`
- `tests/compact/test_password.py`
- `tests/compact/test_renderer_set_definitions.py`
- `tests/compact/test_renderer_stats.py`
- `tests/compact/test_status_tally_bar.py`
- `tests/compact/test_unknown_event_hint.py`
- `tests/compact/test_unmatched_event_hint.py`
- `tests/compact/test_warning_visibility.py`
- `tests/integration/test_compact_renderer.py`
- `tests/unit/test_interactive_prompt.py`

## Audit Trail

- EXTRACTED: 380 (55%)
- INFERRED: 308 (45%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*