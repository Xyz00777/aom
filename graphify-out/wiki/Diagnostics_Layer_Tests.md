# Diagnostics Layer Tests

> 19 nodes · cohesion 0.15

## Key Concepts

- **test_event_source.py** (11 connections) — `tests/unit/test_event_source.py`
- **ReplayDriver** (10 connections) — `src/ansible_aom/drivers/replay.py`
- **test_live_driver_drives_renderer_with_fake_subprocess()** (6 connections) — `tests/unit/test_event_source.py`
- **test_replay_driver_drives_renderer_end_to_end()** (6 connections) — `tests/unit/test_event_source.py`
- **_write_session()** (6 connections) — `tests/unit/test_event_source.py`
- **Path** (5 connections)
- **test_replay_driver_missing_session_returns_1()** (5 connections) — `tests/unit/test_event_source.py`
- **test_replay_driver_satisfies_event_source()** (5 connections) — `tests/unit/test_event_source.py`
- **.drive()** (4 connections) — `src/ansible_aom/drivers/replay.py`
- **Path** (2 connections)
- **.__init__()** (2 connections) — `src/ansible_aom/drivers/replay.py`
- **Re-stream a previously recorded session through a :class:`Renderer`.      Mirror** (1 connections) — `src/ansible_aom/drivers/replay.py`
- **.session_id()** (1 connections) — `src/ansible_aom/drivers/replay.py`
- **MonkeyPatch** (1 connections)
- **Tests for the EventSource Protocol and its two production drivers.  The Protocol** (1 connections) — `tests/unit/test_event_source.py`
- **Drive a synthetic 2-event session into a FakeRenderer and assert     the full Re** (1 connections) — `tests/unit/test_event_source.py`
- **Replay against a non-existent session id propagates a 1 exit code.** (1 connections) — `tests/unit/test_event_source.py`
- **A LiveDriver should drive renderer.start -> events -> completion when     the ru** (1 connections) — `tests/unit/test_event_source.py`
- **Materialise a minimum-viable session directory the replay loader will accept.** (1 connections) — `tests/unit/test_event_source.py`

## Relationships

- [Narrow Terminal View](Narrow_Terminal_View.md) (6 shared connections)
- [Rerun Main Function](Rerun_Main_Function.md) (4 shared connections)
- [Hide State Normalization](Hide_State_Normalization.md) (2 shared connections)
- [State Machine Happy Path](State_Machine_Happy_Path.md) (2 shared connections)
- [Community 504](Community_504.md) (1 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Debug Diagnostics Summary](Debug_Diagnostics_Summary.md) (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/replay.py`
- `tests/unit/test_event_source.py`

## Audit Trail

- EXTRACTED: 61 (87%)
- INFERRED: 9 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*