# test_pty_stream.py

> 50 nodes · cohesion 0.04

## Key Concepts

- **test_pty_stream.py** (18 connections) — `tests/unit/test_pty_stream.py`
- **TestMixedStreamHandling** (10 connections) — `tests/unit/test_pty_stream.py`
- **TestPlaintextLineHandling** (10 connections) — `tests/unit/test_pty_stream.py`
- **TestPatternRegexes** (8 connections) — `tests/unit/test_pty_stream.py`
- **TestPhaseStateMachine** (8 connections) — `tests/unit/test_pty_stream.py`
- **TestRendererProtocolPasswordHandling** (8 connections) — `tests/unit/test_pty_stream.py`
- **.test_invalid_json_returns_empty()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_jsonl_and_plaintext_interleaved()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_jsonl_returns_events()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_before_jsonl_start()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_returns_stderr_line()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_cannot_go_backwards_from_execution()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_phase_properties_immutability()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_phase_transition_order()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_lines_in_execution_phase()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_lines_not_warning()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_lines_order_preserved()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_lines_stored()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_vs_warning_classification()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_full_workflow_simulation()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_detected_before_jsonl()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_pending_password_prompt_interface()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_patterns_match_expected_prompts()** (2 connections) — `tests/unit/test_pty_stream.py`
- **.test_recap_pattern_matches_various_formats()** (2 connections) — `tests/unit/test_pty_stream.py`
- **.test_warning_patterns_match_expected_lines()** (2 connections) — `tests/unit/test_pty_stream.py`
- *... and 25 more nodes in this community*

## Relationships

- [PtyStreamParser](PtyStreamParser.md) (25 shared connections)
- [StreamPhase](StreamPhase.md) (7 shared connections)
- [WarningType](WarningType.md) (5 shared connections)
- [HostRunState](HostRunState.md) (1 shared connections)
- [json.py](json.py.md) (1 shared connections)
- [TestEdgeCases](TestEdgeCases.md) (1 shared connections)
- [TestPlayRecapDetection](TestPlayRecapDetection.md) (1 shared connections)
- [TestPtyStreamParserPhaseTransitions](TestPtyStreamParserPhaseTransitions.md) (1 shared connections)
- [TestWarningPatternDetection](TestWarningPatternDetection.md) (1 shared connections)

## Source Files

- `tests/unit/test_pty_stream.py`

## Audit Trail

- EXTRACTED: 126 (89%)
- INFERRED: 15 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*