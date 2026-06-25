# Subprocess Exit Codes

> 18 nodes · cohesion 0.11

## Key Concepts

- **TestSubprocessExitCodes** (13 connections) — `tests/integration/test_error_handling.py`
- **.test_exit_code_0_marks_completed()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_exit_code_127_marks_crashed_not_found()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_exit_code_130_marks_cancelled()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_exit_code_137_marks_crashed_killed()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_exit_code_1_marks_failed()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_exit_code_2_marks_failed_unreachable()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_exit_code_4_marks_crashed()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_negative_exit_code_marks_crashed_with_signal()** (3 connections) — `tests/integration/test_error_handling.py`
- **TC-469 to TC-476: Subprocess exit code interpretation.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-469: Exit code 0 marks COMPLETED state.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-470: Exit code 1 marks FAILED state.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-471: Exit code 2 marks FAILED with unreachable hosts.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-472: Exit code 4 marks CRASHED state.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-473: Exit code 127 marks CRASHED with not found message.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-474: Exit code 130 marks IDLE (user-initiated cancel).** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-475: Exit code 137 marks CRASHED with 'killed' message.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-476: Negative exit code marks CRASHED with signal info.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[Execution State Transitions]] (9 shared connections)
- [[PTY Stream Parser]] (1 shared connections)
- [[State Machine Module]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 35 (76%)
- INFERRED: 11 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*