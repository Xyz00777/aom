# JSON Renderer

> 49 nodes · cohesion 0.10

## Key Concepts

- **build_run_config_key()** (44 connections) — `src/ansible_aom/core/run_config.py`
- **find_previous_run()** (36 connections) — `src/ansible_aom/session/history.py`
- **test_history.py** (17 connections) — `tests/unit/test_history.py`
- **test_run_config.py** (14 connections) — `tests/unit/test_run_config.py`
- **Path** (13 connections)
- **run_config.py** (12 connections) — `src/ansible_aom/core/run_config.py`
- **_write_session()** (12 connections) — `tests/unit/test_history.py`
- **Path** (12 connections)
- **RunConfigKey** (9 connections) — `src/ansible_aom/core/run_config.py`
- **test_corrupt_meta_is_skipped()** (6 connections) — `tests/unit/test_history.py`
- **test_fallback_loose_match_when_config_differs()** (6 connections) — `tests/unit/test_history.py`
- **test_loose_match_filters_mismatched_host_count()** (6 connections) — `tests/unit/test_history.py`
- **test_loose_match_works_with_any_flag_variation()** (6 connections) — `tests/unit/test_history.py`
- **test_returns_most_recent_matching_completed_run()** (6 connections) — `tests/unit/test_history.py`
- **test_skips_non_completed_status()** (6 connections) — `tests/unit/test_history.py`
- **test_skips_sessions_missing_counts()** (6 connections) — `tests/unit/test_history.py`
- **test_strict_match_takes_precedence_over_loose()** (6 connections) — `tests/unit/test_history.py`
- **test_filters_out_mismatched_host_count()** (5 connections) — `tests/unit/test_history.py`
- **test_prior_run_end_time_parsed_to_datetime()** (5 connections) — `tests/unit/test_history.py`
- **test_returns_none_when_no_sessions()** (4 connections) — `tests/unit/test_history.py`
- **test_returns_none_when_session_dir_missing()** (4 connections) — `tests/unit/test_history.py`
- **test_key_is_hashable_and_frozen()** (4 connections) — `tests/unit/test_run_config.py`
- **test_key_unknown_flag_is_ignored_safely()** (4 connections) — `tests/unit/test_run_config.py`
- **_split_csv_sorted()** (3 connections) — `src/ansible_aom/core/run_config.py`
- **test_key_check_and_diff_are_distinct()** (3 connections) — `tests/unit/test_run_config.py`
- *... and 24 more nodes in this community*

## Relationships

- [Property Based Tests](Property_Based_Tests.md) (14 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (11 shared connections)
- [Run Diagnostics Accumulator](Run_Diagnostics_Accumulator.md) (11 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (3 shared connections)
- [test_history_loop_totals.py](test_history_loop_totals.py.md) (3 shared connections)
- [Terminal Size Check](Terminal_Size_Check.md) (3 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (3 shared connections)
- [Replay Determinism Tests](Replay_Determinism_Tests.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/run_config.py`
- `src/ansible_aom/session/history.py`
- `tests/unit/test_history.py`
- `tests/unit/test_run_config.py`

## Audit Trail

- EXTRACTED: 198 (68%)
- INFERRED: 93 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*