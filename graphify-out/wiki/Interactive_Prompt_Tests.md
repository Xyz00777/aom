# Interactive Prompt Tests

> 52 nodes · cohesion 0.04

## Key Concepts

- **Renderer** (46 connections) — `src/ansible_aom/renderer/protocol.py`
- **renderer/protocol.py** (11 connections) — `src/ansible_aom/renderer/protocol.py`
- **TestProtocol** (6 connections) — `tests/unit/test_interactive_prompt.py`
- **live.py** (5 connections) — `src/ansible_aom/drivers/live.py`
- **.test_compact_renderer_satisfies_protocol()** (4 connections) — `tests/unit/test_cli.py`
- **.add_warning()** (3 connections) — `src/ansible_aom/renderer/protocol.py`
- **.test_renderer_protocol_has_handle_completion_method()** (3 connections) — `tests/unit/test_cli.py`
- **.test_renderer_protocol_has_handle_password_prompt_method()** (3 connections) — `tests/unit/test_cli.py`
- **.test_renderer_protocol_has_start_method()** (3 connections) — `tests/unit/test_cli.py`
- **.test_renderer_protocol_has_stop_method()** (3 connections) — `tests/unit/test_cli.py`
- **.test_renderer_protocol_has_update_state_method()** (3 connections) — `tests/unit/test_cli.py`
- **.test_textual_app_satisfies_protocol()** (3 connections) — `tests/unit/test_cli.py`
- **.test_compact_renderer_still_satisfies_protocol()** (3 connections) — `tests/unit/test_interactive_prompt.py`
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
- *... and 27 more nodes in this community*

## Relationships

- [Tree Block Animation](Tree_Block_Animation.md) (7 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (7 shared connections)
- [Diagnostics Layer Tests](Diagnostics_Layer_Tests.md) (4 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (3 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (3 shared connections)
- [Replay Determinism Tests](Replay_Determinism_Tests.md) (2 shared connections)
- [Debug Diagnostics Summary](Debug_Diagnostics_Summary.md) (2 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (2 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (2 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (2 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)
- [Property Based Tests](Property_Based_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/drivers/live.py`
- `src/ansible_aom/renderer/protocol.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_interactive_prompt.py`

## Audit Trail

- EXTRACTED: 121 (81%)
- INFERRED: 28 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*