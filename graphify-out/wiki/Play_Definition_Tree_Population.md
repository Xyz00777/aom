# Play Definition Tree Population

> 293 nodes · cohesion 0.01

## Key Concepts

- **HostRunState** (309 connections) — `src/ansible_aom/core/models.py`
- **PlayRunState** (279 connections) — `src/ansible_aom/core/models.py`
- **TaskRunState** (266 connections) — `src/ansible_aom/core/models.py`
- **test_cli.py** (35 connections) — `tests/unit/test_cli.py`
- **TestHideStateFlag** (29 connections) — `tests/unit/test_cli.py`
- **TestHostRunState** (22 connections) — `tests/unit/test_models.py`
- **TestPlayRunState** (22 connections) — `tests/unit/test_models.py`
- **TestTaskRunState** (20 connections) — `tests/unit/test_models.py`
- **TestRendererFactory** (18 connections) — `tests/unit/test_cli.py`
- **TestPackageIdentity** (17 connections) — `tests/unit/test_cli.py`
- **TestMemoryBounds** (17 connections) — `tests/unit/test_models.py`
- **determine_exit_code()** (16 connections) — `src/ansible_aom/core/exit_code.py`
- **TestYesFlag** (16 connections) — `tests/unit/test_cli.py`
- **TestExitCodes** (15 connections) — `tests/integration/test_compact_renderer.py`
- **TestCLIEntryPoint** (15 connections) — `tests/unit/test_cli.py`
- **format_failure_recap()** (14 connections) — `src/ansible_aom/compact/format.py`
- **TestExitCode1** (14 connections) — `tests/unit/test_cli.py`
- **TestExitCode2** (14 connections) — `tests/unit/test_cli.py`
- **TestInstallCompletionFlag** (14 connections) — `tests/unit/test_cli.py`
- **TestFormatFailureRecap** (13 connections) — `tests/compact/test_completion_recap.py`
- **TestApplyStateIcons** (13 connections) — `tests/tui/test_live_refresh.py`
- **TestAnsibleOptionsPassthrough** (13 connections) — `tests/unit/test_cli.py`
- **TestBasicCLIInvocation** (13 connections) — `tests/unit/test_cli.py`
- **TestHelpFlag** (13 connections) — `tests/unit/test_cli.py`
- **TestTUIModeFlag** (13 connections) — `tests/unit/test_cli.py`
- *... and 268 more nodes in this community*

## Relationships

- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (158 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (100 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (65 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (60 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (57 shared connections)
- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (46 shared connections)
- [PTY Stream Parser](PTY_Stream_Parser.md) (44 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (35 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (30 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (27 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (24 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (24 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/core/exit_code.py`
- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/tree_projection.py`
- `tests/compact/test_completion_recap.py`
- `tests/compact/test_preserve_tree_on_cancel.py`
- `tests/compact/test_status_bar_colors.py`
- `tests/compact/test_tree_projection_lifecycle.py`
- `tests/compact/test_tree_render.py`
- `tests/compact/test_tree_upcoming_plays.py`
- `tests/compact/test_tree_upcoming_tasks.py`
- `tests/integration/test_compact_renderer.py`
- `tests/tui/test_live_refresh.py`
- `tests/tui/test_panels.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_json_renderer.py`
- `tests/unit/test_models.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_run_state_index.py`
- `tests/unit/test_stale_running_cleanup.py`

## Audit Trail

- EXTRACTED: 765 (37%)
- INFERRED: 1320 (63%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*