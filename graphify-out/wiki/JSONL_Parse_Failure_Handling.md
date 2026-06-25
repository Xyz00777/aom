# JSONL Parse Failure Handling

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestGracefulDegradationJSONLParseFailure** (7 connections) — `tests/integration/test_error_handling.py`
- **.test_malformed_jsonl_does_not_crash()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_valid_json_following_malformed_still_parsed()** (3 connections) — `tests/integration/test_error_handling.py`
- **TC-445: Graceful Degradation - JSONL Parse Failure.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-445: Malformed JSONL line is handled gracefully.** (1 connections) — `tests/integration/test_error_handling.py`
- **TC-445: Valid JSONL after malformed line still processed.** (1 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[PTY Stream Parser]] (3 shared connections)
- [[State Machine Module]] (1 shared connections)
- [[Execution State Transitions]] (1 shared connections)
- [[Error Handling Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 11 (69%)
- INFERRED: 5 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*