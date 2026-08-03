# Run State Summary Panel

> 35 nodes · cohesion 0.08

## Key Concepts

- **AppConfig** (65 connections) — `src/ansible_aom/core/config.py`
- **TestAppConfig** (19 connections) — `tests/unit/test_config.py`
- **.test_app_config_custom_status_bar()** (4 connections) — `tests/unit/test_config.py`
- **.test_app_config_custom_warnings()** (4 connections) — `tests/unit/test_config.py`
- **.test_app_config_default_status_bar()** (4 connections) — `tests/unit/test_config.py`
- **.test_app_config_default_warnings()** (4 connections) — `tests/unit/test_config.py`
- **.test_app_config_independent_instances()** (4 connections) — `tests/unit/test_config.py`
- **.test_app_config_custom_log_max_lines()** (3 connections) — `tests/unit/test_config.py`
- **.test_app_config_custom_redaction()** (3 connections) — `tests/unit/test_config.py`
- **.test_app_config_custom_session_keep_count()** (3 connections) — `tests/unit/test_config.py`
- **.test_app_config_custom_session_keep_days()** (3 connections) — `tests/unit/test_config.py`
- **.test_app_config_default_log_max_lines()** (3 connections) — `tests/unit/test_config.py`
- **.test_app_config_default_redaction()** (3 connections) — `tests/unit/test_config.py`
- **.test_app_config_default_session_keep_count()** (3 connections) — `tests/unit/test_config.py`
- **.test_app_config_default_session_keep_days()** (3 connections) — `tests/unit/test_config.py`
- **.test_app_config_nested_config_isolation()** (3 connections) — `tests/unit/test_config.py`
- **.test_warnings_config_default_from_app_config()** (3 connections) — `tests/unit/test_warnings.py`
- **BaseSettings** (1 connections)
- **Application configuration loaded from YAML and CLI.      YAML loading is handled** (1 connections) — `src/ansible_aom/core/config.py`
- **Tests for AppConfig model - TC-263 to TC-275.** (1 connections) — `tests/unit/test_config.py`
- **TC-263: AppConfig has default log_max_lines=50000.** (1 connections) — `tests/unit/test_config.py`
- **TC-264: AppConfig has default session_keep_count=100.** (1 connections) — `tests/unit/test_config.py`
- **TC-265: AppConfig has default session_keep_days=30.** (1 connections) — `tests/unit/test_config.py`
- **AppConfig has default StatusBarConfig.** (1 connections) — `tests/unit/test_config.py`
- **AppConfig has default RedactionConfig.** (1 connections) — `tests/unit/test_config.py`
- *... and 10 more nodes in this community*

## Relationships

- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (18 shared connections)
- [Session Replay Driver](Session_Replay_Driver.md) (10 shared connections)
- [Inspect Text Golden Tests](Inspect_Text_Golden_Tests.md) (7 shared connections)
- [Status Bar Elements](Status_Bar_Elements.md) (5 shared connections)
- [Loop Item Events Integration](Loop_Item_Events_Integration.md) (4 shared connections)
- [Renderer Set Definitions](Renderer_Set_Definitions.md) (3 shared connections)
- [Inspect Debug Diagnostics](Inspect_Debug_Diagnostics.md) (2 shared connections)
- [Renderer Implementations](Renderer_Implementations.md) (2 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (2 shared connections)
- [Compact Password Passthrough](Compact_Password_Passthrough.md) (1 shared connections)
- [Mitogen Event Tolerance](Mitogen_Event_Tolerance.md) (1 shared connections)
- [Replay CLI Subcommand](Replay_CLI_Subcommand.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/config.py`
- `tests/unit/test_config.py`
- `tests/unit/test_warnings.py`

## Audit Trail

- EXTRACTED: 67 (44%)
- INFERRED: 85 (56%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*