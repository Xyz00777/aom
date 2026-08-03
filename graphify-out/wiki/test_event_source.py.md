# test_event_source.py

> 22 nodes · cohesion 0.13

## Key Concepts

- **test_event_source.py** (13 connections) — `tests/unit/test_event_source.py`
- **EventSource** (9 connections) — `src/ansible_aom/drivers/protocol.py`
- **test_replay_driver_drives_renderer_end_to_end()** (6 connections) — `tests/unit/test_event_source.py`
- **_write_session()** (6 connections) — `tests/unit/test_event_source.py`
- **drivers/protocol.py** (5 connections) — `src/ansible_aom/drivers/protocol.py`
- **Path** (5 connections)
- **test_replay_driver_missing_session_returns_1()** (5 connections) — `tests/unit/test_event_source.py`
- **test_replay_driver_satisfies_event_source()** (5 connections) — `tests/unit/test_event_source.py`
- **test_live_driver_satisfies_event_source()** (4 connections) — `tests/unit/test_event_source.py`
- **.drive()** (3 connections) — `src/ansible_aom/drivers/protocol.py`
- **test_event_source_is_runtime_checkable()** (3 connections) — `tests/unit/test_event_source.py`
- **test_event_source_rejects_non_conforming()** (2 connections) — `tests/unit/test_event_source.py`
- **Protocol** (1 connections)
- **EventSource Protocol — the source-side port of the architecture.  See ``ARCHITEC** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **A producer of run events for a :class:`Renderer`.      Implementations own the f** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **Drive ``renderer`` to completion and return the run's exit code.          Contra** (1 connections) — `src/ansible_aom/drivers/protocol.py`
- **Tests for the EventSource Protocol and its two production drivers.  The Protocol** (1 connections) — `tests/unit/test_event_source.py`
- **``EventSource`` must be ``@runtime_checkable`` so structural checks work.      W** (1 connections) — `tests/unit/test_event_source.py`
- **LiveDriver is the production EventSource for ansible-playbook runs.** (1 connections) — `tests/unit/test_event_source.py`
- **Drive a synthetic 2-event session into a FakeRenderer and assert     the full Re** (1 connections) — `tests/unit/test_event_source.py`
- **Replay against a non-existent session id propagates a 1 exit code.** (1 connections) — `tests/unit/test_event_source.py`
- **Materialise a minimum-viable session directory the replay loader will accept.** (1 connections) — `tests/unit/test_event_source.py`

## Relationships

- [FakeRenderer](FakeRenderer.md) (5 shared connections)
- [json.py](json.py.md) (3 shared connections)
- [Renderer](Renderer.md) (3 shared connections)
- [ReplayDriver](ReplayDriver.md) (3 shared connections)
- [test_live_driver_drives_renderer_with_fake_subprocess](test_live_driver_drives_renderer_with_fake_subprocess.md) (2 shared connections)

## Source Files

- `src/ansible_aom/drivers/protocol.py`
- `tests/unit/test_event_source.py`

## Audit Trail

- EXTRACTED: 66 (87%)
- INFERRED: 10 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*