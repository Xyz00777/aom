# RunState Renderer Invariants

> 35 nodes · cohesion 0.07

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
- **RuleBasedStateMachine** (1 connections)
- **Stateful invariants over RunState and the CompactRenderer mirror.  The HS-2..HS-** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **Free-strategy entry point — task_id appears via runner_on_start.** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- **Quiet-period refresh; must not perturb any counter or index.** (1 connections) — `tests/unit/test_invariants_runstate_renderer.py`
- *... and 10 more nodes in this community*

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (2 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (2 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)

## Source Files

- `tests/unit/test_invariants_runstate_renderer.py`

## Audit Trail

- EXTRACTED: 88 (93%)
- INFERRED: 7 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*