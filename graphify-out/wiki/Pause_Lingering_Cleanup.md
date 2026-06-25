# Pause Lingering Cleanup

> 10 nodes · cohesion 0.40

## Key Concepts

- **TestPauseLingerCleared** (8 connections) — `tests/unit/test_pause_lingering_cleanup.py`
- **_state_with_two_plays()** (6 connections) — `tests/unit/test_pause_lingering_cleanup.py`
- **test_pause_lingering_cleanup.py** (5 connections) — `tests/unit/test_pause_lingering_cleanup.py`
- **.test_completed_prior_task_status_preserved()** (5 connections) — `tests/unit/test_pause_lingering_cleanup.py`
- **.test_tree_shows_no_running_pause_during_second_play()** (5 connections) — `tests/unit/test_pause_lingering_cleanup.py`
- **_play_start()** (4 connections) — `tests/unit/test_pause_lingering_cleanup.py`
- **_task_start()** (4 connections) — `tests/unit/test_pause_lingering_cleanup.py`
- **.test_pause_host_cleared_when_next_play_starts()** (4 connections) — `tests/unit/test_pause_lingering_cleanup.py`
- **Regression: a pause task that is the last task of its play must not linger as RU** (1 connections) — `tests/unit/test_pause_lingering_cleanup.py`
- **Finalising a prior play must not stomp hosts that already have a         termina** (1 connections) — `tests/unit/test_pause_lingering_cleanup.py`

## Relationships

- [[Play Definition Tree Population]] (3 shared connections)
- [[Run State Summary Panel]] (2 shared connections)
- [[Role Group Task Models]] (1 shared connections)
- [[Tree Projection Logic]] (1 shared connections)

## Source Files

- `tests/unit/test_pause_lingering_cleanup.py`

## Audit Trail

- EXTRACTED: 38 (88%)
- INFERRED: 5 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*