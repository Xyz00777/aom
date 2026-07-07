# UUIDv7 Session Generation

> 12 nodes · cohesion 0.18

## Key Concepts

- **TestGenerateUUIDv7** (7 connections) — `tests/integration/test_session.py`
- **generate_uuidv7()** (7 connections) — `src/ansible_aom/session/store.py`
- **.test_uuidv7_contains_timestamp()** (3 connections) — `tests/integration/test_session.py`
- **.test_uuidv7_first_8_chars_usable_for_display()** (3 connections) — `tests/integration/test_session.py`
- **.test_uuidv7_format_matches_pattern()** (3 connections) — `tests/integration/test_session.py`
- **.test_uuidv7_is_time_sortable()** (3 connections) — `tests/integration/test_session.py`
- **.start_session()** (3 connections) — `src/ansible_aom/session/store.py`
- **TC-218: Session UUIDv7 Format Validation.** (1 connections) — `tests/integration/test_session.py`
- **UUIDv7 matches expected format pattern.** (1 connections) — `tests/integration/test_session.py`
- **UUIDv7 values are time-sortable (earlier timestamps produce smaller UUIDs).** (1 connections) — `tests/integration/test_session.py`
- **First 8 characters of UUIDv7 can be used for display.** (1 connections) — `tests/integration/test_session.py`
- **UUIDv7 embeds timestamp in first segment.** (1 connections) — `tests/integration/test_session.py`

## Relationships

- [[Session Recording Tests]] (3 shared connections)
- [[Inspect CLI Commands]] (1 shared connections)

## Source Files

- `src/ansible_aom/session/store.py`
- `tests/integration/test_session.py`

## Audit Trail

- EXTRACTED: 25 (74%)
- INFERRED: 9 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*