# Diagnostics and Profiler

> 21 nodes · cohesion 0.17

## Key Concepts

- **test_inspect_accumulator.py** (16 connections) — `tests/unit/test_inspect_accumulator.py`
- **SessionIndexAccumulator** (15 connections) — `src/ansible_aom/core/inspect_model.py`
- **_events()** (6 connections) — `tests/unit/test_inspect_accumulator.py`
- **_feed_with_refs()** (5 connections) — `tests/unit/test_inspect_accumulator.py`
- **test_streaming_refs_replace_raw_events()** (5 connections) — `tests/unit/test_inspect_accumulator.py`
- **test_summary_from_index_matches_build_run_summary()** (5 connections) — `tests/unit/test_inspect_accumulator.py`
- **test_tree_from_index_matches_build_task_tree()** (5 connections) — `tests/unit/test_inspect_accumulator.py`
- **_session()** (4 connections) — `tests/unit/test_inspect_accumulator.py`
- **test_accumulator_can_skip_stderr_collection()** (4 connections) — `tests/unit/test_inspect_accumulator.py`
- **test_multiple_orphan_tasks_share_one_orphan_play()** (4 connections) — `tests/unit/test_inspect_accumulator.py`
- **test_accumulator_aggregates_counts_and_failed_tasks()** (3 connections) — `tests/unit/test_inspect_accumulator.py`
- **test_accumulator_collects_verbose_rows()** (3 connections) — `tests/unit/test_inspect_accumulator.py`
- **test_empty_hosts_runner_event_does_not_extend_duration()** (3 connections) — `tests/unit/test_inspect_accumulator.py`
- **_iter_task_nodes()** (2 connections) — `tests/unit/test_inspect_accumulator.py`
- **Single-pass, constant-per-event aggregation over a session's events.      ``feed** (1 connections) — `src/ansible_aom/core/inspect_model.py`
- **.__init__()** (1 connections) — `src/ansible_aom/core/inspect_model.py`
- **Unit tests for the streaming SessionIndex accumulator (core).  The accumulator i** (1 connections) — `tests/unit/test_inspect_accumulator.py`
- **The sqlite builder streams stderr rows straight to disk; the     accumulator mus** (1 connections) — `tests/unit/test_inspect_accumulator.py`
- **Tasks with no play attribution must all land under a single     '(orphan tasks)'** (1 connections) — `tests/unit/test_inspect_accumulator.py`
- **A runner event with hosts:{} carries no per-host result; legacy     duration onl** (1 connections) — `tests/unit/test_inspect_accumulator.py`
- **Feed events with synthetic byte refs, as the store's streamer would.** (1 connections) — `tests/unit/test_inspect_accumulator.py`

## Relationships

- [inspect_model.py](inspect_model.py.md) (9 shared connections)
- [StatusCounts](StatusCounts.md) (4 shared connections)
- [index.py](index.py.md) (3 shared connections)
- [json.py](json.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/inspect_model.py`
- `tests/unit/test_inspect_accumulator.py`

## Audit Trail

- EXTRACTED: 87 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*