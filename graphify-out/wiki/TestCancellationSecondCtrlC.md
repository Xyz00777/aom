# TestCancellationSecondCtrlC

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestCancellationSecondCtrlC** (5 connections) — `tests/integration/test_error_handling.py`
- **.test_second_sigint_after_2s_is_normal()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_second_sigint_within_2s_is_immediate_exit()** (2 connections) — `tests/integration/test_error_handling.py`
- **TC-450: Cancellation - Second Ctrl+C Kill Everything.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-450: Second Ctrl+C within 2 seconds triggers immediate exit.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-450: Second Ctrl+C after 2 seconds is normal interrupt.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [PtyStreamParser](PtyStreamParser.md) (1 shared connections)
- [Completion Host Table](Completion_Host_Table.md) (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 11 (92%)
- INFERRED: 1 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*