# Status Bar Formatting

> 16 nodes · cohesion 0.16

## Key Concepts

- **test_properties_parser.py** (10 connections) — `tests/unit/test_properties_parser.py`
- **valid_event_dicts()** (5 connections) — `tests/unit/test_properties_parser.py`
- **test_valid_events_survive_garbage_interleaving()** (4 connections) — `tests/unit/test_properties_parser.py`
- **_encode_event_line()** (3 connections) — `tests/unit/test_properties_parser.py`
- **_hostname_strategy()** (3 connections) — `tests/unit/test_properties_parser.py`
- **_identifier_strategy()** (3 connections) — `tests/unit/test_properties_parser.py`
- **test_jsonline_stream_never_crashes_on_arbitrary_bytes()** (3 connections) — `tests/unit/test_properties_parser.py`
- **test_pty_stream_parser_never_crashes_on_arbitrary_bytes()** (3 connections) — `tests/unit/test_properties_parser.py`
- **SearchStrategy** (2 connections)
- **DrawFn** (1 connections)
- **Property-based tests for the JSONL parser (Batch C, family #5a).  These tests as** (1 connections) — `tests/unit/test_properties_parser.py`
- **Arbitrary bytes (decoded loosely) never raise from JsonLineStream.feed_line.** (1 connections) — `tests/unit/test_properties_parser.py`
- **Arbitrary bytes (decoded loosely) never raise from PtyStreamParser.feed_line.** (1 connections) — `tests/unit/test_properties_parser.py`
- **Well-formed events interleaved with arbitrary noise still drain in order.      T** (1 connections) — `tests/unit/test_properties_parser.py`
- **Build a realistic, JSON-encodable ansible event dict.** (1 connections) — `tests/unit/test_properties_parser.py`
- **Encode an event dict as a single JSONL line (no trailing newline).** (1 connections) — `tests/unit/test_properties_parser.py`

## Relationships

- [Three-Pane Inspect App](Three-Pane_Inspect_App.md) (2 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (1 shared connections)

## Source Files

- `tests/unit/test_properties_parser.py`

## Audit Trail

- EXTRACTED: 40 (93%)
- INFERRED: 3 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*