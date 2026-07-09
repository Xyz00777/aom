# Render Storm Diagnostic

> 14 nodes · cohesion 0.14

## Key Concepts

- **test_diagnostics.py** (14 connections) — `tests/unit/test_diagnostics.py`
- **Unit tests for core.diagnostics — opt-in observability layer.  Spec: docs/superp** (1 connections) — `tests/unit/test_diagnostics.py`
- **_reset_diagnostics()** (1 connections) — `tests/unit/test_diagnostics.py`
- **test_aom_debug_is_the_only_trace_knob()** (1 connections) — `tests/unit/test_diagnostics.py`
- **test_build_diagnostics_record_json_roundtrip()** (1 connections) — `tests/unit/test_diagnostics.py`
- **test_debug_falsy_values_disable()** (1 connections) — `tests/unit/test_diagnostics.py`
- **test_debug_sets_logger_level()** (1 connections) — `tests/unit/test_diagnostics.py`
- **test_install_enables_faulthandler()** (1 connections) — `tests/unit/test_diagnostics.py`
- **test_install_from_env_with_empty_env_is_noop()** (1 connections) — `tests/unit/test_diagnostics.py`
- **test_install_is_idempotent()** (1 connections) — `tests/unit/test_diagnostics.py`
- **test_lifecycle_mark_always_records()** (1 connections) — `tests/unit/test_diagnostics.py`
- **test_watchdog_calls_dump_traceback_later()** (1 connections) — `tests/unit/test_diagnostics.py`
- **test_watchdog_with_invalid_value_is_none()** (1 connections) — `tests/unit/test_diagnostics.py`
- **test_watchdog_zero_is_treated_as_disabled()** (1 connections) — `tests/unit/test_diagnostics.py`

## Relationships

- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/unit/test_diagnostics.py`

## Audit Trail

- EXTRACTED: 27 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*