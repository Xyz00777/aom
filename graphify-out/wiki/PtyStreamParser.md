# PtyStreamParser

> 178 nodes · cohesion 0.02

## Key Concepts

- **PtyStreamParser** (338 connections) — `src/ansible_aom/core/parser.py`
- **TestPtyStreamParserStderrLineEmission** (41 connections) — `tests/unit/test_parser.py`
- **TestPasswordPromptPatterns** (17 connections) — `tests/unit/test_pty_stream.py`
- **TestPtyStreamParserLatestOutputIsPlaintext** (15 connections) — `tests/unit/test_parser.py`
- **TestConftestFixtures** (13 connections) — `tests/unit/test_pty_stream.py`
- **TestPasswordPrompts** (10 connections) — `tests/integration/test_playbook_parser.py`
- **TestPhaseTransitions** (10 connections) — `tests/integration/test_playbook_parser.py`
- **TestCompactModePasswordPassThrough** (10 connections) — `tests/unit/test_pty_stream.py`
- **TestPasswordPromptHandling** (10 connections) — `tests/unit/test_pty_stream.py`
- **TestWarningDetection** (9 connections) — `tests/integration/test_playbook_parser.py`
- **TestGracefulDegradationJSONLParseFailure** (5 connections) — `tests/integration/test_error_handling.py`
- **.test_malformed_jsonl_does_not_crash()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_valid_json_following_malformed_still_parsed()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_become_password_prompt_detected()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_clear_password_prompt()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_ssh_password_prompt_detected()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_vault_password_prompt_detected()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_execution_to_post_run_on_stats_event()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_initial_phase_is_pre_run_prompts()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_non_json_lines_handled_during_execution()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_pre_run_to_execution_on_start_event()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_deprecated_pattern()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_deprecation_warning_pattern()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_warning_pattern()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_ansi_stripped_before_classification()** (3 connections) — `tests/unit/test_parser.py`
- *... and 153 more nodes in this community*

## Relationships

- [StreamPhase](StreamPhase.md) (41 shared connections)
- [WarningType](WarningType.md) (39 shared connections)
- [test_pty_stream.py](test_pty_stream.py.md) (25 shared connections)
- [TestWarningPatternsEdgeCases](TestWarningPatternsEdgeCases.md) (23 shared connections)
- [_drive](_drive.md) (14 shared connections)
- [TestPtyStreamParserPhases](TestPtyStreamParserPhases.md) (11 shared connections)
- [TestEdgeCases](TestEdgeCases.md) (11 shared connections)
- [_safe_loads](_safe_loads.md) (10 shared connections)
- [TestEventParsing](TestEventParsing.md) (9 shared connections)
- [JsonLineStream](JsonLineStream.md) (9 shared connections)
- [TestPtyStreamParserPhaseTransitions](TestPtyStreamParserPhaseTransitions.md) (9 shared connections)
- [TestWarningPatternDetection](TestWarningPatternDetection.md) (9 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/integration/test_error_handling.py`
- `tests/integration/test_playbook_parser.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_pty_stream.py`

## Audit Trail

- EXTRACTED: 630 (79%)
- INFERRED: 165 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*