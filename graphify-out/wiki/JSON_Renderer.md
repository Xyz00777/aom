# JSON Renderer

> 70 nodes · cohesion 0.07

## Key Concepts

- **build_run_config_key()** (37 connections) — `src/ansible_aom/core/run_config.py`
- **find_previous_run()** (30 connections) — `src/ansible_aom/session/history.py`
- **PriorRun** (19 connections) — `src/ansible_aom/session/history.py`
- **test_history.py** (15 connections) — `tests/unit/test_history.py`
- **history.py** (13 connections) — `src/ansible_aom/session/history.py`
- **Path** (13 connections)
- **test_run_config.py** (13 connections) — `tests/unit/test_run_config.py`
- **_write_session()** (12 connections) — `tests/unit/test_history.py`
- **Path** (12 connections)
- **RunConfigKey** (8 connections) — `src/ansible_aom/core/run_config.py`
- **_iter_completed_sessions()** (7 connections) — `src/ansible_aom/session/history.py`
- **_mine_and_replace()** (7 connections) — `src/ansible_aom/session/history.py`
- **Path** (7 connections)
- **_build_prior()** (6 connections) — `src/ansible_aom/session/history.py`
- **_match_loose()** (6 connections) — `src/ansible_aom/session/history.py`
- **_match_strict()** (6 connections) — `src/ansible_aom/session/history.py`
- **test_corrupt_meta_is_skipped()** (6 connections) — `tests/unit/test_history.py`
- **test_fallback_loose_match_when_config_differs()** (6 connections) — `tests/unit/test_history.py`
- **test_loose_match_filters_mismatched_host_count()** (6 connections) — `tests/unit/test_history.py`
- **test_loose_match_works_with_any_flag_variation()** (6 connections) — `tests/unit/test_history.py`
- **test_returns_most_recent_matching_completed_run()** (6 connections) — `tests/unit/test_history.py`
- **test_skips_non_completed_status()** (6 connections) — `tests/unit/test_history.py`
- **test_skips_sessions_missing_counts()** (6 connections) — `tests/unit/test_history.py`
- **test_strict_match_takes_precedence_over_loose()** (6 connections) — `tests/unit/test_history.py`
- **_mine_task_wall()** (5 connections) — `src/ansible_aom/session/history.py`
- *... and 45 more nodes in this community*

## Relationships

- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (11 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (3 shared connections)
- [Community 513](Community_513.md) (3 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (2 shared connections)
- [Community 481](Community_481.md) (2 shared connections)
- [Terminal Size Check](Terminal_Size_Check.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (2 shared connections)
- [Shift Modifier Keybindings](Shift_Modifier_Keybindings.md) (2 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (1 shared connections)
- [Inspect Debug Diagnostics](Inspect_Debug_Diagnostics.md) (1 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/run_config.py`
- `src/ansible_aom/session/history.py`
- `tests/unit/test_history.py`
- `tests/unit/test_run_config.py`

## Audit Trail

- EXTRACTED: 260 (71%)
- INFERRED: 107 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*