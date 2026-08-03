# test_live_driver_drives_renderer_with_fake_subprocess

> 4 nodes · cohesion 0.50

## Key Concepts

- **test_live_driver_drives_renderer_with_fake_subprocess()** (7 connections) — `tests/unit/test_event_source.py`
- **.playbook()** (4 connections) — `src/ansible_aom/drivers/live.py`
- **MonkeyPatch** (1 connections)
- **A LiveDriver should drive renderer.start -> events -> completion when     the ru** (1 connections) — `tests/unit/test_event_source.py`

## Relationships

- [Renderer](Renderer.md) (2 shared connections)
- [test_event_source.py](test_event_source.py.md) (2 shared connections)
- [Host Collection Helpers](Host_Collection_Helpers.md) (1 shared connections)
- [_FakeSpawn](_FakeSpawn.md) (1 shared connections)
- [FakeRenderer](FakeRenderer.md) (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/live.py`
- `tests/unit/test_event_source.py`

## Audit Trail

- EXTRACTED: 8 (62%)
- INFERRED: 5 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*