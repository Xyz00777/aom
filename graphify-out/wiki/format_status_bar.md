# format_status_bar

> 69 nodes · cohesion 0.05

## Key Concepts

- **format_status_bar()** (57 connections) — `src/ansible_aom/compact/format.py`
- **LivenessState** (30 connections) — `src/ansible_aom/core/heartbeat.py`
- **test_status_bar_liveness.py** (20 connections) — `tests/compact/test_status_bar_liveness.py`
- **TestStatusBarColors** (13 connections) — `tests/compact/test_status_bar_colors.py`
- **heartbeat.py** (7 connections) — `src/ansible_aom/core/heartbeat.py`
- **test_status_bar_eta.py** (7 connections) — `tests/compact/test_status_bar_eta.py`
- **TestStatusBarMode** (4 connections) — `tests/compact/test_check_mode_chip.py`
- **test_live_cpu_annotated_with_cpu_marker()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_live_pty_has_no_reason_annotation()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_reason_annotation_is_dim_when_colorized()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_segment_inserted_directly_before_elapsed_no_separator_after_predecessor()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_stuck_carries_no_reason_annotation()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_working_cpu_annotated_with_cpu_marker()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_working_silent_annotated_with_silent_marker()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_ascii_mode_falls_back_to_plain_glyphs()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_live_segment_is_green_when_colorized()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_live_segment_rendered_with_dot_and_age()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_no_color_in_segment_when_colorize_off()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_segment_present_even_with_zero_deprecations_and_warnings()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_stuck_segment_is_red_when_colorized()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_stuck_segment_rendered_with_bang()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_working_segment_is_dim_when_colorized()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_working_segment_rendered_with_open_circle()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_format_status_bar_omits_tasks_when_total_zero()** (3 connections) — `tests/compact/test_task_progress.py`
- **test_format_status_bar_task_progress_defaults_to_zero()** (3 connections) — `tests/compact/test_task_progress.py`
- *... and 44 more nodes in this community*

## Relationships

- [renderer.py](renderer.py.md) (10 shared connections)
- [Status Icon Unicode Mapping](Status_Icon_Unicode_Mapping.md) (8 shared connections)
- [RunState](RunState.md) (7 shared connections)
- [HostRunState](HostRunState.md) (4 shared connections)
- [_BoundedSet](_BoundedSet.md) (3 shared connections)
- [icons.py](icons.py.md) (3 shared connections)
- [PlayDefinition](PlayDefinition.md) (3 shared connections)
- [_row_count](_row_count.md) (2 shared connections)
- [CompactRenderer](CompactRenderer.md) (2 shared connections)
- [format_age](format_age.md) (1 shared connections)
- [._emit_event_log](_emit_event_log.md) (1 shared connections)
- [test_status_bar_estimated_total.py](test_status_bar_estimated_total.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/core/heartbeat.py`
- `tests/compact/test_check_mode_chip.py`
- `tests/compact/test_status_bar_colors.py`
- `tests/compact/test_status_bar_eta.py`
- `tests/compact/test_status_bar_liveness.py`
- `tests/compact/test_task_progress.py`
- `tests/unit/test_event_processing.py`

## Audit Trail

- EXTRACTED: 178 (65%)
- INFERRED: 94 (35%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*