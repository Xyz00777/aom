# Loop Item Line Tests

> 32 nodes · cohesion 0.07

## Key Concepts

- **list_sessions()** (13 connections) — `src/ansible_aom/session/store.py`
- **store.py** (10 connections) — `src/ansible_aom/session/store.py`
- **_AsyncEventWriter** (8 connections) — `src/ansible_aom/session/store.py`
- **TestInspectList** (8 connections) — `tests/integration/test_session.py`
- **Any** (4 connections)
- **.test_list_sessions_empty()** (4 connections) — `tests/integration/test_session.py`
- **.test_list_sessions_includes_status()** (4 connections) — `tests/integration/test_session.py`
- **.test_list_sessions_returns_all_sessions()** (4 connections) — `tests/integration/test_session.py`
- **.test_list_sessions_shows_8_char_uuid_prefix()** (4 connections) — `tests/integration/test_session.py`
- **_lean_event()** (3 connections) — `src/ansible_aom/session/store.py`
- **.record_event()** (3 connections) — `src/ansible_aom/session/store.py`
- **.dropped()** (2 connections) — `src/ansible_aom/session/store.py`
- **.enqueue()** (2 connections) — `src/ansible_aom/session/store.py`
- **.flush()** (2 connections) — `src/ansible_aom/session/store.py`
- **.__init__()** (2 connections) — `src/ansible_aom/session/store.py`
- **._run()** (2 connections) — `src/ansible_aom/session/store.py`
- **.shutdown()** (2 connections) — `src/ansible_aom/session/store.py`
- **Session manager and artifact reader/writer.  File I/O for session recording, art** (1 connections) — `src/ansible_aom/session/store.py`
- **Background thread that drains events onto disk.      R16: ``record_event`` enque** (1 connections) — `src/ansible_aom/session/store.py`
- **Enqueue a serialised JSONL line. Returns immediately.          Drops the line an** (1 connections) — `src/ansible_aom/session/store.py`
- **Cumulative count of events dropped because the queue was full.** (1 connections) — `src/ansible_aom/session/store.py`
- **Wait until the queue is fully drained.          Used by tests that need to asser** (1 connections) — `src/ansible_aom/session/store.py`
- **Signal the writer thread to drain and exit.** (1 connections) — `src/ansible_aom/session/store.py`
- **Drain the queue, writing each line to events.jsonl.** (1 connections) — `src/ansible_aom/session/store.py`
- **Record a JSONL event to the session file.          Args:             session_id:** (1 connections) — `src/ansible_aom/session/store.py`
- *... and 7 more nodes in this community*

## Relationships

- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (12 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (2 shared connections)
- [Total Task Counting](Total_Task_Counting.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (1 shared connections)
- [Keybinding Context Coverage](Keybinding_Context_Coverage.md) (1 shared connections)
- [Compact Renderer Formatters](Compact_Renderer_Formatters.md) (1 shared connections)
- [PTY Buffer Stall Handling](PTY_Buffer_Stall_Handling.md) (1 shared connections)
- [Session Replay Round Trip](Session_Replay_Round_Trip.md) (1 shared connections)

## Source Files

- `src/ansible_aom/session/store.py`
- `tests/integration/test_session.py`

## Audit Trail

- EXTRACTED: 79 (86%)
- INFERRED: 13 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*