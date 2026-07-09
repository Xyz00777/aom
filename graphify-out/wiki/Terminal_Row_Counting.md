# Terminal Row Counting

> 34 nodes · cohesion 0.11

## Key Concepts

- **CallbackModule** (12 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **_make_released()** (11 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **_connection_id()** (10 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **_make_acquired()** (9 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **aom_connection.py** (7 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **._write_event()** (6 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **TestConnectionId** (6 connections) — `tests/unit/test_aom_connection.py`
- **TestEventConstruction** (6 connections) — `tests/unit/test_aom_connection.py`
- **_timestamp()** (5 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **test_aom_connection.py** (5 connections) — `tests/unit/test_aom_connection.py`
- **TestFileWriting** (4 connections) — `tests/unit/test_aom_connection.py`
- **.v2_runner_on_failed()** (3 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **.v2_runner_on_ok()** (3 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **.v2_runner_on_skipped()** (3 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **.v2_runner_on_start()** (3 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **.v2_runner_on_unreachable()** (3 connections) — `src/ansible_aom/callbacks/aom_connection.py`
- **.test_acquire_release_share_connection_id()** (3 connections) — `tests/unit/test_aom_connection.py`
- **.test_acquired_event_shape()** (3 connections) — `tests/unit/test_aom_connection.py`
- **.test_released_event_shape()** (3 connections) — `tests/unit/test_aom_connection.py`
- **.test_write_event_to_temp_file()** (3 connections) — `tests/unit/test_aom_connection.py`
- **.test_deterministic_for_same_pair()** (2 connections) — `tests/unit/test_aom_connection.py`
- **.test_differs_for_different_hosts()** (2 connections) — `tests/unit/test_aom_connection.py`
- **.test_differs_for_different_task_uuids()** (2 connections) — `tests/unit/test_aom_connection.py`
- **.test_returns_valid_uuid_string()** (2 connections) — `tests/unit/test_aom_connection.py`
- **.test_timestamp_format()** (2 connections) — `tests/unit/test_aom_connection.py`
- *... and 9 more nodes in this community*

## Relationships

- [StreamPhase Enum](StreamPhase_Enum.md) (2 shared connections)

## Source Files

- `src/ansible_aom/callbacks/aom_connection.py`
- `tests/unit/test_aom_connection.py`

## Audit Trail

- EXTRACTED: 94 (73%)
- INFERRED: 34 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*