# Run State Completion Recap

> 271 nodes · cohesion 0.01

## Key Concepts

- **PtyStreamParser** (333 connections) — `src/ansible_aom/core/parser.py`
- **TestPtyStreamParserStderrLineEmission** (41 connections) — `tests/unit/test_parser.py`
- **TestPtyStreamParserPhases** (25 connections) — `tests/unit/test_parser.py`
- **TestWarningDetectionThroughAnsiPrefix** (18 connections) — `tests/unit/test_parser.py`
- **TestPasswordPromptPatterns** (17 connections) — `tests/unit/test_pty_stream.py`
- **TestEdgeCases** (15 connections) — `tests/unit/test_pty_stream.py`
- **TestConftestFixtures** (13 connections) — `tests/unit/test_pty_stream.py`
- **TestPtyStreamParserPhaseTransitions** (13 connections) — `tests/unit/test_pty_stream.py`
- **TestWarningPatternDetection** (13 connections) — `tests/unit/test_pty_stream.py`
- **TestPlayRecapDetection** (11 connections) — `tests/unit/test_pty_stream.py`
- **TestPasswordPrompts** (10 connections) — `tests/integration/test_playbook_parser.py`
- **TestPhaseTransitions** (10 connections) — `tests/integration/test_playbook_parser.py`
- **TestPlaintextLineHandling** (10 connections) — `tests/unit/test_pty_stream.py`
- **TestWarningDetection** (9 connections) — `tests/integration/test_playbook_parser.py`
- **TestTaskStartCountsAsHeartbeat** (6 connections) — `tests/unit/test_runner_heartbeat.py`
- **TestGracefulDegradationJSONLParseFailure** (5 connections) — `tests/integration/test_error_handling.py`
- **test_parser_recap_cap.py** (5 connections) — `tests/unit/test_parser_recap_cap.py`
- **_recap_line()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **test_recap_lines_capped_at_max_log_lines()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **test_recap_lines_keeps_most_recent_when_capped()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **test_recap_lines_pin_against_constant_drift()** (4 connections) — `tests/unit/test_parser_recap_cap.py`
- **.test_malformed_jsonl_does_not_crash()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_valid_json_following_malformed_still_parsed()** (3 connections) — `tests/integration/test_error_handling.py`
- **.test_become_password_prompt_detected()** (3 connections) — `tests/integration/test_playbook_parser.py`
- **.test_clear_password_prompt()** (3 connections) — `tests/integration/test_playbook_parser.py`
- *... and 246 more nodes in this community*

## Relationships

- [Role Group Task Models](Role_Group_Task_Models.md) (46 shared connections)
- [Execution State Transitions](Execution_State_Transitions.md) (34 shared connections)
- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (25 shared connections)
- [AOM TUI Application](AOM_TUI_Application.md) (20 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (12 shared connections)
- [Run History Mining](Run_History_Mining.md) (11 shared connections)
- [Three-Pane Inspect App](Three-Pane_Inspect_App.md) (10 shared connections)
- [16-Color Fallback](16-Color_Fallback.md) (9 shared connections)
- [Subprocess Exit Codes](Subprocess_Exit_Codes.md) (9 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (9 shared connections)
- [Host Name Resolution](Host_Name_Resolution.md) (7 shared connections)
- [Password Timeout](Password_Timeout.md) (7 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/integration/test_error_handling.py`
- `tests/integration/test_playbook_parser.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_parser_recap_cap.py`
- `tests/unit/test_pty_stream.py`
- `tests/unit/test_runner_heartbeat.py`

## Audit Trail

- EXTRACTED: 585 (56%)
- INFERRED: 459 (44%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*