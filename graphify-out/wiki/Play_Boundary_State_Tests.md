# Play Boundary State Tests

> 25 nodes · cohesion 0.20

## Key Concepts

- **TestPlayBoundaryState** (16 connections) — `tests/unit/test_play_boundary_state.py`
- **_two_play_state()** (13 connections) — `tests/unit/test_play_boundary_state.py`
- **_start_play()** (11 connections) — `tests/unit/test_play_boundary_state.py`
- **_start_task()** (11 connections) — `tests/unit/test_play_boundary_state.py`
- **test_play_boundary_state.py** (9 connections) — `tests/unit/test_play_boundary_state.py`
- **_ts()** (8 connections) — `tests/unit/test_play_boundary_state.py`
- **.test_terminal_runner_events_route_to_task_owner_play()** (7 connections) — `tests/unit/test_play_boundary_state.py`
- **.test_free_strategy_prior_play_not_force_finalised()** (6 connections) — `tests/unit/test_play_boundary_state.py`
- **.test_runner_events_route_to_task_owner_play()** (6 connections) — `tests/unit/test_play_boundary_state.py`
- **.test_same_play_id_replace_keeps_completed_count()** (6 connections) — `tests/unit/test_play_boundary_state.py`
- **.test_same_play_id_replacement_keeps_tasks()** (6 connections) — `tests/unit/test_play_boundary_state.py`
- **_runner_ok()** (5 connections) — `tests/unit/test_play_boundary_state.py`
- **_runner_start()** (5 connections) — `tests/unit/test_play_boundary_state.py`
- **.test_cross_play_graft_cursor_resets_on_play_boundary()** (5 connections) — `tests/unit/test_play_boundary_state.py`
- **.test_linear_strategy_prior_play_still_force_finalised()** (5 connections) — `tests/unit/test_play_boundary_state.py`
- **.test_meta_task_force_completed_across_plays()** (5 connections) — `tests/unit/test_play_boundary_state.py`
- **_task_def()** (3 connections) — `tests/unit/test_play_boundary_state.py`
- **TC-BOUNDARY-1: Duplicate play_start for the same play_id must not         destro** (1 connections) — `tests/unit/test_play_boundary_state.py`
- **TC-BOUNDARY-2: Re-emitting the same play_start must preserve the         task co** (1 connections) — `tests/unit/test_play_boundary_state.py`
- **TC-BOUNDARY-3: A RUNNING meta task from play 1 must be force-         completed** (1 connections) — `tests/unit/test_play_boundary_state.py`
- **TC-BOUNDARY-4: The dynamic-graft cursor ``_last_matched_task_def``         must** (1 connections) — `tests/unit/test_play_boundary_state.py`
- **TC-BOUNDARY-5: Under ``strategy: free`` a play_start for play N         can arri** (1 connections) — `tests/unit/test_play_boundary_state.py`
- **TC-BOUNDARY-6: The free-strategy skip must NOT regress the linear         case —** (1 connections) — `tests/unit/test_play_boundary_state.py`
- **TC-BOUNDARY-7: A ``v2_runner_on_*`` event that arrives WITHOUT a         ``play`** (1 connections) — `tests/unit/test_play_boundary_state.py`
- **TC-BOUNDARY-8: A terminal ``v2_runner_on_ok`` event that arrives         WITHOUT** (1 connections) — `tests/unit/test_play_boundary_state.py`

## Relationships

- [[Run State Summary Panel]] (6 shared connections)
- [[Run State Completion Recap]] (3 shared connections)
- [[Task Definition Live Refresh]] (2 shared connections)
- [[Play Definition Tree Population]] (2 shared connections)
- [[Run History Mining]] (1 shared connections)
- [[Role Group Task Models]] (1 shared connections)

## Source Files

- `tests/unit/test_play_boundary_state.py`

## Audit Trail

- EXTRACTED: 127 (94%)
- INFERRED: 8 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*