# Loop Item Line Tests

> 36 nodes · cohesion 0.06

## Key Concepts

- **_AsyncEventWriter** (12 connections) — `src/ansible_aom/session/store.py`
- **Path** (9 connections)
- **.record_event()** (5 connections) — `src/ansible_aom/session/store.py`
- **.record_stderr()** (5 connections) — `src/ansible_aom/session/store.py`
- **._writer_for()** (5 connections) — `src/ansible_aom/session/store.py`
- **.enqueue()** (4 connections) — `src/ansible_aom/session/store.py`
- **._run()** (4 connections) — `src/ansible_aom/session/store.py`
- **Any** (4 connections)
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
- **.__init__()** (2 connections) — `src/ansible_aom/session/store.py`
- **.session_dir()** (2 connections) — `src/ansible_aom/session/store.py`
- **Background thread that drains events onto disk.      R16: ``record_event`` enque** (1 connections) — `src/ansible_aom/session/store.py`
- **Enqueue a serialised JSONL line. Returns immediately.          Drops the line an** (1 connections) — `src/ansible_aom/session/store.py`
- **Cumulative count of events dropped because the queue was full.** (1 connections) — `src/ansible_aom/session/store.py`
- *... and 11 more nodes in this community*

## Relationships

- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (11 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (3 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (2 shared connections)
- [Include Role Discovery](Include_Role_Discovery.md) (2 shared connections)
- [Prompt Detection Heuristics](Prompt_Detection_Heuristics.md) (1 shared connections)

## Source Files

- `src/ansible_aom/session/store.py`

## Audit Trail

- EXTRACTED: 98 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*