# Interactive Prompt Tests

> 50 nodes · cohesion 0.04

## Key Concepts

- **Renderer** (41 connections) — `src/ansible_aom/renderer/protocol.py`
- **TestProtocol** (7 connections) — `tests/unit/test_interactive_prompt.py`
- **.test_compact_renderer_satisfies_protocol()** (4 connections) — `tests/unit/test_cli.py`
- **test_interactive_prompt.py** (4 connections) — `tests/unit/test_interactive_prompt.py`
- **.test_renderer_protocol_has_handle_completion_method()** (3 connections) — `tests/unit/test_cli.py`
- **.test_renderer_protocol_has_handle_password_prompt_method()** (3 connections) — `tests/unit/test_cli.py`
- **.test_renderer_protocol_has_start_method()** (3 connections) — `tests/unit/test_cli.py`
- **.test_renderer_protocol_has_stop_method()** (3 connections) — `tests/unit/test_cli.py`
- **.test_renderer_protocol_has_update_state_method()** (3 connections) — `tests/unit/test_cli.py`
- **.test_aom_app_still_satisfies_protocol()** (3 connections) — `tests/unit/test_interactive_prompt.py`
- **.test_compact_renderer_still_satisfies_protocol()** (3 connections) — `tests/unit/test_interactive_prompt.py`
- **protocol.py** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.add_warning()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.handle_completion()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.handle_interactive_prompt()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.handle_password_prompt()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.note_pty_bytes()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.note_subprocess_active()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.print_log()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.set_definitions()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.set_prior_run()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.start()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.stop()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.tick()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- **.update_state()** (2 connections) — `src/ansible_aom/renderer/protocol.py`
- *... and 25 more nodes in this community*

## Relationships

- [Session Recording Tests](Session_Recording_Tests.md) (10 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (5 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (4 shared connections)
- [CLI Main Entry Point](CLI_Main_Entry_Point.md) (1 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)
- [Debug Diagnostics Summary](Debug_Diagnostics_Summary.md) (1 shared connections)
- [Rerun Main Function](Rerun_Main_Function.md) (1 shared connections)
- [Hide State Normalization](Hide_State_Normalization.md) (1 shared connections)
- [Diagnostics Layer Tests](Diagnostics_Layer_Tests.md) (1 shared connections)
- [Preflight Summary Rendering](Preflight_Summary_Rendering.md) (1 shared connections)
- [JSON Renderer](JSON_Renderer.md) (1 shared connections)
- [Pause Lingering Cleanup](Pause_Lingering_Cleanup.md) (1 shared connections)

## Source Files

- `src/ansible_aom/renderer/protocol.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_interactive_prompt.py`

## Audit Trail

- EXTRACTED: 103 (79%)
- INFERRED: 28 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*