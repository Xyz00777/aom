# Status Bar Widget

> 45 nodes · cohesion 0.08

## Key Concepts

- **inspect/cli.py** (27 connections) — `src/ansible_aom/inspect/cli.py`
- **load_session_meta()** (14 connections) — `src/ansible_aom/session/store.py`
- **inspect_text()** (12 connections) — `src/ansible_aom/inspect/cli.py`
- **test_inspect_index_wiring.py** (12 connections) — `tests/unit/test_inspect_index_wiring.py`
- **find_latest_session()** (11 connections) — `src/ansible_aom/session/store.py`
- **main()** (10 connections) — `src/ansible_aom/inspect/cli.py`
- **inspect_debug()** (8 connections) — `src/ansible_aom/inspect/cli.py`
- **Path** (7 connections)
- **test_session_helpers.py** (7 connections) — `tests/unit/test_session_helpers.py`
- **inspect_tui()** (6 connections) — `src/ansible_aom/inspect/cli.py`
- **test_index_and_legacy_sessions_agree()** (6 connections) — `tests/unit/test_inspect_index_wiring.py`
- **test_inspect_text_renders_from_index_without_full_parse()** (6 connections) — `tests/unit/test_inspect_index_wiring.py`
- **inspect_prune()** (5 connections) — `src/ansible_aom/inspect/cli.py`
- **Path** (5 connections)
- **_write_session()** (5 connections) — `tests/unit/test_inspect_index_wiring.py`
- **test_state_dir_isolation.py** (5 connections) — `tests/unit/test_state_dir_isolation.py`
- **_build_parser()** (4 connections) — `src/ansible_aom/inspect/cli.py`
- **prewarm_parallel_pool()** (4 connections) — `src/ansible_aom/session/index.py`
- **test_end_session_builds_fresh_index()** (4 connections) — `tests/unit/test_inspect_index_wiring.py`
- **test_inspect_text_falls_back_without_events_file()** (4 connections) — `tests/unit/test_inspect_index_wiring.py`
- **test_load_session_meta_reads_no_events()** (4 connections) — `tests/unit/test_inspect_index_wiring.py`
- **Path** (4 connections)
- **test_find_latest_returns_newest()** (4 connections) — `tests/unit/test_session_helpers.py`
- **_default_state_dir()** (3 connections) — `src/ansible_aom/inspect/cli.py`
- **test_load_session_meta_missing_session()** (3 connections) — `tests/unit/test_inspect_index_wiring.py`
- *... and 20 more nodes in this community*

## Relationships

- [Include Role Discovery](Include_Role_Discovery.md) (12 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (7 shared connections)
- [Color ASCII Fallback](Color_ASCII_Fallback.md) (4 shared connections)
- [ASCII Status Icon Fallback](ASCII_Status_Icon_Fallback.md) (3 shared connections)
- [Loop Item Line Tests](Loop_Item_Line_Tests.md) (3 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (3 shared connections)
- [Loop Item Stream Tests](Loop_Item_Stream_Tests.md) (2 shared connections)
- [Two-Cut Tree Truncation](Two-Cut_Tree_Truncation.md) (2 shared connections)
- [Task Summary Count Tests](Task_Summary_Count_Tests.md) (2 shared connections)
- [First Ctrl-C Cancellation](First_Ctrl-C_Cancellation.md) (2 shared connections)
- [Data Model Unit Tests](Data_Model_Unit_Tests.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (2 shared connections)

## Source Files

- `src/ansible_aom/inspect/cli.py`
- `src/ansible_aom/session/index.py`
- `src/ansible_aom/session/store.py`
- `tests/unit/test_inspect_index_wiring.py`
- `tests/unit/test_session_helpers.py`
- `tests/unit/test_state_dir_isolation.py`

## Audit Trail

- EXTRACTED: 190 (91%)
- INFERRED: 18 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*