# json.py

> 84 nodes · cohesion 0.04

## Key Concepts

- **json.py** (80 connections) — `src/ansible_aom/formats/json.py`
- **JsonlEvent** (66 connections) — `src/ansible_aom/core/event_types.py`
- **run_state.py** (63 connections) — `src/ansible_aom/core/run_state.py`
- **parse_iso_timestamp()** (19 connections) — `src/ansible_aom/core/timestamp.py`
- **drivers/replay.py** (19 connections) — `src/ansible_aom/drivers/replay.py`
- **_BoundedDict** (18 connections) — `src/ansible_aom/core/run_state.py`
- **_BoundedSet** (18 connections) — `src/ansible_aom/core/run_state.py`
- **event_types.py** (14 connections) — `src/ansible_aom/core/event_types.py`
- **JsonlTask** (14 connections) — `src/ansible_aom/core/event_types.py`
- **overhead.py** (13 connections) — `src/ansible_aom/core/overhead.py`
- **core/replay.py** (12 connections) — `src/ansible_aom/core/replay.py`
- **_parse_timestamp()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **RunSummary** (12 connections) — `src/ansible_aom/formats/json.py`
- **renderer/protocol.py** (11 connections) — `src/ansible_aom/renderer/protocol.py`
- **iter_tree_frames()** (10 connections) — `src/ansible_aom/core/replay.py`
- **timestamp.py** (10 connections) — `src/ansible_aom/core/timestamp.py`
- **JsonlHostResult** (8 connections) — `src/ansible_aom/core/event_types.py`
- **JsonlPlay** (8 connections) — `src/ansible_aom/core/event_types.py`
- **HostCounts** (8 connections) — `src/ansible_aom/formats/json.py`
- **TaskFailure** (8 connections) — `src/ansible_aom/formats/json.py`
- **.handle_completion()** (7 connections) — `src/ansible_aom/formats/json.py`
- **factory.py** (7 connections) — `src/ansible_aom/renderer/factory.py`
- **._event_time()** (6 connections) — `src/ansible_aom/compact/renderer.py`
- **_parse_iso8601()** (5 connections) — `src/ansible_aom/core/overhead.py`
- **_event_timestamp()** (5 connections) — `src/ansible_aom/core/replay.py`
- *... and 59 more nodes in this community*

## Relationships

- [RunState](RunState.md) (42 shared connections)
- [HostRunState](HostRunState.md) (27 shared connections)
- [._emit_event_log](_emit_event_log.md) (13 shared connections)
- [Color ASCII Fallback](Color_ASCII_Fallback.md) (10 shared connections)
- [TaskDefinition](TaskDefinition.md) (10 shared connections)
- [run_playbook](run_playbook.md) (9 shared connections)
- [load_session](load_session.md) (7 shared connections)
- [test_replay_determinism.py](test_replay_determinism.py.md) (6 shared connections)
- [test_run_summary_schema.py](test_run_summary_schema.py.md) (6 shared connections)
- [renderer.py](renderer.py.md) (5 shared connections)
- [StreamPhase](StreamPhase.md) (5 shared connections)
- [_safe_loads](_safe_loads.md) (5 shared connections)

## Source Files

- `src/ansible_aom/compact/renderer.py`
- `src/ansible_aom/core/event_types.py`
- `src/ansible_aom/core/overhead.py`
- `src/ansible_aom/core/replay.py`
- `src/ansible_aom/core/run_state.py`
- `src/ansible_aom/core/timestamp.py`
- `src/ansible_aom/drivers/replay.py`
- `src/ansible_aom/formats/json.py`
- `src/ansible_aom/renderer/factory.py`
- `src/ansible_aom/renderer/protocol.py`
- `tests/unit/test_event_processing.py`
- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 484 (88%)
- INFERRED: 69 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*