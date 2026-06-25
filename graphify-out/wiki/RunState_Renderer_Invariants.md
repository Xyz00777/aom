# RunState Renderer Invariants

> 34 nodes · cohesion 0.07

## Key Concepts

- **RendererMirrorMachine** (25 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **._next_ts()** (9 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **test_invariants_runstate_renderer.py** (4 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **_renderer()** (4 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.runner_on_start()** (3 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.task_def_index_matches_definitions()** (3 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.tasks_completed_matches_oracle()** (3 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.tasks_seen_matches_oracle()** (3 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **_ts()** (3 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.completed_ids_are_actually_terminal()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.completed_ids_subset_of_known_tasks()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.__init__()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.play_def_by_name_matches_definitions()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.play_start()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.projection_cache_references_current_state()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.runner_on_failed()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.runner_on_ok()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.runner_on_skipped()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.runner_on_unreachable()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.task_start()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.tick()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **Stateful invariants over RunState and the CompactRenderer mirror.  The HS-2..HS-** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **Free-strategy entry point — task_id appears via runner_on_start.** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **Quiet-period refresh; must not perturb any counter or index.** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **HS-2: incremental counter == authoritative full-state walk.** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- *... and 9 more nodes in this community*

## Relationships

- [[Compact Renderer Implementation]] (2 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Play Definition Tree Population]] (2 shared connections)
- [[Task Definition Live Refresh]] (1 shared connections)
- [[State Machine Invariants]] (1 shared connections)
- [[Run State Completion Recap]] (1 shared connections)
- [[Total Task Counting]] (1 shared connections)

## Source Files

- `tests/unit/test_invariants_runstate_renderer.py`

## Audit Trail

- EXTRACTED: 87 (93%)
- INFERRED: 7 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*