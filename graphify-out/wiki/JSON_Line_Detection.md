# JSON Line Detection

> 14 nodes · cohesion 0.14

## Key Concepts

- **TestLogPanelJsonLineDetection** (16 connections) — `tests/tui/test_panels.py`
- **.test_json_line_detection_startswith_brace()** (2 connections) — `tests/tui/test_panels.py`
- **.test_json_line_parsing_attempts_parse()** (2 connections) — `tests/tui/test_panels.py`
- **.test_json_within_text_not_parsed()** (2 connections) — `tests/tui/test_panels.py`
- **.test_malformed_json_falls_back_to_text()** (2 connections) — `tests/tui/test_panels.py`
- **.test_plain_text_line_not_json()** (2 connections) — `tests/tui/test_panels.py`
- **.test_whitespace_ignored_before_brace()** (2 connections) — `tests/tui/test_panels.py`
- **Tests for JSON vs text line detection - TC-276.** (1 connections) — `tests/tui/test_panels.py`
- **TC-276: Lines starting with '{' are JSON-parsed.** (1 connections) — `tests/tui/test_panels.py`
- **TC-276: Plain text lines (not starting with '{') are raw text.** (1 connections) — `tests/tui/test_panels.py`
- **TC-276: Malformed JSON falls back to text rendering.** (1 connections) — `tests/tui/test_panels.py`
- **TC-276 edge case: JSON embedded in text is not parsed.** (1 connections) — `tests/tui/test_panels.py`
- **TC-276: JSON lines attempt json.loads().** (1 connections) — `tests/tui/test_panels.py`
- **TC-276: Leading whitespace doesn't prevent JSON detection.** (1 connections) — `tests/tui/test_panels.py`

## Relationships

- [[Status Bar Warning Panels]] (3 shared connections)
- [[Run State Completion Recap]] (3 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[Run State Summary Panel]] (1 shared connections)

## Source Files

- `tests/tui/test_panels.py`

## Audit Trail

- EXTRACTED: 27 (77%)
- INFERRED: 8 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*