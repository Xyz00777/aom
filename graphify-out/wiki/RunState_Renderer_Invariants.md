# RunState Renderer Invariants

> 30 nodes · cohesion 0.08

## Key Concepts

- **RendererMirrorMachine** (25 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **._next_ts()** (9 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.runner_on_start()** (3 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.task_def_index_matches_definitions()** (3 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.tasks_completed_matches_oracle()** (3 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.tasks_seen_matches_oracle()** (3 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **_ts()** (3 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.completed_ids_are_actually_terminal()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.completed_ids_subset_of_known_tasks()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.play_def_by_name_matches_definitions()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.play_start()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.projection_cache_references_current_state()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.runner_on_failed()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.runner_on_ok()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.runner_on_skipped()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.runner_on_unreachable()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.task_start()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **.tick()** (2 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **RuleBasedStateMachine** (1 connections)
- **Free-strategy entry point — task_id appears via runner_on_start.** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **Quiet-period refresh; must not perturb any counter or index.** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **HS-2: incremental counter == authoritative full-state walk.** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **HS-2: ``_tasks_seen`` is the renderer-side denominator floor.          The statu** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **Every id we counted as completed must still exist in state.** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **A task id in ``_completed_task_ids`` must have no RUNNING hosts.          Counte** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- *... and 5 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (3 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (3 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)
- [Renderer Stats Parity](Renderer_Stats_Parity.md) (1 shared connections)
- [._render_status_panel](_render_status_panel.md) (1 shared connections)

## Source Files

- `tests/unit/test_invariants_runstate_renderer.py`

## Audit Trail

- EXTRACTED: 76 (92%)
- INFERRED: 7 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*