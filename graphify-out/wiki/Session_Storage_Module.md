# Session Storage Module

> 25 nodes · cohesion 0.12

## Key Concepts

- **test_session_store_async_write.py** (12 connections) — `tests/unit/test_session_store_async_write.py`
- **Path** (9 connections)
- **_break_events_file()** (5 connections) — `tests/unit/test_session_store_async_write.py`
- **test_queue_full_drops_event_and_counts()** (5 connections) — `tests/unit/test_session_store_async_write.py`
- **test_record_event_returns_quickly()** (5 connections) — `tests/unit/test_session_store_async_write.py`
- **test_write_failure_does_not_propagate()** (5 connections) — `tests/unit/test_session_store_async_write.py`
- **test_write_failure_surfaces_via_recording_failed()** (5 connections) — `tests/unit/test_session_store_async_write.py`
- **test_index_built_from_complete_events_after_end_session()** (4 connections) — `tests/unit/test_session_store_async_write.py`
- **test_interleaved_event_and_stderr_order_preserved()** (4 connections) — `tests/unit/test_session_store_async_write.py`
- **test_no_event_loss_and_order_on_end_session()** (4 connections) — `tests/unit/test_session_store_async_write.py`
- **test_recorded_event_persists_after_drain()** (4 connections) — `tests/unit/test_session_store_async_write.py`
- **.dropped_events()** (3 connections) — `src/ansible_aom/session/store.py`
- **_build_1mb_event()** (3 connections) — `tests/unit/test_session_store_async_write.py`
- **Total events dropped across all sessions because a queue was full.** (1 connections) — `src/ansible_aom/session/store.py`
- **R16 — async / non-blocking disk write in session/store.py.  R16 spec: the legacy** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **R16: ``end_session`` drains the writer, so every recorded event lands     on dis** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **R16: events and stderr lines share one writer, so their relative     order on di** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **Requirement: ``end_session`` flushes the writer BEFORE building the     sqlite i** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **Replace events.jsonl with a directory so the writer's ``open('ab')``     fails w** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **R16: a disk write failure in the background writer must never raise     out of `** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **R16: the writer's disk failure is observable through     ``recording_failed`` so** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **Produce a JSONL event whose serialised form is roughly 1 MB.** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **R16: ``record_event`` with a 1 MB event returns in < 10 ms.** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **R16: events are written to disk eventually (after the writer drains).** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **R16: when the writer falls behind, the bounded queue drops events.      We can't** (1 connections) — `tests/unit/test_session_store_async_write.py`

## Relationships

- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (9 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `src/ansible_aom/session/store.py`
- `tests/unit/test_session_store_async_write.py`

## Audit Trail

- EXTRACTED: 70 (88%)
- INFERRED: 10 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*