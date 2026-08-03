# Unknown Event Hint

> 16 nodes · cohesion 0.12

## Key Concepts

- **_parse_timestamp()** (12 connections) — `src/ansible_aom/core/run_state.py`
- **.handle_event()** (4 connections) — `src/ansible_aom/core/run_state.py`
- **.test_local_timezone_preserves_instant()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_utc_timestamp_converted_to_local_timezone()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_utc_timestamp_parsed_with_timezone()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_utc_timestamp_without_z()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_utc_z_suffix_parsed_correctly()** (3 connections) — `tests/unit/test_event_processing.py`
- **.test_various_utc_timestamps()** (3 connections) — `tests/unit/test_event_processing.py`
- **Process a JSONL event and update state.** (1 connections) — `src/ansible_aom/core/run_state.py`
- **Parse timestamp from event, defaulting to current time.** (1 connections) — `src/ansible_aom/core/run_state.py`
- **TC-085: _parse_timestamp returns timezone-aware datetime from UTC string.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-085: UTC timestamp can be converted to local timezone via astimezone().** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-085: 'Z' suffix in timestamps is handled as UTC.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-085: Timestamps without Z still parse as UTC if +00:00.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-085: Various UTC timestamp strings parse correctly.** (1 connections) — `tests/unit/test_event_processing.py`
- **TC-085: fromisoformat().astimezone() preserves UTC instant.** (1 connections) — `tests/unit/test_event_processing.py`

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (6 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (2 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (1 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (1 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (1 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/run_state.py`
- `tests/unit/test_event_processing.py`

## Audit Trail

- EXTRACTED: 41 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*