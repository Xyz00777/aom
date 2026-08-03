# Conftest Fixture Validation

> 22 nodes · cohesion 0.15

## Key Concepts

- **test_throttle.py** (9 connections) — `tests/integration/test_throttle.py`
- **_run_aom()** (8 connections) — `tests/integration/test_throttle.py`
- **TestThrottleAwareness** (7 connections) — `tests/integration/test_throttle.py`
- **_find_session()** (6 connections) — `tests/integration/test_throttle.py`
- **Path** (6 connections)
- **.test_throttle_cap_recorded_on_task_definition()** (6 connections) — `tests/integration/test_throttle.py`
- **.test_wave_assignment_matches_host_bursts()** (6 connections) — `tests/integration/test_throttle.py`
- **_parse_jsonl_through_core()** (5 connections) — `tests/integration/test_throttle.py`
- **.test_wave_progress_records_three_waves()** (5 connections) — `tests/integration/test_throttle.py`
- **_ansible_collection_paths()** (3 connections) — `tests/integration/test_throttle.py`
- **_has_ansible_posix()** (2 connections) — `tests/integration/test_throttle.py`
- **CompletedProcess** (1 connections)
- **Real-ansible throttle awareness test (RED — TDD failing test).  This test is **i** (1 connections) — `tests/integration/test_throttle.py`
- **Spawn ``python -m ansible_aom <playbook>`` against a sandboxed HOME.      The fi** (1 connections) — `tests/integration/test_throttle.py`
- **Return the lone session directory under ``home_dir`` or fail loudly.** (1 connections) — `tests/integration/test_throttle.py`
- **Feed each recorded line through ``JsonLineStream``.      Same code path the live** (1 connections) — `tests/integration/test_throttle.py`
- **Behavioural contract: aom must surface ``throttle:`` and wave progress.      Run** (1 connections) — `tests/integration/test_throttle.py`
- **``TaskDefinition.throttle == 2`` for the throttled task after the run.** (1 connections) — `tests/integration/test_throttle.py`
- **``RunState.wave_progress.wave_count == 3`` for 6 hosts @ throttle 2.          6** (1 connections) — `tests/integration/test_throttle.py`
- **``RunState.wave_progress.per_host`` matches the observed burst pattern.** (1 connections) — `tests/integration/test_throttle.py`
- **Search-path entries reported by ``ansible-galaxy collection list``.      Mirror** (1 connections) — `tests/integration/test_throttle.py`
- **True if ``ansible.posix`` is installed and discoverable.      Without it the JSO** (1 connections) — `tests/integration/test_throttle.py`

## Relationships

- [JsonLineStream](JsonLineStream.md) (2 shared connections)
- [TaskDefinition](TaskDefinition.md) (2 shared connections)
- [StreamPhase](StreamPhase.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)

## Source Files

- `tests/integration/test_throttle.py`

## Audit Trail

- EXTRACTED: 71 (96%)
- INFERRED: 3 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*