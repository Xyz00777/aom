# Diagnostics and Profiler

> 28 nodes · cohesion 0.06

## Key Concepts

- **diagnostics.py** (30 connections) — `src/ansible_aom/core/diagnostics.py`
- **install_from_env()** (7 connections) — `src/ansible_aom/core/diagnostics.py`
- **lifecycle_mark()** (5 connections) — `src/ansible_aom/core/diagnostics.py`
- **dump_profile()** (4 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_profiler()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **_is_truthy()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **_parse_watchdog()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_lifecycle_marks()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **record_tracemalloc_peak()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **_reset_for_testing()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **.note_event()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_last_renderer_stats()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_psutil_disabled()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_session_recording_disabled()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_last_renderer_stats()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_tracemalloc_peak_kb()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **is_debug()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **is_profile()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **is_tracemalloc()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **psutil_disabled_reason()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Opt-in diagnostics / observability layer for AOM.  Pure module — reads ``os.envi** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Test-only: undo all module state so each test gets a fresh install.      Cancels** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Return True iff ``value`` is set and not a known falsy literal.** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Parse ``AOM_WATCHDOG`` into a positive int, else None.** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Install diagnostics based on ``env`` (defaults to ``os.environ``).      Idempote** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- *... and 3 more nodes in this community*

## Relationships

- [[Run Diagnostics Accumulator]] (4 shared connections)
- [[Diagnostics Record Building]] (3 shared connections)
- [[Design Specs Plans]] (2 shared connections)
- [[Debug Diagnostics Summary]] (1 shared connections)
- [[Run Config Key Normalization]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/diagnostics.py`

## Audit Trail

- EXTRACTED: 83 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*