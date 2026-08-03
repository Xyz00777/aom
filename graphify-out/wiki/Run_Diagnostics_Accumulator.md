# Run Diagnostics Accumulator

> 13 nodes · cohesion 0.37

## Key Concepts

- **test_history_observed_count.py** (12 connections) — `tests/unit/test_history_observed_count.py`
- **test_loose_match_is_flagged_inexact()** (8 connections) — `tests/unit/test_history_observed_count.py`
- **test_observed_count_includes_starts_with_bad_timestamps()** (8 connections) — `tests/unit/test_history_observed_count.py`
- **test_observed_task_count_counts_task_starts()** (7 connections) — `tests/unit/test_history_observed_count.py`
- **test_strict_match_is_flagged_exact()** (7 connections) — `tests/unit/test_history_observed_count.py`
- **Path** (6 connections)
- **_write_session()** (6 connections) — `tests/unit/test_history_observed_count.py`
- **_stats()** (5 connections) — `tests/unit/test_history_observed_count.py`
- **_task_start()** (5 connections) — `tests/unit/test_history_observed_count.py`
- **test_missing_events_yields_zero_observed()** (4 connections) — `tests/unit/test_history_observed_count.py`
- **Prior-run observed task count + match-confidence flag.  ``preflight_task_count``** (1 connections) — `tests/unit/test_history_observed_count.py`
- **Same playbook + host count but different args -> loose fallback.** (1 connections) — `tests/unit/test_history_observed_count.py`
- **A raw count of task-start events — not gated on a parseable delta.** (1 connections) — `tests/unit/test_history_observed_count.py`

## Relationships

- [JSON Renderer](JSON_Renderer.md) (11 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Property Based Tests](Property_Based_Tests.md) (1 shared connections)

## Source Files

- `tests/unit/test_history_observed_count.py`

## Audit Trail

- EXTRACTED: 71 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*