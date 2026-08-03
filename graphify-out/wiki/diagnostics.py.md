# diagnostics.py

> 64 nodes · cohesion 0.04

## Key Concepts

- **diagnostics.py** (38 connections) — `src/ansible_aom/core/diagnostics.py`
- **RunDiagnostics** (15 connections) — `src/ansible_aom/core/diagnostics.py`
- **test_aom_trace_events.py** (10 connections) — `tests/unit/test_aom_trace_events.py`
- **_FakeSink** (8 connections) — `tests/unit/test_aom_trace_events.py`
- **_feed_many()** (8 connections) — `tests/unit/test_aom_trace_events.py`
- **build_diagnostics_record()** (5 connections) — `src/ansible_aom/core/diagnostics.py`
- **RendererStats** (5 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_profiler()** (4 connections) — `src/ansible_aom/core/diagnostics.py`
- **lifecycle_mark()** (4 connections) — `src/ansible_aom/core/diagnostics.py`
- **render_storm_warning()** (4 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_last_run_diagnostics()** (4 connections) — `src/ansible_aom/core/diagnostics.py`
- **dump_profile()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **_is_truthy()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **_parse_watchdog()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **record_tracemalloc_peak()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_debug()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **_execution_parser()** (3 connections) — `tests/unit/test_aom_trace_events.py`
- **test_trace_events_emits_every_100th_event_under_debug()** (3 connections) — `tests/unit/test_aom_trace_events.py`
- **test_trace_events_silent_when_debug_off()** (3 connections) — `tests/unit/test_aom_trace_events.py`
- **Profile** (2 connections)
- **_psutil_disabled_reason()** (2 connections) — `src/ansible_aom/ansible/runner.py`
- **get_last_run_diagnostics()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_lifecycle_marks()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **psutil_disabled_reason()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **_reset_for_testing()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- *... and 39 more nodes in this community*

## Relationships

- [run_playbook](run_playbook.md) (11 shared connections)
- [load_session](load_session.md) (8 shared connections)
- [IO](IO.md) (2 shared connections)
- [json.py](json.py.md) (2 shared connections)
- [StreamPhase](StreamPhase.md) (2 shared connections)
- [PtyStreamParser](PtyStreamParser.md) (2 shared connections)
- [RunState](RunState.md) (2 shared connections)
- [ansible_aom/cli.py](ansible_aom-cli.py.md) (1 shared connections)
- [renderer.py](renderer.py.md) (1 shared connections)
- [_get_psutil](_get_psutil.md) (1 shared connections)
- [_BoundedSet](_BoundedSet.md) (1 shared connections)
- [core/__init__.py](core-__init__.py.md) (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/runner.py`
- `src/ansible_aom/core/diagnostics.py`
- `tests/unit/test_aom_trace_events.py`

## Audit Trail

- EXTRACTED: 177 (96%)
- INFERRED: 7 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*