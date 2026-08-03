# Preflight Definition Assembly

> 15 nodes · cohesion 0.30

## Key Concepts

- **test_summary_flush_scaling.py** (13 connections) — `tests/compact/test_summary_flush_scaling.py`
- **test_host_death_flushes_other_pending_tasks()** (8 connections) — `tests/compact/test_summary_flush_scaling.py`
- **test_revived_host_blocks_completion_again()** (8 connections) — `tests/compact/test_summary_flush_scaling.py`
- **_logged()** (6 connections) — `tests/compact/test_summary_flush_scaling.py`
- **_renderer()** (6 connections) — `tests/compact/test_summary_flush_scaling.py`
- **test_completion_checks_stay_linear_with_a_straggler_host()** (6 connections) — `tests/compact/test_summary_flush_scaling.py`
- **_summary_lines()** (5 connections) — `tests/compact/test_summary_flush_scaling.py`
- **_ok()** (4 connections) — `tests/compact/test_summary_flush_scaling.py`
- **_start()** (4 connections) — `tests/compact/test_summary_flush_scaling.py`
- **_failed()** (2 connections) — `tests/compact/test_summary_flush_scaling.py`
- **_unreachable()** (2 connections) — `tests/compact/test_summary_flush_scaling.py`
- **Per-event cost of the full-completion summary sweep must stay flat.  Regression** (1 connections) — `tests/compact/test_summary_flush_scaling.py`
- **A host dying in one task completes OTHER tasks it was blocking:     dead hosts l** (1 connections) — `tests/compact/test_summary_flush_scaling.py`
- **A host whose FAILED result is later overwritten by an OK (retry /     async-poll** (1 connections) — `tests/compact/test_summary_flush_scaling.py`
- **One slow host must not make per-event completion checks sweep the     whole pend** (1 connections) — `tests/compact/test_summary_flush_scaling.py`

## Relationships

- [CompactRenderer](CompactRenderer.md) (3 shared connections)
- [renderer.py](renderer.py.md) (1 shared connections)
- [HostRunState](HostRunState.md) (1 shared connections)
- [PlayDefinition](PlayDefinition.md) (1 shared connections)

## Source Files

- `tests/compact/test_summary_flush_scaling.py`

## Audit Trail

- EXTRACTED: 68 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*