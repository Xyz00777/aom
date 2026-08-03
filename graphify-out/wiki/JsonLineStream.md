# JsonLineStream

> 94 nodes · cohesion 0.03

## Key Concepts

- **JsonLineStream** (78 connections) — `src/ansible_aom/core/parser.py`
- **TestJsonLineStreamBasics** (31 connections) — `tests/unit/test_parser.py`
- **TestJsonLineStreamCarryBuffer** (20 connections) — `tests/unit/test_parser.py`
- **TestPreParsePhase** (17 connections) — `tests/unit/test_parser.py`
- **TestJsonLineStreamSurvivesMojibake** (9 connections) — `tests/unit/test_encoding_robustness.py`
- **_decode_pexpect_style()** (8 connections) — `tests/unit/test_encoding_robustness.py`
- **TestPtyStreamParserSurvivesMojibake** (7 connections) — `tests/unit/test_encoding_robustness.py`
- **test_encoding_robustness.py** (6 connections) — `tests/unit/test_encoding_robustness.py`
- **test_parser_orjson_swap.py** (6 connections) — `tests/unit/test_parser_orjson_swap.py`
- **TestR6ParserAcceptsSurrogateLines** (5 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_latin1_bytes_decoded_via_replace_do_not_raise()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_partial_multibyte_sequence_does_not_break_carry()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_utf8_bom_at_line_start_does_not_break_parse()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_replacement_char_in_plaintext_line_is_recorded_not_crashed()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **test_perf_005_parser_byte_equal_to_stdlib()** (4 connections) — `tests/unit/test_parser_orjson_swap.py`
- **.test_mojibake_subsequent_lines_still_parse()** (3 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_invalid_utf8_byte_between_events_does_not_drop_surroundings()** (3 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_mojibake_in_execution_phase_keeps_state()** (3 connections) — `tests/unit/test_encoding_robustness.py`
- **test_perf_006_carry_buffer_still_works_after_swap()** (3 connections) — `tests/unit/test_parser_orjson_swap.py`
- **test_perf_007_non_dict_json_rejected()** (3 connections) — `tests/unit/test_parser_orjson_swap.py`
- **.test_feed_line_event_play_start()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_playbook_start()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_runner_failed()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_runner_ok()** (3 connections) — `tests/unit/test_parser.py`
- **.test_feed_line_event_runner_ok_changed()** (3 connections) — `tests/unit/test_parser.py`
- *... and 69 more nodes in this community*

## Relationships

- [WarningType](WarningType.md) (20 shared connections)
- [HostRunState](HostRunState.md) (12 shared connections)
- [StreamPhase](StreamPhase.md) (9 shared connections)
- [PtyStreamParser](PtyStreamParser.md) (9 shared connections)
- [TaskDefinition](TaskDefinition.md) (7 shared connections)
- [PlayDefinition](PlayDefinition.md) (4 shared connections)
- [test_r6_encoding_roundtrip.py](test_r6_encoding_roundtrip.py.md) (4 shared connections)
- [json.py](json.py.md) (3 shared connections)
- [Warning Pattern Detection](Warning_Pattern_Detection.md) (2 shared connections)
- [Conftest Fixture Validation](Conftest_Fixture_Validation.md) (2 shared connections)
- [parse_list_tasks_output](parse_list_tasks_output.md) (2 shared connections)
- [Status Bar Formatting](Status_Bar_Formatting.md) (2 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`
- `tests/integration/test_r6_encoding_roundtrip.py`
- `tests/unit/test_encoding_robustness.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_parser_orjson_swap.py`

## Audit Trail

- EXTRACTED: 269 (77%)
- INFERRED: 81 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*