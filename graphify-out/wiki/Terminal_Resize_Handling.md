# Terminal Resize Handling

> 7 nodes · cohesion 0.29

## Key Concepts

- **TestReEnableOnResize** (7 connections) — `tests/compact/test_small_terminal.py`
- **.test_update_without_force_size_falls_back_to_real_terminal()** (3 connections) — `tests/compact/test_small_terminal.py`
- **.test_re_enable_does_not_reprint_warning()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_update_drops_into_degraded_mode_when_terminal_shrinks()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_update_re_enables_panel_when_terminal_grows()** (2 connections) — `tests/compact/test_small_terminal.py`
- **The 'SIGWINCH' equivalent: a previously-degraded display     re-enables its live** (1 connections) — `tests/compact/test_small_terminal.py`
- **force_size is the test seam; production calls don't pass it.         Verify the** (1 connections) — `tests/compact/test_small_terminal.py`

## Relationships

- [[Terminal Display Manager]] (5 shared connections)
- [[Small Terminal Handling]] (1 shared connections)

## Source Files

- `tests/compact/test_small_terminal.py`

## Audit Trail

- EXTRACTED: 13 (72%)
- INFERRED: 5 (28%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*