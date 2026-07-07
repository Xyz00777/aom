# Run Config Key Normalization

> 78 nodes · cohesion 0.06

## Key Concepts

- **Path** (416 connections)
- **build_run_config_key()** (37 connections) — `src/ansible_aom/core/run_config.py`
- **find_previous_run()** (31 connections) — `src/ansible_aom/session/history.py`
- **test_history.py** (14 connections) — `tests/unit/test_history.py`
- **test_run_config.py** (13 connections) — `tests/unit/test_run_config.py`
- **test_inspect_cli.py** (12 connections) — `tests/integration/test_inspect_cli.py`
- **_write_session()** (12 connections) — `tests/unit/test_history.py`
- **test_history_roundtrip.py** (8 connections) — `tests/integration/test_history_roundtrip.py`
- **test_runner_pushes_prior_run_into_renderer()** (7 connections) — `tests/integration/test_history_roundtrip.py`
- **test_history_loop_totals.py** (7 connections) — `tests/unit/test_history_loop_totals.py`
- **_prior()** (7 connections) — `tests/unit/test_history_loop_totals.py`
- **test_different_tags_match_via_fallback()** (6 connections) — `tests/integration/test_history_roundtrip.py`
- **test_failed_session_is_not_returned()** (6 connections) — `tests/integration/test_history_roundtrip.py`
- **test_corrupt_meta_is_skipped()** (6 connections) — `tests/unit/test_history.py`
- **test_fallback_loose_match_when_config_differs()** (6 connections) — `tests/unit/test_history.py`
- **test_loose_match_filters_mismatched_host_count()** (6 connections) — `tests/unit/test_history.py`
- **test_loose_match_works_with_any_flag_variation()** (6 connections) — `tests/unit/test_history.py`
- **test_skips_non_completed_status()** (6 connections) — `tests/unit/test_history.py`
- **test_skips_sessions_missing_counts()** (6 connections) — `tests/unit/test_history.py`
- **test_strict_match_takes_precedence_over_loose()** (6 connections) — `tests/unit/test_history.py`
- **test_different_host_count_does_not_match()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **test_most_recent_completed_wins()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **test_session_then_history_roundtrip()** (5 connections) — `tests/integration/test_history_roundtrip.py`
- **test_mines_loop_total_per_task_path_and_host()** (5 connections) — `tests/unit/test_history_loop_totals.py`
- **test_filters_out_mismatched_host_count()** (5 connections) — `tests/unit/test_history.py`
- *... and 53 more nodes in this community*

## Relationships

- [[Include Role Discovery]] (58 shared connections)
- [[Session Recording Tests]] (38 shared connections)
- [[Three-Pane Inspect App]] (30 shared connections)
- [[Inspect CLI Commands]] (24 shared connections)
- [[Run History Mining]] (17 shared connections)
- [[Session Replay Round Trip]] (16 shared connections)
- [[Interactive Prompt Tests]] (15 shared connections)
- [[Inventory Auto Detection]] (15 shared connections)
- [[Inspect Session List]] (14 shared connections)
- [[Playbook Run Integration Tests]] (13 shared connections)
- [[Task Wall Duration Mining]] (11 shared connections)
- [[Version Bump Script]] (10 shared connections)

## Source Files

- `src/ansible_aom/core/run_config.py`
- `src/ansible_aom/session/history.py`
- `tests/integration/test_history_roundtrip.py`
- `tests/integration/test_inspect_cli.py`
- `tests/integration/test_playbook_parser.py`
- `tests/unit/test_history.py`
- `tests/unit/test_history_loop_totals.py`
- `tests/unit/test_run_config.py`

## Audit Trail

- EXTRACTED: 664 (86%)
- INFERRED: 109 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*