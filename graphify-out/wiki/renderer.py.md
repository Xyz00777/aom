# renderer.py

> 48 nodes · cohesion 0.07

## Key Concepts

- **renderer.py** (106 connections) — `src/ansible_aom/compact/renderer.py`
- **format.py** (60 connections) — `src/ansible_aom/compact/format.py`
- **_wrap()** (19 connections) — `src/ansible_aom/compact/format.py`
- **format_host_summary()** (14 connections) — `src/ansible_aom/compact/format.py`
- **TestHostSummaryColors** (12 connections) — `tests/compact/test_status_bar_colors.py`
- **test_status_bar_colors.py** (10 connections) — `tests/compact/test_status_bar_colors.py`
- **TestColorEnabled** (10 connections) — `tests/compact/test_status_bar_colors.py`
- **_truncate_msg()** (8 connections) — `src/ansible_aom/compact/format.py`
- **._format_loop_item_line()** (8 connections) — `src/ansible_aom/compact/renderer.py`
- **_color_enabled()** (7 connections) — `src/ansible_aom/compact/format.py`
- **is_async_poll_payload()** (7 connections) — `src/ansible_aom/core/_async_poll.py`
- **test_invariants_runstate_renderer.py** (7 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **_truncate_visible()** (6 connections) — `src/ansible_aom/compact/format.py`
- **_verbose_ok_body()** (6 connections) — `src/ansible_aom/compact/format.py`
- **_format_count_cells()** (5 connections) — `src/ansible_aom/compact/format.py`
- **_extract_error_msg()** (5 connections) — `src/ansible_aom/compact/renderer.py`
- **_count_cell()** (4 connections) — `src/ansible_aom/compact/format.py`
- **_async_poll.py** (4 connections) — `src/ansible_aom/core/_async_poll.py`
- **_first_line()** (3 connections) — `src/ansible_aom/compact/renderer.py`
- **test_truncate_visible_plain_mode_emits_no_sgr()** (3 connections) — `tests/compact/test_tree_render.py`
- **Render non-zero status count cells.      Order: ok, changed, skipped, failed, un** (2 connections) — `src/ansible_aom/compact/format.py`
- **.test_off_when_no_color_set_even_for_tty()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_off_when_not_a_tty()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_on_when_tty_and_no_color_unset()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- **.test_changed_segment_is_yellow()** (2 connections) — `tests/compact/test_status_bar_colors.py`
- *... and 23 more nodes in this community*

## Relationships

- [HostRunState](HostRunState.md) (22 shared connections)
- [._emit_event_log](_emit_event_log.md) (12 shared connections)
- [PlayDefinition](PlayDefinition.md) (10 shared connections)
- [format_status_bar](format_status_bar.md) (10 shared connections)
- [.from_run_state](from_run_state.md) (8 shared connections)
- [icons.py](icons.py.md) (8 shared connections)
- [CompactRenderer](CompactRenderer.md) (8 shared connections)
- [_compute_mode_label](_compute_mode_label.md) (6 shared connections)
- [format_tree_block](format_tree_block.md) (6 shared connections)
- [RunProgress](RunProgress.md) (6 shared connections)
- [format_preflight_summary](format_preflight_summary.md) (5 shared connections)
- [format_age](format_age.md) (5 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`
- `src/ansible_aom/core/_async_poll.py`
- `tests/compact/test_status_bar_colors.py`
- `tests/compact/test_tree_render.py`
- `tests/unit/test_invariants_runstate_renderer.py`

## Audit Trail

- EXTRACTED: 308 (90%)
- INFERRED: 34 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*