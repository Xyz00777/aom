# Credential String Sanitization

> 35 nodes · cohesion 0.09

## Key Concepts

- **reconstruct_pause_prompt()** (17 connections) — `src/ansible_aom/core/prompts.py`
- **TestReconstructPausePrompt** (15 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **looks_like_interactive_prompt()** (8 connections) — `src/ansible_aom/core/prompts.py`
- **prompts.py** (5 connections) — `src/ansible_aom/core/prompts.py`
- **_strip_ansi()** (4 connections) — `src/ansible_aom/core/prompts.py`
- **.test_ansi_colorized_block_is_rebuilt()** (4 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_folded_scalar_single_body_line_is_rebuilt()** (4 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_long_preview_anchors_on_marker_when_header_out_of_window()** (4 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_marker_only_block_without_header_is_rebuilt()** (4 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_header_beyond_lookback_is_none()** (3 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_header_preferred_over_marker_for_full_context()** (3 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_lone_colon_after_header_rebuilds_block()** (3 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_moderate_preview_includes_full_context_via_header()** (3 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_nearest_header_wins_for_second_pause()** (3 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_no_anchor_within_window_is_none()** (3 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_trailing_blank_line_is_none()** (3 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **test_pause_prompt_reconstruction.py** (2 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_empty_list_is_none()** (2 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_no_header_in_window_is_none()** (2 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **.test_tail_not_a_terminator_is_none()** (2 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- **Pure prompt-detection heuristics.  Two responsibilities, both pure (str in → boo** (1 connections) — `src/ansible_aom/core/prompts.py`
- **Rebuild a multi-line ``ansible.builtin.pause`` block from recent plaintext.** (1 connections) — `src/ansible_aom/core/prompts.py`
- **Remove SGR escape sequences from ``text``.** (1 connections) — `src/ansible_aom/core/prompts.py`
- **True if ``pending`` (unread PTY buffer) looks like a child waiting on stdin.** (1 connections) — `src/ansible_aom/core/prompts.py`
- **Tests for reconstruct_pause_prompt (multi-line ``|`` pause prompts).  A YAML ``|** (1 connections) — `tests/unit/test_pause_prompt_reconstruction.py`
- *... and 10 more nodes in this community*

## Relationships

- [Golden Frame Tests](Golden_Frame_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/prompts.py`
- `tests/unit/test_pause_prompt_reconstruction.py`

## Audit Trail

- EXTRACTED: 71 (65%)
- INFERRED: 38 (35%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*