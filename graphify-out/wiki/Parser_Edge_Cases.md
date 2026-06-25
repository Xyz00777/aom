# Parser Edge Cases

> 22 nodes · cohesion 0.09

## Key Concepts

- **TestEdgeCases** (15 connections) — `tests/unit/test_pty_stream.py`
- **.test_case_sensitivity_warning_patterns()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_consecutive_stats_events()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_empty_line_handled()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_json_with_newline()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_json_without_event_field()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_malformed_json_handled()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_with_variant_text()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_unicode_in_plaintext()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_very_long_line()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_whitespace_line_handled()** (3 connections) — `tests/unit/test_pty_stream.py`
- **Edge cases and boundary conditions.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Empty lines don't crash parser.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Whitespace-only lines handled gracefully.** (1 connections) — `tests/unit/test_pty_stream.py`
- **JSON without _event field returns empty.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Malformed JSON doesn't crash parser.** (1 connections) — `tests/unit/test_pty_stream.py`
- **JSON with trailing newline handled.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Multiple stats events handled (shouldn't happen but test).** (1 connections) — `tests/unit/test_pty_stream.py`
- **Password prompts with extra text still match.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Warning patterns are case-sensitive.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Unicode characters in plaintext handled.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Very long lines handled without crash.** (1 connections) — `tests/unit/test_pty_stream.py`

## Relationships

- [[PTY Stream Parser]] (11 shared connections)
- [[Role Group Task Models]] (2 shared connections)
- [[PTY Stream Parser Tests]] (1 shared connections)

## Source Files

- `tests/unit/test_pty_stream.py`

## Audit Trail

- EXTRACTED: 43 (77%)
- INFERRED: 13 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*