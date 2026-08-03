# TestStderrHandling

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestStderrHandling** (5 connections) — `tests/integration/test_error_handling.py`
- **.test_stderr_file_creation()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_stderr_mixed_with_jsonl()** (2 connections) — `tests/integration/test_error_handling.py`
- **Tests for stderr capture and handling.** (1 connections) — `tests/integration/test_error_handling.py`
- **stderr.log file is created in session directory.** (1 connections) — `tests/integration/test_error_handling.py`
- **stderr might contain JSONL events in some cases.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [Run State Completion Recap](Run_State_Completion_Recap.md) (1 shared connections)
- [Completion Host Table](Completion_Host_Table.md) (1 shared connections)
- [Role Inference Indexes](Role_Inference_Indexes.md) (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 12 (92%)
- INFERRED: 1 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*