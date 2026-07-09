# Unknown Event Hint

> 14 nodes · cohesion 0.14

## Key Concepts

- **TestTimestampLocalTimezone** (14 connections) — `tests/unit/test_event_processing.py`
- **.test_local_timezone_preserves_instant()** (2 connections) — `tests/unit/test_event_processing.py`
- **.test_utc_timestamp_converted_to_local_timezone()** (2 connections) — `tests/unit/test_event_processing.py`
- **.test_utc_timestamp_parsed_with_timezone()** (2 connections) — `tests/unit/test_event_processing.py`
- **.test_utc_timestamp_without_z()** (2 connections) — `tests/unit/test_event_processing.py`
- **.test_utc_z_suffix_parsed_correctly()** (2 connections) — `tests/unit/test_event_processing.py`
- **.test_various_utc_timestamps()** (2 connections) — `tests/unit/test_event_processing.py`
- **Tests for UTC timestamp conversion to local timezone (TC-085).** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-085: _parse_timestamp returns timezone-aware datetime from UTC string.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-085: UTC timestamp can be converted to local timezone via astimezone().** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-085: 'Z' suffix in timestamps is handled as UTC.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-085: Timestamps without Z still parse as UTC if +00:00.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-085: Various UTC timestamp strings parse correctly.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-085: fromisoformat().astimezone() preserves UTC instant.** (1 connections) — `tests/unit/test_event_processing.py`

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (3 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (2 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (1 shared connections)

## Source Files

- `tests/unit/test_event_processing.py`

## Audit Trail

- EXTRACTED: 27 (82%)
- INFERRED: 6 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*