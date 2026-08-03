# Incremental Task Counters

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestPlayStart** (11 connections) — `tests/unit/test_event_processing.py`
- **.test_play_start_creates_play_run_state()** (4 connections) — `tests/unit/test_event_processing.py`
- **.test_play_start_existing_play_updates()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_play_start_sets_status_running()** (3 connections) — `tests/unit/test_event_processing.py`
- **Tests for v2_playbook_on_play_start handling (TC-201).** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-201: v2_playbook_on_play_start creates new PlayRunState.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-201 edge case: Same play.id updates existing PlayRunState.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-201: play status is set to RUNNING.** (1 connections) — `tests/unit/test_event_processing.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (5 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (4 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)

## Source Files

- `tests/unit/test_event_processing.py`

## Audit Trail

- EXTRACTED: 18 (72%)
- INFERRED: 7 (28%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*