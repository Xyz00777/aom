# Status Bar Liveness Tests

> 28 nodes · cohesion 0.11

## Key Concepts

- **LivenessState** (27 connections) — `src/ansible_aom/core/heartbeat.py`
- **test_status_bar_liveness.py** (18 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_live_cpu_annotated_with_cpu_marker()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_live_pty_has_no_reason_annotation()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_reason_annotation_is_dim_when_colorized()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_segment_inserted_directly_before_elapsed_no_separator_after_predecessor()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_stuck_carries_no_reason_annotation()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_working_cpu_annotated_with_cpu_marker()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_working_silent_annotated_with_silent_marker()** (3 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_ascii_mode_falls_back_to_plain_glyphs()** (2 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_live_segment_is_green_when_colorized()** (2 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_live_segment_rendered_with_dot_and_age()** (2 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_no_color_in_segment_when_colorize_off()** (2 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_segment_present_even_with_zero_deprecations_and_warnings()** (2 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_stuck_segment_is_red_when_colorized()** (2 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_stuck_segment_rendered_with_bang()** (2 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_working_segment_is_dim_when_colorized()** (2 connections) — `tests/compact/test_status_bar_liveness.py`
- **test_working_segment_rendered_with_open_circle()** (2 connections) — `tests/compact/test_status_bar_liveness.py`
- **Tests for the liveness segment in ``format_status_bar``.  When a ``LivenessState** (1 connections) — `tests/compact/test_status_bar_liveness.py`
- **The common case (●, recent PTY bytes) carries no annotation —     the dot alone** (1 connections) — `tests/compact/test_status_bar_liveness.py`
- **LIVE rescued by CPU activity (no recent PTY but subprocess tree is     busy) — m** (1 connections) — `tests/compact/test_status_bar_liveness.py`
- **WORKING via byte-age alone: nothing positive to report. The     annotation tells** (1 connections) — `tests/compact/test_status_bar_liveness.py`
- **WORKING rescued from STUCK by an old-ish CPU sample (5–30s).** (1 connections) — `tests/compact/test_status_bar_liveness.py`
- **STUCK is unambiguous on its own — the red ! already says it all.** (1 connections) — `tests/compact/test_status_bar_liveness.py`
- **The (cpu)/(silent) suffix is metadata — render it dim so it     sits visually be** (1 connections) — `tests/compact/test_status_bar_liveness.py`
- *... and 3 more nodes in this community*

## Relationships

- [[Heartbeat Liveness Tracker]] (5 shared connections)
- [[Compact Renderer Formatters]] (1 shared connections)
- [[Compact Renderer Implementation]] (1 shared connections)
- [[Heartbeat Liveness Machine]] (1 shared connections)
- [[Terminal Row Counting]] (1 shared connections)
- [[Liveness State Reason]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/heartbeat.py`
- `tests/compact/test_status_bar_liveness.py`

## Audit Trail

- EXTRACTED: 55 (59%)
- INFERRED: 39 (41%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*