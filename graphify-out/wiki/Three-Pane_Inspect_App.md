# Three-Pane Inspect App

> 80 nodes · cohesion 0.04

## Key Concepts

- **JsonLineStream** (78 connections) — `src/ansible_aom/core/parser.py`
- **TestJsonLineStreamBasics** (31 connections) — `tests/unit/test_parser.py`
- **TestJsonLineStreamCarryBuffer** (20 connections) — `tests/unit/test_parser.py`
- **TestPreParsePhase** (17 connections) — `tests/unit/test_parser.py`
- **TestJsonLineStreamSurvivesMojibake** (9 connections) — `tests/unit/test_encoding_robustness.py`
- **_decode_pexpect_style()** (8 connections) — `tests/unit/test_encoding_robustness.py`
- **TestPtyStreamParserSurvivesMojibake** (7 connections) — `tests/unit/test_encoding_robustness.py`
- **test_encoding_robustness.py** (6 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_latin1_bytes_decoded_via_replace_do_not_raise()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_partial_multibyte_sequence_does_not_break_carry()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_utf8_bom_at_line_start_does_not_break_parse()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_replacement_char_in_plaintext_line_is_recorded_not_crashed()** (4 connections) — `tests/unit/test_encoding_robustness.py`
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
- **.test_feed_line_event_task_start()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_json_without_event_field()** (3 connections) — `tests/unit/test_parser.py`
- *... and 55 more nodes in this community*

## Relationships

- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (18 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (12 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (11 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (11 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (9 shared connections)
- [Host Overview Table](Host_Overview_Table.md) (6 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (5 shared connections)
- [test_parser_orjson_swap.py](test_parser_orjson_swap.py.md) (3 shared connections)
- [Warning Pattern Detection](Warning_Pattern_Detection.md) (2 shared connections)
- [Conftest Fixture Validation](Conftest_Fixture_Validation.md) (2 shared connections)
- [Status Bar Formatting](Status_Bar_Formatting.md) (2 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/unit/test_encoding_robustness.py`
- `tests/unit/test_parser.py`

## Audit Trail

- EXTRACTED: 172 (54%)
- INFERRED: 145 (46%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*