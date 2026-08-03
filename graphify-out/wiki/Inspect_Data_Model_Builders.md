# Inspect Data Model Builders

> 47 nodes · cohesion 0.04

## Key Concepts

- **JsonRenderer** (77 connections) — `src/ansible_aom/formats/json.py`
- **TestInstallCompletionFlag** (13 connections) — `tests/unit/test_cli.py`
- **factory.py** (7 connections) — `src/ansible_aom/renderer/factory.py`
- **test_handle_completion_falls_back_to_wall_clock_when_state_lacks_timestamps()** (7 connections) — `tests/unit/test_json_renderer.py`
- **test_handle_completion_unreachable_lands_in_tasks_failed()** (7 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_satisfies_renderer_protocol()** (4 connections) — `tests/unit/test_json_renderer.py`
- **.handle_interactive_prompt()** (3 connections) — `src/ansible_aom/formats/json.py`
- **.handle_password_prompt()** (3 connections) — `src/ansible_aom/formats/json.py`
- **.start()** (3 connections) — `src/ansible_aom/formats/json.py`
- **.update_state()** (3 connections) — `src/ansible_aom/formats/json.py`
- **test_handle_completion_empty_state_emits_zero_exit()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_json_renderer_through_full_lifecycle()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_prompt_refusal_does_not_corrupt_completion_json()** (3 connections) — `tests/unit/test_json_renderer.py`
- **.add_warning()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.note_pty_bytes()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.note_subprocess_active()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.print_log()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.set_definitions()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.set_prior_run()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.stop()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.tick()** (2 connections) — `src/ansible_aom/formats/json.py`
- **.__init__()** (1 connections) — `src/ansible_aom/formats/json.py`
- **Store preflight definitions. No output.** (1 connections) — `src/ansible_aom/formats/json.py`
- **No-op — JSON mode doesn't show the prior-run hint.** (1 connections) — `src/ansible_aom/formats/json.py`
- **Drive RunState from a JSONL event. No output.** (1 connections) — `src/ansible_aom/formats/json.py`
- *... and 22 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (25 shared connections)
- [Preflight Summary Rendering](Preflight_Summary_Rendering.md) (20 shared connections)
- [PTY Stream Parser](PTY_Stream_Parser.md) (6 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (5 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (3 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (2 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (2 shared connections)
- [test_replay_determinism.py](test_replay_determinism.py.md) (2 shared connections)
- [Invalid Key Handling](Invalid_Key_Handling.md) (2 shared connections)
- [JSONL Environment Variable](JSONL_Environment_Variable.md) (2 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (2 shared connections)

## Source Files

- `src/ansible_aom/formats/json.py`
- `src/ansible_aom/renderer/factory.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 95 (53%)
- INFERRED: 83 (47%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*