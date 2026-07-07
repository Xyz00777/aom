# CompactRenderer

> God node · 288 connections · `src/ansible_aom/compact/renderer.py`

**Community:** [[Compact Renderer Implementation]]

## Connections by Relation

### calls
- [[create_renderer()]] `INFERRED`
- [[_record_live_compact()]] `INFERRED`
- [[_build_compact_renderer()]] `INFERRED`
- [[test_handle_completion_keeps_runtime_grown_denominator()]] `INFERRED`
- [[.test_colored_output_has_ansi_codes()]] `EXTRACTED`
- [[test_fixed_floor_not_scaled_by_fast_variable_task()]] `EXTRACTED`
- [[test_long_running_task_burns_estimate_down()]] `EXTRACTED`
- [[_replay_compact()]] `INFERRED`
- [[_final_line()]] `INFERRED`
- [[test_no_estimate_without_prior()]] `EXTRACTED`
- [[_render()]] `INFERRED`
- [[._final_line()]] `EXTRACTED`
- [[_drive_compact()]] `INFERRED`
- [[test_renderer_status_bar_reflects_task_progress()]] `INFERRED`
- [[test_hosts_completed_doesnt_oscillate_with_in_flight_task()]] `INFERRED`
- [[.test_failure_recap_lines_indented()]] `INFERRED`
- [[test_completion_snapshot_contains_host_rows()]] `INFERRED`
- [[test_set_definitions_called_before_start_is_safe()]] `INFERRED`
- [[test_set_definitions_prints_summary_above_status_panel()]] `INFERRED`
- [[test_set_definitions_unions_hosts_across_plays()]] `INFERRED`

### contains
- [[renderer.py]] `EXTRACTED`

### method
- [[._emit_event_log()]] `EXTRACTED`
- [[._render_status_panel()]] `EXTRACTED`
- [[.__init__()]] `EXTRACTED`
- [[.print_log()]] `EXTRACTED`
- [[._announce_task()]] `EXTRACTED`
- [[.handle_completion()]] `EXTRACTED`
- [[._bump_task_counters()]] `EXTRACTED`
- [[._emit_previous_task_summary()]] `EXTRACTED`
- [[._format_loop_item_line()]] `EXTRACTED`
- [[.start()]] `EXTRACTED`
- [[._task_dict()]] `EXTRACTED`
- [[._capture_panel_snapshot()]] `EXTRACTED`
- [[._flush_pending_skips()]] `EXTRACTED`
- [[._count_completed_task()]] `EXTRACTED`
- [[._inline_duration_suffix()]] `EXTRACTED`
- [[.stop()]] `EXTRACTED`
- [[.update_state()]] `EXTRACTED`
- [[.add_warning()]] `EXTRACTED`
- [[._enter_terminal_event()]] `EXTRACTED`
- [[._event_time()]] `EXTRACTED`

### rationale_for
- [[ANSI-based compact renderer satisfying the Renderer Protocol.      Implements th]] `EXTRACTED`

### references
- [[_renderer()]] `EXTRACTED`
- [[_logged()]] `EXTRACTED`
- [[_logged()]] `EXTRACTED`
- [[_renderer()]] `EXTRACTED`
- [[_renderer()]] `EXTRACTED`
- [[_renderer()]] `EXTRACTED`
- [[_last_summary_line()]] `EXTRACTED`
- [[_renderer()]] `EXTRACTED`
- [[_all_text()]] `EXTRACTED`
- [[_logged()]] `EXTRACTED`
- [[_renderer()]] `EXTRACTED`
- [[_renderer()]] `EXTRACTED`
- [[_renderer_with_running_task()]] `EXTRACTED`
- [[_logged()]] `EXTRACTED`
- [[_renderer()]] `EXTRACTED`
- [[_setup()]] `EXTRACTED`
- [[_logged()]] `EXTRACTED`
- [[_seed_sticky_gap_state()]] `EXTRACTED`
- [[_logged()]] `EXTRACTED`
- [[._logged()]] `EXTRACTED`

### uses
- [[RunState]] `INFERRED`
- [[Status]] `INFERRED`
- [[Display]] `INFERRED`
- [[JsonlEvent]] `INFERRED`
- [[TestHideStateFlag]] `INFERRED`
- [[LivenessState]] `INFERRED`
- [[HeartbeatTracker]] `INFERRED`
- [[RunProgress]] `INFERRED`
- [[RendererMirrorMachine]] `INFERRED`
- [[TestStatusBarFormat]] `INFERRED`
- [[TestSignalHandling]] `INFERRED`
- [[TestRendererProtocol]] `INFERRED`
- [[TestPasswordPromptPatterns]] `INFERRED`
- [[TestStatusIcons]] `INFERRED`
- [[TestHideStateCompactPlumbing]] `INFERRED`
- [[TestNoRedactFlag]] `INFERRED`
- [[TestRendererFactory]] `INFERRED`
- [[PriorRun]] `INFERRED`
- [[TestStatusIconFallback]] `INFERRED`
- [[TestFormatFlag]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*