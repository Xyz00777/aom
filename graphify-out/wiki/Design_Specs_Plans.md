# Design Specs Plans

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestHandleEventTimestampParsing** (11 connections) — `tests/unit/test_event_processing.py`
- **.test_handle_event_invalid_timestamp_handled_gracefully()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_handle_event_missing_timestamp_defaults_to_now()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_handle_event_parses_iso_timestamp()** (3 connections) — `tests/unit/test_event_processing.py`
- **Tests for timestamp parsing in handle_event (TC-198).** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-198: Timestamp is parsed from _timestamp field as ISO format datetime.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-198: Missing _timestamp field defaults to current time.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-198: Invalid timestamp string is handled gracefully.** (1 connections) — `tests/unit/test_event_processing.py`

## Relationships

- [CLI Interface Tests](CLI_Interface_Tests.md) (5 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (3 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)

## Source Files

- `tests/unit/test_event_processing.py`

## Audit Trail

- EXTRACTED: 18 (75%)
- INFERRED: 6 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*