# Failed Host Collection

> 20 nodes · cohesion 0.16

## Key Concepts

- **test_concurrent_inspect.py** (8 connections) — `tests/integration/test_concurrent_inspect.py`
- **.test_aom_inspect_during_active_writer()** (8 connections) — `tests/integration/test_concurrent_inspect.py`
- **.test_load_session_during_active_writer_does_not_raise()** (8 connections) — `tests/integration/test_concurrent_inspect.py`
- **Path** (6 connections)
- **_read_snapshot()** (6 connections) — `tests/integration/test_concurrent_inspect.py`
- **_writer_thread()** (6 connections) — `tests/integration/test_concurrent_inspect.py`
- **_build_session()** (5 connections) — `tests/integration/test_concurrent_inspect.py`
- **_run_aom_inspect()** (4 connections) — `tests/integration/test_concurrent_inspect.py`
- **TestInspectDuringWrite** (3 connections) — `tests/integration/test_concurrent_inspect.py`
- **TestLoadSessionDuringWrite** (3 connections) — `tests/integration/test_concurrent_inspect.py`
- **Any** (1 connections)
- **Concurrency test: writer + concurrent inspect (Phase 8 / Task 8.4).  What this t** (1 connections) — `tests/integration/test_concurrent_inspect.py`
- **Create ``<state_dir>/<session_id>/`` with a minimal meta.json.      Mirrors the** (1 connections) — `tests/integration/test_concurrent_inspect.py`
- **Append events to *events_file* at ~1000/sec until *stop* is set.      The writer** (1 connections) — `tests/integration/test_concurrent_inspect.py`
- **Invoke ``aom inspect --text --state-dir <state>`` and return the exit code.** (1 connections) — `tests/integration/test_concurrent_inspect.py`
- **Open the events file and return ``(well_formed_count, malformed_count, events)``** (1 connections) — `tests/integration/test_concurrent_inspect.py`
- **Concurrent writer + reader on the same events.jsonl.      The writer pushes ~100** (1 connections) — `tests/integration/test_concurrent_inspect.py`
- **The headline concurrency test.          Steps:           1. Create a session dir** (1 connections) — `tests/integration/test_concurrent_inspect.py`
- **``load_session`` is the lowest layer the inspect reader relies on.      This cla** (1 connections) — `tests/integration/test_concurrent_inspect.py`
- **``load_session`` returns a dict (not None, not raising) on every read.** (1 connections) — `tests/integration/test_concurrent_inspect.py`

## Relationships

- [Session Recording Tests](Session_Recording_Tests.md) (3 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Total Task Counting](Total_Task_Counting.md) (1 shared connections)

## Source Files

- `tests/integration/test_concurrent_inspect.py`

## Audit Trail

- EXTRACTED: 62 (93%)
- INFERRED: 5 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*