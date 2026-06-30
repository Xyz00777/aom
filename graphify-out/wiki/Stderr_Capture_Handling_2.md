# Stderr Capture Handling

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestStderrHandling** (7 connections) — `tests/integration/test_error_handling.py`
- **.test_stderr_file_creation()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_stderr_mixed_with_jsonl()** (2 connections) — `tests/integration/test_error_handling.py`
- **Tests for stderr capture and handling.** (1 connections) — `tests/integration/test_error_handling.py`
- **stderr.log file is created in session directory.** (1 connections) — `tests/integration/test_error_handling.py`
- **stderr might contain JSONL events in some cases.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[PTY Stream Parser]] (1 shared connections)
- [[State Machine Module]] (1 shared connections)
- [[Execution State Transitions]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)
- [[Run Config Key Normalization]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 12 (80%)
- INFERRED: 3 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*