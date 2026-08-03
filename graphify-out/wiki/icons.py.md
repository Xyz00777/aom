# icons.py

> 22 nodes · cohesion 0.11

## Key Concepts

- **icons.py** (14 connections) — `src/ansible_aom/core/icons.py`
- **test_ascii_fallback.py** (12 connections) — `tests/compact/test_ascii_fallback.py`
- **get_running_frame()** (8 connections) — `src/ansible_aom/core/icons.py`
- **is_unicode_terminal()** (8 connections) — `src/ansible_aom/core/icons.py`
- **test_spinner_animation.py** (8 connections) — `tests/compact/test_spinner_animation.py`
- **test_default_frame_still_works_for_backward_compat()** (5 connections) — `tests/compact/test_spinner_animation.py`
- **test_is_unicode_terminal_false_for_none_encoding()** (3 connections) — `tests/compact/test_ascii_fallback.py`
- **test_format_host_summary_ascii_mode_uses_ascii_icons()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_format_host_summary_unicode_mode_default()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_format_status_bar_ascii_mode_uses_ascii_warning_glyph()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_format_status_bar_ascii_mode_uses_pipe_separator()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_format_status_bar_unicode_mode_keeps_unicode_glyphs()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_is_unicode_terminal_false_for_ascii()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_is_unicode_terminal_true_for_uppercase_utf8()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **test_is_unicode_terminal_true_for_utf8()** (2 connections) — `tests/compact/test_ascii_fallback.py`
- **Status icon mapping for AOM display.  This module provides Unicode status icons** (1 connections) — `src/ansible_aom/core/icons.py`
- **Get the current animation frame for RUNNING status.      Cycles through the 4 qu** (1 connections) — `src/ansible_aom/core/icons.py`
- **True if stdout claims a UTF-family encoding.      Used by the compact renderer t** (1 connections) — `src/ansible_aom/core/icons.py`
- **Tests for ASCII fallback in the compact renderer (TC-060 / TC-377).  The status** (1 connections) — `tests/compact/test_ascii_fallback.py`
- **Some pipe wrappers expose `encoding = None` — be defensive.** (1 connections) — `tests/compact/test_ascii_fallback.py`
- **Running spinner (◐→◓→◑→◒) animates across renders.  Previously ``format_tree_blo** (1 connections) — `tests/compact/test_spinner_animation.py`
- **Existing callers that don't pass animation_frame still render.** (1 connections) — `tests/compact/test_spinner_animation.py`

## Relationships

- [renderer.py](renderer.py.md) (8 shared connections)
- [HostRunState](HostRunState.md) (6 shared connections)
- [format_status_bar](format_status_bar.md) (3 shared connections)
- [.from_run_state](from_run_state.md) (2 shared connections)
- [format_tree_block](format_tree_block.md) (2 shared connections)
- [Error Handling Tests](Error_Handling_Tests.md) (2 shared connections)
- [Dirty Flag Throttle](Dirty_Flag_Throttle.md) (1 shared connections)
- [Warning Pattern Classification](Warning_Pattern_Classification.md) (1 shared connections)
- [Pydantic Model Basics](Pydantic_Model_Basics.md) (1 shared connections)
- [Ansible Args Validation](Ansible_Args_Validation.md) (1 shared connections)
- [test_icons.py](test_icons.py.md) (1 shared connections)
- [Crash Recovery Notification](Crash_Recovery_Notification.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/icons.py`
- `tests/compact/test_ascii_fallback.py`
- `tests/compact/test_spinner_animation.py`

## Audit Trail

- EXTRACTED: 76 (94%)
- INFERRED: 5 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*