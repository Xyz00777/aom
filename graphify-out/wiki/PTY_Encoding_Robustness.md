# PTY Encoding Robustness

> 17 nodes · cohesion 0.15

## Key Concepts

- **TestJsonLineStreamSurvivesMojibake** (9 connections) — `tests/unit/test_encoding_robustness.py`
- **_decode_pexpect_style()** (8 connections) — `tests/unit/test_encoding_robustness.py`
- **TestPtyStreamParserSurvivesMojibake** (7 connections) — `tests/unit/test_encoding_robustness.py`
- **test_encoding_robustness.py** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_latin1_bytes_decoded_via_replace_do_not_raise()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_partial_multibyte_sequence_does_not_break_carry()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_utf8_bom_at_line_start_does_not_break_parse()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_replacement_char_in_plaintext_line_is_recorded_not_crashed()** (4 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_invalid_utf8_byte_between_events_does_not_drop_surroundings()** (3 connections) — `tests/unit/test_encoding_robustness.py`
- **.test_mojibake_in_execution_phase_keeps_state()** (3 connections) — `tests/unit/test_encoding_robustness.py`
- **Batch E item #10a — R6 encoding robustness.  The PTY-side decode (``pexpect.spaw** (1 connections) — `tests/unit/test_encoding_robustness.py`
- **Mimic pexpect's ``codec_errors='replace'`` decode.** (1 connections) — `tests/unit/test_encoding_robustness.py`
- **``JsonLineStream.feed_line`` must not crash on mojibake interleaved     with rea** (1 connections) — `tests/unit/test_encoding_robustness.py`
- **A UTF-8 BOM (``\\ufeff``) mid-stream must not corrupt subsequent         lines.** (1 connections) — `tests/unit/test_encoding_robustness.py`
- **Latin-1 bytes (``b'\\xe9\\xe8\\xea'`` for ``éèê``) interpreted         as UTF-8** (1 connections) — `tests/unit/test_encoding_robustness.py`
- **A truncated UTF-8 lead byte (``b'\\xc3'``) followed by a real         JSONL even** (1 connections) — `tests/unit/test_encoding_robustness.py`
- **The 3-phase ``PtyStreamParser`` must also tolerate mojibake at any     phase bou** (1 connections) — `tests/unit/test_encoding_robustness.py`

## Relationships

- [[Role Group Task Models]] (8 shared connections)
- [[PTY Stream Parser]] (4 shared connections)

## Source Files

- `tests/unit/test_encoding_robustness.py`

## Audit Trail

- EXTRACTED: 45 (79%)
- INFERRED: 12 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*