# Cancellation Timer

> 15 nodes · cohesion 0.13

## Key Concepts

- **test_psutil_safe_probe.py** (10 connections) — `tests/unit/test_psutil_safe_probe.py`
- **test_probe_failure_disables_psutil_in_diagnostics()** (2 connections) — `tests/unit/test_psutil_safe_probe.py`
- **test_probe_failure_returns_false_without_importing_psutil()** (2 connections) — `tests/unit/test_psutil_safe_probe.py`
- **test_probe_runs_once_per_process()** (2 connections) — `tests/unit/test_psutil_safe_probe.py`
- **test_probe_success_path_uses_returned_module()** (2 connections) — `tests/unit/test_psutil_safe_probe.py`
- **test_real_probe_in_current_process_does_not_crash()** (2 connections) — `tests/unit/test_psutil_safe_probe.py`
- **test_sample_short_circuits_when_subprocess_check_unavailable()** (2 connections) — `tests/unit/test_psutil_safe_probe.py`
- **Tests for the psutil-safe probe in the runner.  Background: ``_sample_subprocess** (1 connections) — `tests/unit/test_psutil_safe_probe.py`
- **If subprocess itself blows up (highly unlikely but defensive), the     helper st** (1 connections) — `tests/unit/test_psutil_safe_probe.py`
- **If the subprocess probe exits non-zero (e.g. SIGSEGV at import),     ``_sample_s** (1 connections) — `tests/unit/test_psutil_safe_probe.py`
- **The disable reason is surfaced via the diagnostics module so it     lands in dia** (1 connections) — `tests/unit/test_psutil_safe_probe.py`
- **The probe is expensive (subprocess spawn). It must be cached so     repeated hea** (1 connections) — `tests/unit/test_psutil_safe_probe.py`
- **A successful probe yields a usable psutil module; subsequent     sample calls go** (1 connections) — `tests/unit/test_psutil_safe_probe.py`
- **Sanity: the real subprocess probe runs to completion in the test     environment** (1 connections) — `tests/unit/test_psutil_safe_probe.py`
- **_reset()** (1 connections) — `tests/unit/test_psutil_safe_probe.py`

## Relationships

- [test_posix_callback.py](test_posix_callback.py.md) (1 shared connections)
- [core/__init__.py](core-__init__.py.md) (1 shared connections)

## Source Files

- `tests/unit/test_psutil_safe_probe.py`

## Audit Trail

- EXTRACTED: 30 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*