# Core Domain Architecture

> 13 nodes · cohesion 0.17

## Key Concepts

- **test_profile_tracemalloc.py** (12 connections) — `tests/unit/test_profile_tracemalloc.py`
- **Path** (2 connections)
- **test_dump_profile_noop_when_off()** (2 connections) — `tests/unit/test_profile_tracemalloc.py`
- **test_dump_profile_writes_pstats()** (2 connections) — `tests/unit/test_profile_tracemalloc.py`
- **Phase 7: AOM_PROFILE and AOM_TRACEMALLOC wiring.  Spec: docs/superpowers/specs/2** (1 connections) — `tests/unit/test_profile_tracemalloc.py`
- **_reset()** (1 connections) — `tests/unit/test_profile_tracemalloc.py`
- **test_aom_profile_creates_profiler_instance()** (1 connections) — `tests/unit/test_profile_tracemalloc.py`
- **test_aom_tracemalloc_starts_tracing()** (1 connections) — `tests/unit/test_profile_tracemalloc.py`
- **test_is_profile_default_false()** (1 connections) — `tests/unit/test_profile_tracemalloc.py`
- **test_is_tracemalloc_default_false()** (1 connections) — `tests/unit/test_profile_tracemalloc.py`
- **test_record_tracemalloc_peak_noop_when_off()** (1 connections) — `tests/unit/test_profile_tracemalloc.py`
- **test_record_tracemalloc_peak_reads_current_peak()** (1 connections) — `tests/unit/test_profile_tracemalloc.py`
- **test_reset_stops_tracemalloc()** (1 connections) — `tests/unit/test_profile_tracemalloc.py`

## Relationships

- [core/__init__.py](core-__init__.py.md) (1 shared connections)

## Source Files

- `tests/unit/test_profile_tracemalloc.py`

## Audit Trail

- EXTRACTED: 27 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*