# Small Terminal Handling

> 10 nodes · cohesion 0.20

## Key Concepts

- **test_small_terminal.py** (6 connections) — `tests/compact/test_small_terminal.py`
- **TestForceSizePassthrough** (5 connections) — `tests/compact/test_small_terminal.py`
- **TestThresholdConstant** (4 connections) — `tests/compact/test_small_terminal.py`
- **.test_start_without_force_size_works_as_before()** (3 connections) — `tests/compact/test_small_terminal.py`
- **.test_start_accepts_force_size_kwarg_without_error()** (2 connections) — `tests/compact/test_small_terminal.py`
- **Tests for R4 — graceful degradation on terminals smaller than 80×24.  Today the** (1 connections) — `tests/compact/test_small_terminal.py`
- **The (cols, rows) threshold lives as a module constant so tests     can reference** (1 connections) — `tests/compact/test_small_terminal.py`
- **`force_size` is the test injection seam for the size detection     that Task 2 w** (1 connections) — `tests/compact/test_small_terminal.py`
- **Backwards-compatible: existing callers don't pass force_size.** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_minimum_size_is_80_cols_24_rows()** (1 connections) — `tests/compact/test_small_terminal.py`

## Relationships

- [[Terminal Display Manager]] (6 shared connections)
- [[Terminal Resize Handling]] (1 shared connections)

## Source Files

- `tests/compact/test_small_terminal.py`

## Audit Trail

- EXTRACTED: 21 (84%)
- INFERRED: 4 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*