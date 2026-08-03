# _AsyncEventWriter

> 32 nodes · cohesion 0.07

## Key Concepts

- **_AsyncEventWriter** (12 connections) — `src/ansible_aom/session/store.py`
- **.record_event()** (5 connections) — `src/ansible_aom/session/store.py`
- **.record_stderr()** (5 connections) — `src/ansible_aom/session/store.py`
- **._writer_for()** (5 connections) — `src/ansible_aom/session/store.py`
- **.enqueue()** (4 connections) — `src/ansible_aom/session/store.py`
- **._run()** (4 connections) — `src/ansible_aom/session/store.py`
- **.create_artifact()** (4 connections) — `src/ansible_aom/session/store.py`
- **.end_session()** (4 connections) — `src/ansible_aom/session/store.py`
- **.flush()** (4 connections) — `src/ansible_aom/session/store.py`
- **._drain_after_failure()** (3 connections) — `src/ansible_aom/session/store.py`
- **.shutdown()** (3 connections) — `src/ansible_aom/session/store.py`
- **._write_diagnostics_json()** (3 connections) — `src/ansible_aom/session/store.py`
- **.dropped()** (2 connections) — `src/ansible_aom/session/store.py`
- **.error()** (2 connections) — `src/ansible_aom/session/store.py`
- **.flush()** (2 connections) — `src/ansible_aom/session/store.py`
- **.__init__()** (2 connections) — `src/ansible_aom/session/store.py`
- **._set_error()** (2 connections) — `src/ansible_aom/session/store.py`
- **Classify *line* and persist it as an ``aom_stderr_line`` event.          Phase 4** (2 connections) — `src/ansible_aom/session/store.py`
- **Background thread that drains events onto disk.      R16: ``record_event`` enque** (1 connections) — `src/ansible_aom/session/store.py`
- **Enqueue a serialised JSONL line. Returns immediately.          Drops the line an** (1 connections) — `src/ansible_aom/session/store.py`
- **Cumulative count of events dropped because the queue was full.** (1 connections) — `src/ansible_aom/session/store.py`
- **Reason string if the writer thread hit a disk error, else None.          Set onc** (1 connections) — `src/ansible_aom/session/store.py`
- **Wait until the queue is fully drained.          Used by tests that need to asser** (1 connections) — `src/ansible_aom/session/store.py`
- **Signal the writer thread to drain and exit.** (1 connections) — `src/ansible_aom/session/store.py`
- **Consume the rest of the queue as no-ops after a disk error.          We can't wr** (1 connections) — `src/ansible_aom/session/store.py`
- *... and 7 more nodes in this community*

## Relationships

- [SessionManager](SessionManager.md) (7 shared connections)
- [load_session](load_session.md) (4 shared connections)
- [Prompt Detection Heuristics](Prompt_Detection_Heuristics.md) (1 shared connections)

## Source Files

- `src/ansible_aom/session/store.py`

## Audit Trail

- EXTRACTED: 82 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*