# Stderr Capture Handling

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestStderrCapture** (8 connections) — `tests/integration/test_error_handling.py`
- **.test_stderr_captured_and_stored()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_stderr_displayed_in_view()** (2 connections) — `tests/integration/test_error_handling.py`
- **.test_stderr_json_parsing_attempt()** (2 connections) — `tests/integration/test_error_handling.py`
- **TC-477 to TC-479: Stderr capture and handling.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-477: Stderr output stored in session directory.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-478: Stderr lines displayed in log panel.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-479: Stderr containing JSON is parsed as JSONL if possible.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[PTY Stream Parser]] (1 shared connections)
- [[State Machine Module]] (1 shared connections)
- [[Execution State Transitions]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)
- [[Run Config Key Normalization]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 16 (84%)
- INFERRED: 3 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*