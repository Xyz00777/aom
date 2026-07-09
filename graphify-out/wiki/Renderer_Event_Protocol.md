# Renderer Event Protocol

> 51 nodes · cohesion 0.07

## Key Concepts

- **.format_status_bar()** (54 connections) — `tests/integration/test_compact_renderer.py`
- **LivenessState** (28 connections) — `src/ansible_aom/core/heartbeat.py`
- **test_status_bar_liveness.py** (18 connections) — `tests/compact/test_status_bar_liveness.py`
- **TestStatusBarMode** (4 connections) — `tests/compact/test_check_mode_chip.py`
- **test_live_cpu_annotated_with_cpu_marker()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_live_pty_has_no_reason_annotation()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_reason_annotation_is_dim_when_colorized()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_segment_inserted_directly_before_elapsed_no_separator_after_predecessor()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_stuck_carries_no_reason_annotation()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_working_cpu_annotated_with_cpu_marker()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_working_silent_annotated_with_silent_marker()** (4 connections) — `tests/compact/test_status_bar_liveness.py`
- **.test_sigwinch_triggers_rerender()** (4 connections) — `tests/integration/test_compact_renderer.py`
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
- **.test_status_bar_format_basic()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_status_bar_with_warnings()** (3 connections) — `tests/integration/test_compact_renderer.py`
- *... and 26 more nodes in this community*

## Relationships

- [Status Icon Unicode Mapping](Status_Icon_Unicode_Mapping.md) (7 shared connections)
- [Community 505](Community_505.md) (6 shared connections)
- [Community 530](Community_530.md) (5 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (4 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (3 shared connections)
- [Session List View](Session_List_View.md) (3 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (3 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (2 shared connections)
- [Ansible Runner Subprocess](Ansible_Runner_Subprocess.md) (2 shared connections)
- [Renderer Set Definitions](Renderer_Set_Definitions.md) (1 shared connections)
- [Inspect Debug Diagnostics](Inspect_Debug_Diagnostics.md) (1 shared connections)
- [Replay Frame Signatures](Replay_Frame_Signatures.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/heartbeat.py`
- `tests/compact/test_check_mode_chip.py`
- `tests/compact/test_status_bar_liveness.py`
- `tests/compact/test_task_progress.py`
- `tests/integration/test_compact_renderer.py`
- `tests/unit/test_event_processing.py`

## Audit Trail

- EXTRACTED: 100 (47%)
- INFERRED: 112 (53%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*