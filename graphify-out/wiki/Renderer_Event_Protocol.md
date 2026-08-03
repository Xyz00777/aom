# Renderer Event Protocol

> 69 nodes · cohesion 0.05

## Key Concepts

- **format_status_bar()** (57 connections) — `src/ansible_aom/compact/format.py`
- **LivenessState** (30 connections) — `src/ansible_aom/core/heartbeat.py`
- **test_status_bar_liveness.py** (20 connections) — `tests/compact/test_status_bar_liveness.py`
- **TestStatusBarColors** (13 connections) — `tests/compact/test_status_bar_colors.py`
- **heartbeat.py** (7 connections) — `src/ansible_aom/core/heartbeat.py`
- **test_status_bar_eta.py** (7 connections) — `tests/compact/test_status_bar_eta.py`
- **test_row_count_ignores_ansi_escape_sequences()** (5 connections) — `tests/compact/test_row_count.py`
- **.test_sigwinch_triggers_rerender()** (5 connections) — `tests/integration/test_compact_renderer.py`
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
- *... and 44 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (10 shared connections)
- [Status Icon Unicode Mapping](Status_Icon_Unicode_Mapping.md) (8 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (6 shared connections)
- [._render_status_panel](_render_status_panel.md) (5 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (4 shared connections)
- [Session List View](Session_List_View.md) (3 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (3 shared connections)
- [Replay Frame Signatures](Replay_Frame_Signatures.md) (2 shared connections)
- [Ansible Runner Subprocess](Ansible_Runner_Subprocess.md) (2 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (1 shared connections)
- [Source Hash Version](Source_Hash_Version.md) (1 shared connections)
- [Playbook Parser Integration Tests](Playbook_Parser_Integration_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/core/heartbeat.py`
- `tests/compact/test_check_mode_chip.py`
- `tests/compact/test_row_count.py`
- `tests/compact/test_status_bar_colors.py`
- `tests/compact/test_status_bar_eta.py`
- `tests/compact/test_status_bar_liveness.py`
- `tests/integration/test_compact_renderer.py`
- `tests/unit/test_event_processing.py`

## Audit Trail

- EXTRACTED: 137 (50%)
- INFERRED: 139 (50%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*