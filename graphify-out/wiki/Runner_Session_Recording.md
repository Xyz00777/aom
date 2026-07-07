# Runner Session Recording

> 30 nodes · cohesion 0.07

## Key Concepts

- **runner.py** (24 connections) — `src/ansible_aom/ansible/runner.py`
- **_SessionSink** (22 connections) — `src/ansible_aom/ansible/runner.py`
- **_feed()** (18 connections) — `src/ansible_aom/ansible/runner.py`
- **_NullSink** (18 connections) — `src/ansible_aom/ansible/runner.py`
- **_drive()** (15 connections) — `src/ansible_aom/ansible/runner.py`
- **_flush_pending()** (11 connections) — `src/ansible_aom/ansible/runner.py`
- **.record_stderr()** (6 connections) — `src/ansible_aom/ansible/runner.py`
- **_bundled_callback_dir()** (5 connections) — `src/ansible_aom/ansible/runner.py`
- **_callback_env()** (5 connections) — `src/ansible_aom/ansible/runner.py`
- **_default_session_dir()** (5 connections) — `src/ansible_aom/ansible/runner.py`
- **._disable()** (4 connections) — `src/ansible_aom/ansible/runner.py`
- **.__init__()** (4 connections) — `src/ansible_aom/ansible/runner.py`
- **.record_event()** (4 connections) — `src/ansible_aom/ansible/runner.py`
- **test_sink_end_without_counts_still_works()** (4 connections) — `tests/unit/test_runner_session_meta.py`
- **_build_command()** (3 connections) — `src/ansible_aom/ansible/runner.py`
- **_reset_psutil_probe_for_testing()** (3 connections) — `src/ansible_aom/ansible/runner.py`
- **_trace()** (3 connections) — `src/ansible_aom/ansible/runner.py`
- **test_runner_session_meta.py** (3 connections) — `tests/unit/test_runner_session_meta.py`
- **test_sink_end_persists_counts()** (3 connections) — `tests/unit/test_runner_session_meta.py`
- **.record_event()** (2 connections) — `src/ansible_aom/ansible/runner.py`
- **.end()** (2 connections) — `src/ansible_aom/ansible/runner.py`
- **_trace_enabled()** (2 connections) — `src/ansible_aom/ansible/runner.py`
- **.end()** (1 connections) — `src/ansible_aom/ansible/runner.py`
- **.record_stderr()** (1 connections) — `src/ansible_aom/ansible/runner.py`
- **.session_id()** (1 connections) — `src/ansible_aom/ansible/runner.py`
- *... and 5 more nodes in this community*

## Relationships

- [[PTY Buffer Stall Handling]] (12 shared connections)
- [[Playbook Run Integration Tests]] (9 shared connections)
- [[Run Config Key Normalization]] (5 shared connections)
- [[PTY Stream Parser]] (5 shared connections)
- [[CPU Sampling Probing]] (4 shared connections)
- [[Role Group Task Models]] (4 shared connections)
- [[Run Diagnostics Accumulator]] (3 shared connections)
- [[Renderer Event Protocol]] (3 shared connections)
- [[Runner Heartbeat Wiring]] (3 shared connections)
- [[Session Recording Tests]] (3 shared connections)
- [[Session Footer Hint]] (2 shared connections)
- [[Run Diagnostics Tests]] (2 shared connections)

## Source Files

- `src/ansible_aom/ansible/runner.py`
- `tests/unit/test_runner_session_meta.py`

## Audit Trail

- EXTRACTED: 151 (87%)
- INFERRED: 23 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*