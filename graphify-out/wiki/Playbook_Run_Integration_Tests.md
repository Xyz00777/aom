# Playbook Run Integration Tests

> 39 nodes · cohesion 0.15

## Key Concepts

- **_renderer()** (20 connections) — `tests/compact/test_loop_item_streaming.py`
- **_task_start()** (19 connections) — `tests/compact/test_loop_item_streaming.py`
- **test_loop_item_streaming.py** (16 connections) — `tests/compact/test_loop_item_streaming.py`
- **_all_text()** (15 connections) — `tests/compact/test_loop_item_streaming.py`
- **TestItemEventTypeIsAuthoritative** (9 connections) — `tests/compact/test_loop_item_streaming.py`
- **_aom_jsonl_item_event()** (8 connections) — `tests/compact/test_loop_item_streaming.py`
- **_item_event()** (8 connections) — `tests/compact/test_loop_item_streaming.py`
- **_logged()** (8 connections) — `tests/compact/test_loop_item_streaming.py`
- **TestAsyncPollDoesNotLeakDictIntoItemLabel** (7 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_streamed_items_not_duplicated_by_aggregate()** (7 connections) — `tests/compact/test_loop_item_streaming.py`
- **TestItemEventRendersImmediately** (7 connections) — `tests/compact/test_loop_item_streaming.py`
- **_async_poll_payload()** (6 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_aggregate_still_expands_without_streamed_items()** (6 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_ok_item_still_uses_changed_flag()** (6 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_async_poll_failed_does_not_leak_dict_into_item_label()** (5 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_async_poll_failed_label_is_red()** (5 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_async_poll_failed_stays_compact_one_line()** (5 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_async_poll_in_flight_does_not_render_as_item()** (5 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_changed_item_streams_one_line()** (5 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_failed_item_streams_with_msg()** (5 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_item_colors_match_status()** (5 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_ok_item_streams_one_line()** (5 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_skipped_item_streams_one_line()** (5 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_failed_item_colors_red()** (5 connections) — `tests/compact/test_loop_item_streaming.py`
- **.test_failed_item_without_failed_flag_renders_failed()** (5 connections) — `tests/compact/test_loop_item_streaming.py`
- *... and 14 more nodes in this community*

## Relationships

- [CompactRenderer](CompactRenderer.md) (8 shared connections)
- [renderer.py](renderer.py.md) (1 shared connections)

## Source Files

- `tests/compact/test_loop_item_streaming.py`

## Audit Trail

- EXTRACTED: 230 (98%)
- INFERRED: 5 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*