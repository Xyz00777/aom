# CompactRenderer

> God node · 314 connections · `src/ansible_aom/compact/renderer.py`

**Community:** [App Configuration Settings](App_Configuration_Settings.md)

## Connections by Relation

### calls
- create_renderer() `INFERRED`
- _record_live_compact() `INFERRED`
- _build_compact_renderer() `INFERRED`
- test_handle_completion_keeps_runtime_grown_denominator() `INFERRED`
- .test_colored_output_has_ansi_codes() `EXTRACTED`
- test_fixed_floor_not_scaled_by_fast_variable_task() `EXTRACTED`
- test_long_running_task_burns_estimate_down() `EXTRACTED`
- _replay_compact() `INFERRED`
- _final_line() `INFERRED`
- test_no_estimate_without_prior() `EXTRACTED`
- _render() `INFERRED`
- ._final_line() `EXTRACTED`
- _drive_compact() `INFERRED`
- test_renderer_status_bar_reflects_task_progress() `INFERRED`
- test_hosts_completed_doesnt_oscillate_with_in_flight_task() `INFERRED`
- .test_failure_recap_lines_indented() `INFERRED`
- test_completion_snapshot_contains_host_rows() `INFERRED`
- test_set_definitions_called_before_start_is_safe() `INFERRED`
- test_set_definitions_prints_summary_above_status_panel() `INFERRED`
- test_set_definitions_unions_hosts_across_plays() `INFERRED`

### contains
- renderer.py `EXTRACTED`

### indirect_call
- .test_factory_creates_compact_renderer_by_default() `INFERRED`
- .test_factory_creates_compact_renderer_when_tui_false() `INFERRED`
- .test_factory_forwards_failed_hint_flag_to_compact_renderer() `INFERRED`
- .test_factory_forwards_is_tty_to_compact_renderer() `INFERRED`
- .test_factory_forwards_recording_flags_to_compact_renderer() `INFERRED`
- .test_factory_forwards_warning_flags_to_compact_renderer() `INFERRED`
- .test_compact_renderer_has_handle_completion_method() `INFERRED`
- .test_compact_renderer_has_handle_password_prompt_method() `INFERRED`
- .test_compact_renderer_has_start_method() `INFERRED`
- .test_compact_renderer_has_stop_method() `INFERRED`
- .test_compact_renderer_has_update_state_method() `INFERRED`
- test_factory_compact_format_explicit_returns_compact_renderer() `INFERRED`
- test_factory_default_format_is_compact() `INFERRED`

### method
- ._emit_event_log() `EXTRACTED`
- ._render_status_panel() `EXTRACTED`
- .handle_completion() `EXTRACTED`
- .__init__() `EXTRACTED`
- .print_log() `EXTRACTED`
- ._announce_task() `EXTRACTED`
- .start() `EXTRACTED`
- ._bump_task_counters() `EXTRACTED`
- ._emit_previous_task_summary() `EXTRACTED`
- ._task_dict() `EXTRACTED`
- ._capture_panel_snapshot() `EXTRACTED`
- ._flush_pending_skips() `EXTRACTED`
- ._format_loop_item_line() `EXTRACTED`
- ._count_completed_task() `EXTRACTED`
- ._inline_duration_suffix() `EXTRACTED`
- .stop() `EXTRACTED`
- .update_state() `EXTRACTED`
- .add_warning() `EXTRACTED`
- ._enter_terminal_event() `EXTRACTED`
- ._event_time() `EXTRACTED`

### rationale_for
- ANSI-based compact renderer satisfying the Renderer Protocol.      Implements th `EXTRACTED`

### references
- _renderer() `EXTRACTED`
- _logged() `EXTRACTED`
- _logged() `EXTRACTED`
- _renderer() `EXTRACTED`
- _renderer() `EXTRACTED`
- _renderer() `EXTRACTED`
- _last_summary_line() `EXTRACTED`
- _renderer() `EXTRACTED`
- _all_text() `EXTRACTED`
- _logged() `EXTRACTED`
- _renderer() `EXTRACTED`
- _renderer() `EXTRACTED`
- _renderer_with_running_task() `EXTRACTED`
- _logged() `EXTRACTED`
- _renderer() `EXTRACTED`
- _setup() `EXTRACTED`
- _logged() `EXTRACTED`
- _seed_sticky_gap_state() `EXTRACTED`
- _logged() `EXTRACTED`
- ._logged() `EXTRACTED`

### uses
- [Status](Status.md) `INFERRED`
- JsonlEvent `INFERRED`
- Display `INFERRED`
- TestHideStateFlag `INFERRED`
- LivenessState `INFERRED`
- HeartbeatTracker `INFERRED`
- TestPasswordPromptPTYIntegration `INFERRED`
- RunProgress `INFERRED`
- RendererMirrorMachine `INFERRED`
- TestStatusBarFormat `INFERRED`
- PriorRun `INFERRED`
- TestSignalHandling `INFERRED`
- TestRendererProtocol `INFERRED`
- TestPasswordPromptPatterns `INFERRED`
- TestStatusIcons `INFERRED`
- TestHideStateCompactPlumbing `INFERRED`
- TestNoRedactFlag `INFERRED`
- TestRendererFactory `INFERRED`
- TestStatusIconFallback `INFERRED`
- TestFormatFlag `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*