# TestDegradedModeFallthrough

> 7 nodes · cohesion 0.29

## Key Concepts

- **TestDegradedModeFallthrough** (7 connections) — `tests/compact/test_small_terminal.py`
- **.test_stop_in_degraded_mode_is_a_noop()** (3 connections) — `tests/compact/test_small_terminal.py`
- **.test_clear_in_degraded_mode_is_a_noop()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_print_log_in_degraded_mode_emits_plain_text()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_update_in_degraded_mode_emits_no_dec_frame()** (2 connections) — `tests/compact/test_small_terminal.py`
- **In degraded mode update() drops the status content (we don't     flood stdout wi** (1 connections) — `tests/compact/test_small_terminal.py`
- **No panel was ever shown, so stop() must not emit clear/show         sequences th** (1 connections) — `tests/compact/test_small_terminal.py`

## Relationships

- [Display](Display.md) (5 shared connections)
- [IO](IO.md) (1 shared connections)

## Source Files

- `tests/compact/test_small_terminal.py`

## Audit Trail

- EXTRACTED: 17 (94%)
- INFERRED: 1 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*