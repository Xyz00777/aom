# JSONL Parse Failure Handling

> 3 nodes · cohesion 0.33

## Key Concepts

- **TestGracefulDegradationJSONLParseFailure** (5 connections) — `tests/integration/test_error_handling.py`
- **.test_malformed_jsonl_does_not_crash()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_valid_json_following_malformed_still_parsed()** (3 connections) — `tests/integration/test_error_handling.py`

## Relationships

- [[PTY Stream Parser]] (3 shared connections)
- [[Error Handling Tests]] (1 shared connections)

## Source Files

- `tests/integration/test_error_handling.py`

## Audit Trail

- EXTRACTED: 8 (73%)
- INFERRED: 3 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*