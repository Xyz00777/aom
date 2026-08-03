# Session List View

> 29 nodes · cohesion 0.10

## Key Concepts

- **format_host_summary()** (14 connections) — `src/ansible_aom/compact/format.py`
- **icons.py** (14 connections) — `src/ansible_aom/core/icons.py`
- **test_ascii_fallback.py** (12 connections) — `tests/compact/test_ascii_fallback.py`
- **TestHostSummaryColors** (12 connections) — `tests/compact/test_status_bar_colors.py`
- **get_running_frame()** (8 connections) — `src/ansible_aom/core/icons.py`
- **is_unicode_terminal()** (8 connections) — `src/ansible_aom/core/icons.py`
- **_format_count_cells()** (5 connections) — `src/ansible_aom/compact/format.py`
- **test_is_unicode_terminal_false_for_none_encoding()** (3 connections) — `tests/compact/test_ascii_fallback.py`
- **Render non-zero status count cells.      Order: ok, changed, skipped, failed, un** (2 connections) — `src/ansible_aom/compact/format.py`
- **test_format_host_summary_ascii_mode_uses_ascii_icons()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_format_host_summary_unicode_mode_default()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_format_status_bar_ascii_mode_uses_ascii_warning_glyph()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_format_status_bar_ascii_mode_uses_pipe_separator()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_format_status_bar_unicode_mode_keeps_unicode_glyphs()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_is_unicode_terminal_false_for_ascii()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_is_unicode_terminal_true_for_uppercase_utf8()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_is_unicode_terminal_true_for_utf8()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **.test_changed_segment_is_yellow()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_default_no_color()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_failed_segment_is_red()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_ok_segment_is_green()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_skipped_segment_is_dim()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_unreachable_segment_is_magenta()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **Format a host summary line with status icons.      Only includes non-zero counts** (1 connections) — `src/ansible_aom/compact/format.py`
- **Status icon mapping for AOM display.  This module provides Unicode status icons** (1 connections) — `src/ansible_aom/core/icons.py`
- *... and 4 more nodes in this community*

## Relationships

- [Warning Classification Tests](Warning_Classification_Tests.md) (6 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (4 shared connections)
- [Renderer Event Protocol](Renderer_Event_Protocol.md) (3 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (3 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (2 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (2 shared connections)
- [Pause Prompt Heuristic](Pause_Prompt_Heuristic.md) (2 shared connections)
- [Error Handling Tests](Error_Handling_Tests.md) (2 shared connections)
- [Dirty Flag Throttle](Dirty_Flag_Throttle.md) (1 shared connections)
- [Warning Pattern Classification](Warning_Pattern_Classification.md) (1 shared connections)
- [Pydantic Model Basics](Pydantic_Model_Basics.md) (1 shared connections)
- [Ansible Args Validation](Ansible_Args_Validation.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/core/icons.py`
- `tests/compact/test_ascii_fallback.py`
- `tests/compact/test_status_bar_colors.py`

## Audit Trail

- EXTRACTED: 74 (66%)
- INFERRED: 38 (34%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*