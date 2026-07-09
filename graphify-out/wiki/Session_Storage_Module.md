# Session Storage Module

> 11 nodes · cohesion 0.24

## Key Concepts

- **test_session_store_async_write.py** (6 connections) — `tests/unit/test_session_store_async_write.py`
- **test_record_event_returns_quickly()** (5 connections) — `tests/unit/test_session_store_async_write.py`
- **test_queue_full_drops_event_and_counts()** (4 connections) — `tests/unit/test_session_store_async_write.py`
- **test_recorded_event_persists_after_drain()** (4 connections) — `tests/unit/test_session_store_async_write.py`
- **_build_1mb_event()** (3 connections) — `tests/unit/test_session_store_async_write.py`
- **Path** (3 connections)
- **R16 — async / non-blocking disk write in session/store.py.  R16 spec: the legacy** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **Produce a JSONL event whose serialised form is roughly 1 MB.** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **R16: ``record_event`` with a 1 MB event returns in < 10 ms.** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **R16: events are written to disk eventually (after the writer drains).** (1 connections) — `tests/unit/test_session_store_async_write.py`
- **R16: when the writer falls behind, the bounded queue drops events.      We can't** (1 connections) — `tests/unit/test_session_store_async_write.py`

## Relationships

- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (3 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/unit/test_session_store_async_write.py`

## Audit Trail

- EXTRACTED: 27 (90%)
- INFERRED: 3 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*