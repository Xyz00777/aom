# Property Based Tests

> 26 nodes · cohesion 0.07

## Key Concepts

- **test_properties_redaction.py** (12 connections) — `tests/unit/test_properties_redaction.py`
- **test_properties_parser.py** (8 connections) — `tests/unit/test_properties_parser.py`
- **SearchStrategy** (6 connections)
- **valid_event_dicts()** (5 connections) — `tests/unit/test_properties_parser.py`
- **test_valid_events_survive_garbage_interleaving()** (4 connections) — `tests/unit/test_properties_parser.py`
- **_distinctive_secret()** (4 connections) — `tests/unit/test_properties_redaction.py`
- **_innocuous_key()** (4 connections) — `tests/unit/test_properties_redaction.py`
- **_password_shaped_key()** (4 connections) — `tests/unit/test_properties_redaction.py`
- **_encode_event_line()** (3 connections) — `tests/unit/test_properties_parser.py`
- **_hostname_strategy()** (3 connections) — `tests/unit/test_properties_parser.py`
- **_identifier_strategy()** (3 connections) — `tests/unit/test_properties_parser.py`
- **test_jsonline_stream_never_crashes_on_arbitrary_bytes()** (3 connections) — `tests/unit/test_properties_parser.py`
- **test_pty_stream_parser_never_crashes_on_arbitrary_bytes()** (3 connections) — `tests/unit/test_properties_parser.py`
- **test_no_log_at_top_level_censors_everything()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_no_log_in_loop_items_censors_that_item()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_password_redaction_works_through_nested_dicts()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_password_shaped_keys_are_redacted()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **test_whitelisted_keys_pass_through()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **_whitelisted_key()** (3 connections) — `tests/unit/test_properties_redaction.py`
- **Property-based tests for the JSONL parser (Batch C, family #5a).  These tests as** (1 connections) — `tests/unit/test_properties_parser.py`
- **Arbitrary bytes (decoded loosely) never raise from JsonLineStream.feed_line.** (1 connections) — `tests/unit/test_properties_parser.py`
- **Arbitrary bytes (decoded loosely) never raise from PtyStreamParser.feed_line.** (1 connections) — `tests/unit/test_properties_parser.py`
- **Well-formed events interleaved with arbitrary noise still drain in order.      T** (1 connections) — `tests/unit/test_properties_parser.py`
- **Build a realistic, JSON-encodable ansible event dict.** (1 connections) — `tests/unit/test_properties_parser.py`
- **Encode an event dict as a single JSONL line (no trailing newline).** (1 connections) — `tests/unit/test_properties_parser.py`
- *... and 1 more nodes in this community*

## Relationships

- [[Secret Redaction Configuration]] (5 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Credential String Sanitization]] (2 shared connections)
- [[PTY Stream Parser]] (1 shared connections)
- [[Session Roundtrip Invariants]] (1 shared connections)

## Source Files

- `tests/unit/test_properties_parser.py`
- `tests/unit/test_properties_redaction.py`

## Audit Trail

- EXTRACTED: 79 (91%)
- INFERRED: 8 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*