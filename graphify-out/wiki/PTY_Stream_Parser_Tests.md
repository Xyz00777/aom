# PTY Stream Parser Tests

> 30 nodes · cohesion 0.07

## Key Concepts

- **test_pty_stream.py** (16 connections) — `tests/unit/test_pty_stream.py`
- **TestMixedStreamHandling** (10 connections) — `tests/unit/test_pty_stream.py`
- **TestPatternRegexes** (8 connections) — `tests/unit/test_pty_stream.py`
- **TestRendererProtocolPasswordHandling** (8 connections) — `tests/unit/test_pty_stream.py`
- **.test_invalid_json_returns_empty()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_jsonl_and_plaintext_interleaved()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_jsonl_returns_events()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_before_jsonl_start()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_returns_empty()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_full_workflow_simulation()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_detected_before_jsonl()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_pending_password_prompt_interface()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_patterns_match_expected_prompts()** (2 connections) — `tests/unit/test_pty_stream.py`
- **.test_recap_pattern_matches_various_formats()** (2 connections) — `tests/unit/test_pty_stream.py`
- **.test_warning_patterns_match_expected_lines()** (2 connections) — `tests/unit/test_pty_stream.py`
- **Unit tests for PTY stream parsing.  Covers TEST_SPECIFICATION.md Sections 5.5, 5** (1 connections) — `tests/unit/test_pty_stream.py`
- **Section 5.6: JSONL events interleaved with plaintext.** (1 connections) — `tests/unit/test_pty_stream.py`
- **JSONL events and plaintext interleaved correctly.** (1 connections) — `tests/unit/test_pty_stream.py`
- **Plaintext before v2_playbook_on_start is captured.** (1 connections) — `tests/unit/test_pty_stream.py`
- **feed_line returns parsed events for JSONL.** (1 connections) — `tests/unit/test_pty_stream.py`
- **feed_line returns empty list for plaintext.** (1 connections) — `tests/unit/test_pty_stream.py`
- **feed_line returns empty for invalid JSON.** (1 connections) — `tests/unit/test_pty_stream.py`
- **TC-133-141: Validate regex patterns.** (1 connections) — `tests/unit/test_pty_stream.py`
- **All password patterns match their expected prompts.** (1 connections) — `tests/unit/test_pty_stream.py`
- **All warning patterns match their expected lines.** (1 connections) — `tests/unit/test_pty_stream.py`
- *... and 5 more nodes in this community*

## Relationships

- [[PTY Stream Parser]] (11 shared connections)
- [[Role Group Task Models]] (6 shared connections)
- [[Run History Mining]] (1 shared connections)
- [[Compact Password Passthrough]] (1 shared connections)
- [[Conftest Fixture Validation]] (1 shared connections)
- [[Parser Edge Cases]] (1 shared connections)
- [[Password Prompt Handling]] (1 shared connections)
- [[Password Pattern Detection]] (1 shared connections)
- [[Phase State Machine]] (1 shared connections)
- [[Plaintext Line Handling]] (1 shared connections)
- [[Play Recap Detection]] (1 shared connections)
- [[Parser Phase Transitions]] (1 shared connections)

## Source Files

- `tests/unit/test_pty_stream.py`

## Audit Trail

- EXTRACTED: 70 (80%)
- INFERRED: 17 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*