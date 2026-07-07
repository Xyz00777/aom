# Stderr Capture Handling

> 4 nodes · cohesion 0.25

## Key Concepts

- **TestStderrCapture** (6 connections) — `tests/integration/test_error_handling.py`
- **.test_stderr_captured_and_stored()** (4 connections) — `tests/integration/test_error_handling.py`
- **.test_stderr_displayed_in_view()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_stderr_json_parsing_attempt()** (2 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[PTY Stream Parser]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)
- [[Run Config Key Normalization]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 13 (93%)
- INFERRED: 1 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*