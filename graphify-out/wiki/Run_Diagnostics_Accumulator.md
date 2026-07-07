# Run Diagnostics Accumulator

> 18 nodes · cohesion 0.12

## Key Concepts

- **RunDiagnostics** (15 connections) — `src/ansible_aom/core/diagnostics.py`
- **_FakeSink** (8 connections) — `tests/unit/test_aom_trace_events.py`
- **_feed_many()** (8 connections) — `tests/unit/test_aom_trace_events.py`
- **test_aom_trace_events.py** (7 connections) — `tests/unit/test_aom_trace_events.py`
- **set_last_run_diagnostics()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **_execution_parser()** (3 connections) — `tests/unit/test_aom_trace_events.py`
- **test_trace_events_emits_every_100th_event_under_debug()** (3 connections) — `tests/unit/test_aom_trace_events.py`
- **test_trace_events_silent_when_debug_off()** (3 connections) — `tests/unit/test_aom_trace_events.py`
- **get_last_run_diagnostics()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **.note_preflight_elapsed_ms()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **.note_pty_bytes()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **.note_stall()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **.note_timeout()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **.end()** (1 connections) — `tests/unit/test_aom_trace_events.py`
- **.record_event()** (1 connections) — `tests/unit/test_aom_trace_events.py`
- **.record_stderr()** (1 connections) — `tests/unit/test_aom_trace_events.py`
- **Phase 14/15: every-100th event stderr counter (under AOM_DEBUG).  Logs ``[aom-tr** (1 connections) — `tests/unit/test_aom_trace_events.py`
- **_reset()** (1 connections) — `tests/unit/test_aom_trace_events.py`

## Relationships

- [[Diagnostics and Profiler]] (5 shared connections)
- [[Runner Session Recording]] (3 shared connections)
- [[PTY Stream Parser]] (2 shared connections)
- [[Playbook Run Integration Tests]] (1 shared connections)
- [[Role Group Task Models]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/diagnostics.py`
- `tests/unit/test_aom_trace_events.py`

## Audit Trail

- EXTRACTED: 57 (92%)
- INFERRED: 5 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*