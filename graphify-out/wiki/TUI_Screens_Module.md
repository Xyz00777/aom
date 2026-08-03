# TUI Screens Module

> 13 nodes · cohesion 0.15

## Key Concepts

- **test_run_state_set_caps.py** (8 connections) — `tests/unit/test_run_state_set_caps.py`
- **state_machine.py** (7 connections) — `src/ansible_aom/core/state_machine.py`
- **test_grafted_role_names_capped()** (3 connections) — `tests/unit/test_run_state_set_caps.py`
- **test_grafted_uuids_capped_at_max_tasks_per_play()** (3 connections) — `tests/unit/test_run_state_set_caps.py`
- **test_play_window_counts_capped_at_max_plays()** (3 connections) — `tests/unit/test_run_state_set_caps.py`
- **test_unknown_events_keys_naturally_bounded()** (3 connections) — `tests/unit/test_run_state_set_caps.py`
- **Memory bounds constants for AOM.  This module previously also housed an ``Execut** (1 connections) — `src/ansible_aom/core/state_machine.py`
- **R15 — cap unbounded RunState sets.  R15 spec: ``RunState`` carries several set/d** (1 connections) — `tests/unit/test_run_state_set_caps.py`
- **R15: ``_grafted_uuids`` does not exceed ``MAX_TASKS_PER_PLAY``.** (1 connections) — `tests/unit/test_run_state_set_caps.py`
- **R15: ``_grafted_role_names`` is bounded (some reasonable N).** (1 connections) — `tests/unit/test_run_state_set_caps.py`
- **R15: ``_play_window_counts`` is bounded at ``MAX_PLAYS``.** (1 connections) — `tests/unit/test_run_state_set_caps.py`
- **R15: ``unknown_events`` keys are bounded by event-type cardinality.      The JSO** (1 connections) — `tests/unit/test_run_state_set_caps.py`
- **_ts()** (1 connections) — `tests/unit/test_run_state_set_caps.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (4 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (2 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [Session Diff Comparison](Session_Diff_Comparison.md) (1 shared connections)
- [JSONL Event Parsing](JSONL_Event_Parsing.md) (1 shared connections)
- [Task Tree Truncation](Task_Tree_Truncation.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/state_machine.py`
- `tests/unit/test_run_state_set_caps.py`

## Audit Trail

- EXTRACTED: 30 (88%)
- INFERRED: 4 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*