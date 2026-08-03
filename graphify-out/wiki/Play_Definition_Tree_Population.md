# Play Definition Tree Population

> 391 nodes · cohesion 0.01

## Key Concepts

- **HostRunState** (301 connections) — `src/ansible_aom/core/models.py`
- **PlayRunState** (268 connections) — `src/ansible_aom/core/models.py`
- **TaskRunState** (260 connections) — `src/ansible_aom/core/models.py`
- **test_cli.py** (35 connections) — `tests/unit/test_cli.py`
- **test_panels.py** (29 connections) — `tests/tui/test_panels.py`
- **test_compact_renderer.py** (22 connections) — `tests/integration/test_compact_renderer.py`
- **TestHostRunState** (22 connections) — `tests/unit/test_models.py`
- **TestPlayRunState** (22 connections) — `tests/unit/test_models.py`
- **TestTaskRunState** (20 connections) — `tests/unit/test_models.py`
- **determine_exit_code()** (19 connections) — `src/ansible_aom/core/exit_code.py`
- **TestRendererProtocol** (18 connections) — `tests/unit/test_cli.py`
- **TestRendererFactory** (17 connections) — `tests/unit/test_cli.py`
- **TestMemoryBounds** (17 connections) — `tests/unit/test_models.py`
- **TestDisplayClass** (16 connections) — `tests/integration/test_compact_renderer.py`
- **TestNonTTYBehavior** (16 connections) — `tests/integration/test_compact_renderer.py`
- **TestRefreshStrategy** (16 connections) — `tests/integration/test_compact_renderer.py`
- **TestTerminalSizeCheck** (16 connections) — `tests/integration/test_compact_renderer.py`
- **TestPackageIdentity** (16 connections) — `tests/unit/test_cli.py`
- **test_tree_upcoming_plays.py** (15 connections) — `tests/compact/test_tree_upcoming_plays.py`
- **TestCompactRendererHandleCompletion** (15 connections) — `tests/integration/test_compact_renderer.py`
- **TestCompactRendererProtocol** (15 connections) — `tests/integration/test_compact_renderer.py`
- **TestExitCodes** (15 connections) — `tests/integration/test_compact_renderer.py`
- **TestElapsedTimeFormat** (15 connections) — `tests/unit/test_event_processing.py`
- **TestHandleEventMalformedPayloads** (15 connections) — `tests/unit/test_event_processing.py`
- **._handle_v2_playbook_on_task_start()** (14 connections) — `src/ansible_aom/core/run_state.py`
- *... and 366 more nodes in this community*

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (236 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (113 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (63 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (62 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (59 shared connections)
- [PTY Stream Parser](PTY_Stream_Parser.md) (43 shared connections)
- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (33 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (26 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (25 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (22 shared connections)
- [Hide State Gating Tests](Hide_State_Gating_Tests.md) (22 shared connections)
- [Check Mode Chip](Check_Mode_Chip.md) (20 shared connections)

## Source Files

- `src/ansible_aom/core/exit_code.py`
- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/run_state.py`
- `tests/compact/test_completion_recap.py`
- `tests/compact/test_task_progress.py`
- `tests/compact/test_tree_render.py`
- `tests/compact/test_tree_upcoming_plays.py`
- `tests/compact/test_tree_upcoming_tasks.py`
- `tests/integration/test_compact_renderer.py`
- `tests/tui/test_live_refresh.py`
- `tests/tui/test_panels.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_event_processing.py`
- `tests/unit/test_models.py`
- `tests/unit/test_status_tally.py`

## Audit Trail

- EXTRACTED: 1065 (43%)
- INFERRED: 1415 (57%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*