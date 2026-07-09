# Loop Item Stream Tests

> 38 nodes · cohesion 0.06

## Key Concepts

- **diagnostics.py** (30 connections) — `src/ansible_aom/core/diagnostics.py`
- **install_from_env()** (5 connections) — `src/ansible_aom/core/diagnostics.py`
- **dump_profile()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_profiler()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **_is_truthy()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **_parse_watchdog()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **Profile** (2 connections)
- **_psutil_disabled_reason()** (2 connections) — `src/ansible_aom/ansible/runner.py`
- **get_lifecycle_marks()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **psutil_disabled_reason()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **record_tracemalloc_peak()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **_reset_for_testing()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_debug()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_last_renderer_stats()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_psutil_disabled()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_session_recording_disabled()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_last_renderer_stats()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_tracemalloc_peak_kb()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **is_debug()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **is_profile()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **is_tracemalloc()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Path** (1 connections)
- **Opt-in diagnostics / observability layer for AOM.  Pure module — reads ``os.envi** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Test-only: undo all module state so each test gets a fresh install.      Cancels** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Enable/disable debug mode programmatically.      Called by cli.py when the --ver** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- *... and 13 more nodes in this community*

## Relationships

- [Renderer Protocol Tests](Renderer_Protocol_Tests.md) (4 shared connections)
- [Community 476](Community_476.md) (3 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (1 shared connections)
- [Frame Parameter Handling](Frame_Parameter_Handling.md) (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/runner.py`
- `src/ansible_aom/core/diagnostics.py`

## Audit Trail

- EXTRACTED: 87 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*