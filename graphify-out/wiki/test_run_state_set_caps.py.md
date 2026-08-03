# test_run_state_set_caps.py

> 11 nodes · cohesion 0.18

## Key Concepts

- **test_run_state_set_caps.py** (8 connections) — `tests/unit/test_run_state_set_caps.py`
- **test_grafted_role_names_capped()** (3 connections) — `tests/unit/test_run_state_set_caps.py`
- **test_grafted_uuids_capped_at_max_tasks_per_play()** (3 connections) — `tests/unit/test_run_state_set_caps.py`
- **test_play_window_counts_capped_at_max_plays()** (3 connections) — `tests/unit/test_run_state_set_caps.py`
- **test_unknown_events_keys_naturally_bounded()** (3 connections) — `tests/unit/test_run_state_set_caps.py`
- **R15 — cap unbounded RunState sets.  R15 spec: ``RunState`` carries several set/d** (1 connections) — `tests/unit/test_run_state_set_caps.py`
- **R15: ``_grafted_uuids`` does not exceed ``MAX_TASKS_PER_PLAY``.** (1 connections) — `tests/unit/test_run_state_set_caps.py`
- **R15: ``_grafted_role_names`` is bounded (some reasonable N).** (1 connections) — `tests/unit/test_run_state_set_caps.py`
- **R15: ``_play_window_counts`` is bounded at ``MAX_PLAYS``.** (1 connections) — `tests/unit/test_run_state_set_caps.py`
- **R15: ``unknown_events`` keys are bounded by event-type cardinality.      The JSO** (1 connections) — `tests/unit/test_run_state_set_caps.py`
- **_ts()** (1 connections) — `tests/unit/test_run_state_set_caps.py`

## Relationships

- [RunState](RunState.md) (4 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [state_machine.py](state_machine.py.md) (1 shared connections)

## Source Files

- `tests/unit/test_run_state_set_caps.py`

## Audit Trail

- EXTRACTED: 26 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*