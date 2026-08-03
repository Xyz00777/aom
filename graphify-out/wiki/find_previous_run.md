# find_previous_run

> 25 nodes · cohesion 0.19

## Key Concepts

- **find_previous_run()** (36 connections) — `src/ansible_aom/session/history.py`
- **test_history.py** (17 connections) — `tests/unit/test_history.py`
- **Path** (13 connections)
- **_write_session()** (12 connections) — `tests/unit/test_history.py`
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
- **Return the most recent completed session matching ``(key, host_count)``.      Tw** (1 connections) — `src/ansible_aom/session/history.py`
- **Unit tests for session.history.find_previous_run.** (1 connections) — `tests/unit/test_history.py`
- **Different tags still match via the loose fallback (same playbook + host count).** (1 connections) — `tests/unit/test_history.py`
- **Failed / crashed runs are unreliable as estimates.** (1 connections) — `tests/unit/test_history.py`
- **Pre-v1.2 sessions don't have the fields — can't estimate from them.** (1 connections) — `tests/unit/test_history.py`
- **When both an exact and a loose match exist, the exact (most recent) is chosen.** (1 connections) — `tests/unit/test_history.py`
- **Loose fallback still requires host count to match.** (1 connections) — `tests/unit/test_history.py`
- **Loose fallback ignores tags, limit, extra_vars, diff, check, step.** (1 connections) — `tests/unit/test_history.py`
- **A session dir whose meta.json fails to parse must not crash the lookup.** (1 connections) — `tests/unit/test_history.py`

## Relationships

- [build_run_config_key](build_run_config_key.md) (12 shared connections)
- [history.py](history.py.md) (10 shared connections)
- [test_history_roundtrip.py](test_history_roundtrip.py.md) (5 shared connections)
- [Run Diagnostics Accumulator](Run_Diagnostics_Accumulator.md) (5 shared connections)
- [run_playbook](run_playbook.md) (2 shared connections)
- [PriorRun](PriorRun.md) (2 shared connections)
- [test_history_loop_totals.py](test_history_loop_totals.py.md) (1 shared connections)
- [Terminal Size Check](Terminal_Size_Check.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/session/history.py`
- `tests/unit/test_history.py`

## Audit Trail

- EXTRACTED: 152 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*