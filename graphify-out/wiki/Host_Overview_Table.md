# Host Overview Table

> 31 nodes · cohesion 0.09

## Key Concepts

- **test_r6_encoding_roundtrip.py** (9 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **TestR6RendererDisplay** (7 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_renderer_print_log_does_not_show_surrogate_codepoint()** (7 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_invalid_utf8_bytes_round_trip_byte_exact_into_events_jsonl()** (6 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_valid_utf8_bytes_also_round_trip_unchanged()** (6 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **_fake_ansible_emits_jsonl_with_raw_msg()** (5 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **Path** (5 connections)
- **_read_jsonl()** (5 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **TestR6ParserAcceptsSurrogateLines** (5 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **TestR6SurrogateescapeRoundTrip** (5 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **_isolate_session_dir()** (4 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **TestR6RunnerPexpectConfig** (4 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_mojibake_subsequent_lines_still_parse()** (3 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_replace_surrogates_helper_idempotent_on_clean_text()** (3 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_truncate_msg_replaces_surrogate_codepoint_with_replacement()** (3 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_jsonl_line_with_surrogate_parses()** (2 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **MonkeyPatch** (1 connections)
- **R6: encoding surrogateescape for byte-exact round-trip into ``events.jsonl``.  P** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **Sanity check: switching pexpect to ``surrogateescape`` must         not change b** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **The renderer's display path must normalise surrogate codepoints     to U+FFFD (`** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **``_truncate_msg`` runs every msg field through the         encode-with-replace/d** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **Strings without surrogate codepoints pass through unchanged.** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **End-to-end: drive the runner with a fake ansible that emits         a JSONL even** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **The parser's ``JsonLineStream`` must accept lines containing     surrogate codep** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **A surrogate-bearing line must not poison subsequent lines.** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- *... and 6 more nodes in this community*

## Relationships

- [Three-Pane Inspect App](Three-Pane_Inspect_App.md) (6 shared connections)
- [Replay Determinism Tests](Replay_Determinism_Tests.md) (3 shared connections)
- [Replay Frame Signatures](Replay_Frame_Signatures.md) (2 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (2 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/integration/test_r6_encoding_roundtrip.py`

## Audit Trail

- EXTRACTED: 82 (87%)
- INFERRED: 12 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*