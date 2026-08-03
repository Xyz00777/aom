# Diagnostics Layer Tests

> 45 nodes · cohesion 0.06

## Key Concepts

- **FakeRenderer** (22 connections) — `tests/unit/test_event_source.py`
- **test_event_source.py** (13 connections) — `tests/unit/test_event_source.py`
- **ReplayDriver** (10 connections) — `src/ansible_aom/drivers/replay.py`
- **EventSource** (9 connections) — `src/ansible_aom/drivers/protocol.py`
- **test_live_driver_drives_renderer_with_fake_subprocess()** (7 connections) — `tests/unit/test_event_source.py`
- **test_replay_driver_drives_renderer_end_to_end()** (6 connections) — `tests/unit/test_event_source.py`
- **_write_session()** (6 connections) — `tests/unit/test_event_source.py`
- **drivers/protocol.py** (5 connections) — `src/ansible_aom/drivers/protocol.py`
- **Path** (5 connections)
- **test_replay_driver_missing_session_returns_1()** (5 connections) — `tests/unit/test_event_source.py`
- **test_replay_driver_satisfies_event_source()** (5 connections) — `tests/unit/test_event_source.py`
- **.drive()** (4 connections) — `src/ansible_aom/drivers/replay.py`
- **.drive()** (3 connections) — `src/ansible_aom/drivers/protocol.py`
- **Any** (3 connections)
- **test_event_source_is_runtime_checkable()** (3 connections) — `tests/unit/test_event_source.py`
- **Path** (2 connections)
- **.__init__()** (2 connections) — `src/ansible_aom/drivers/replay.py`
- **.set_definitions()** (2 connections) — `tests/unit/test_event_source.py`
- **.update_state()** (2 connections) — `tests/unit/test_event_source.py`
- **test_event_source_rejects_non_conforming()** (2 connections) — `tests/unit/test_event_source.py`
- **Protocol** (1 connections)
- **EventSource Protocol — the source-side port of the architecture.  See ``ARCHITEC** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **A producer of run events for a :class:`Renderer`.      Implementations own the f** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **Drive ``renderer`` to completion and return the run's exit code.          Contra** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **Re-stream a previously recorded session through a :class:`Renderer`.      Mirror** (1 connections) — `src/ansible_aom/drivers/replay.py`
- *... and 20 more nodes in this community*

## Relationships

- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (4 shared connections)
- [Debug Diagnostics Summary](Debug_Diagnostics_Summary.md) (4 shared connections)
- [Hide State Normalization](Hide_State_Normalization.md) (2 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (2 shared connections)
- [State Machine Happy Path](State_Machine_Happy_Path.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Status Bar Liveness Tests](Status_Bar_Liveness_Tests.md) (1 shared connections)
- [Session Diagnostics Writing](Session_Diagnostics_Writing.md) (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/protocol.py`
- `src/ansible_aom/drivers/replay.py`
- `tests/unit/test_event_source.py`

## Audit Trail

- EXTRACTED: 121 (86%)
- INFERRED: 20 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*