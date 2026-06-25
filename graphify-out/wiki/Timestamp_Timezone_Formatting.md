# Timestamp Timezone Formatting

> 30 nodes · cohesion 0.06

## Key Concepts

- **TestElapsedTimeFormat** (15 connections) — `tests/unit/test_event_processing.py`
- **TestTimestampLocalTimezone** (14 connections) — `tests/unit/test_event_processing.py`
- **.test_format_status_bar_elapsed_24_plus_hours()** (2 connections) — `tests/unit/test_event_processing.py`
- **.test_format_status_bar_elapsed_float_seconds()** (2 connections) — `tests/unit/test_event_processing.py`
- **.test_format_status_bar_elapsed_over_one_hour()** (2 connections) — `tests/unit/test_event_processing.py`
- **.test_format_status_bar_elapsed_over_one_minute()** (2 connections) — `tests/unit/test_event_processing.py`
- **.test_format_status_bar_elapsed_under_one_minute()** (2 connections) — `tests/unit/test_event_processing.py`
- **.test_format_status_bar_elapsed_various_durations()** (2 connections) — `tests/unit/test_event_processing.py`
- **.test_format_status_bar_elapsed_zero()** (2 connections) — `tests/unit/test_event_processing.py`
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
- **Tests for elapsed time formatting as H:MM:SS (TC-086).** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-086: Elapsed time under 1 minute formats as 0:00:XX.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-086: Elapsed time over 1 minute formats as 0:MM:SS.** (1 connections) — `tests/unit/test_event_processing.py`
- *... and 5 more nodes in this community*

## Relationships

- [[Run State Completion Recap]] (6 shared connections)
- [[Run State Summary Panel]] (4 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Task Definition Live Refresh]] (2 shared connections)

## Source Files

- `tests/unit/test_event_processing.py`

## Audit Trail

- EXTRACTED: 58 (83%)
- INFERRED: 12 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*