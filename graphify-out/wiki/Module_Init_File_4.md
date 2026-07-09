# Module Init File

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestDegradedModeEntry** (9 connections) — `tests/compact/test_small_terminal.py`
- **.test_force_size_at_threshold_does_not_degrade()** (2 connections) — `tests/compact/test_small_terminal.py`
- **.test_non_tty_is_never_degraded()** (2 connections) — `tests/compact/test_small_terminal.py`
- **Pipe/CI mode has its own no-op behaviour and shouldn't gain         the warning** (1 connections) — `tests/compact/test_small_terminal.py`
- **A terminal smaller than MINIMUM_SIZE puts Display into degraded     mode at star** (1 connections) — `tests/compact/test_small_terminal.py`
- **Exactly (80, 24) is the supported minimum, not below.** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_force_size_below_threshold_enters_degraded_mode()** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_force_size_below_threshold_prints_one_line_warning()** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_force_size_just_below_cols_threshold_degrades()** (1 connections) — `tests/compact/test_small_terminal.py`
- **.test_force_size_just_below_rows_threshold_degrades()** (1 connections) — `tests/compact/test_small_terminal.py`

## Relationships

- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)
- [Frame Parameter Handling](Frame_Parameter_Handling.md) (1 shared connections)

## Source Files

- `tests/compact/test_small_terminal.py`

## Audit Trail

- EXTRACTED: 19 (95%)
- INFERRED: 1 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*