# Three-Pane Inspect App

> 84 nodes · cohesion 0.03

## Key Concepts

- **JsonLineStream** (83 connections) — `src/ansible_aom/core/parser.py`
- **TestJsonLineStreamBasics** (31 connections) — `tests/unit/test_parser.py`
- **TestJsonLineStreamCarryBuffer** (19 connections) — `tests/unit/test_parser.py`
- **TestPreParsePhase** (17 connections) — `tests/unit/test_parser.py`
- **TestJsonLineStreamSurvivesMojibake** (9 connections) — `tests/unit/test_encoding_robustness.py`
- **_decode_pexpect_style()** (8 connections) — `tests/unit/test_encoding_robustness.py`
- **TestPtyStreamParserSurvivesMojibake** (7 connections) — `tests/unit/test_encoding_robustness.py`
- **TestR6ParserAcceptsSurrogateLines** (5 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **test_encoding_robustness.py** (5 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_latin1_bytes_decoded_via_replace_do_not_raise()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_partial_multibyte_sequence_does_not_break_carry()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_utf8_bom_at_line_start_does_not_break_parse()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_replacement_char_in_plaintext_line_is_recorded_not_crashed()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_mojibake_subsequent_lines_still_parse()** (3 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_invalid_utf8_byte_between_events_does_not_drop_surroundings()** (3 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_mojibake_in_execution_phase_keeps_state()** (3 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_feed_line_event_play_start()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_playbook_start()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_runner_failed()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_runner_ok()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_runner_ok_changed()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_runner_skipped()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_runner_start()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_runner_unreachable()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_stats()** (3 connections) — `tests/unit/test_parser.py`
- *... and 59 more nodes in this community*

## Relationships

- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (19 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (10 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (9 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (6 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (4 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (4 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (4 shared connections)
- [Host Overview Table](Host_Overview_Table.md) (4 shared connections)
- [Community 484](Community_484.md) (3 shared connections)
- [Diagnostics and Profiler](Diagnostics_and_Profiler.md) (3 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (3 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (3 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/integration/test_r6_encoding_roundtrip.py`
- `tests/unit/test_encoding_robustness.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 175 (53%)
- INFERRED: 154 (47%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*