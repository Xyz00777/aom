# test_r6_encoding_roundtrip.py

> 26 nodes · cohesion 0.11

## Key Concepts

- **test_r6_encoding_roundtrip.py** (9 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **TestR6RendererDisplay** (7 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_renderer_print_log_does_not_show_surrogate_codepoint()** (7 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_invalid_utf8_bytes_round_trip_byte_exact_into_events_jsonl()** (6 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_valid_utf8_bytes_also_round_trip_unchanged()** (6 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **_fake_ansible_emits_jsonl_with_raw_msg()** (5 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **Path** (5 connections)
- **_read_jsonl()** (5 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **TestR6SurrogateescapeRoundTrip** (5 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **_isolate_session_dir()** (4 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **TestR6RunnerPexpectConfig** (4 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_replace_surrogates_helper_idempotent_on_clean_text()** (3 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **.test_truncate_msg_replaces_surrogate_codepoint_with_replacement()** (3 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **MonkeyPatch** (1 connections)
- **R6: encoding surrogateescape for byte-exact round-trip into ``events.jsonl``.  P** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **Sanity check: switching pexpect to ``surrogateescape`` must         not change b** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **The renderer's display path must normalise surrogate codepoints     to U+FFFD (`** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **``_truncate_msg`` runs every msg field through the         encode-with-replace/d** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **Strings without surrogate codepoints pass through unchanged.** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **End-to-end: drive the runner with a fake ansible that emits         a JSONL even** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **The runner's pexpect.spawn call must use ``codec_errors="surrogateescape"``.** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **Force ``_default_session_dir`` to a per-test tmp so the suite     doesn't litter** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **Emit a JSONL event whose ``msg`` field carries the given raw bytes.      The fak** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **The invalid-UTF-8 bytes that arrive via the PTY must round-trip     byte-exactly** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- **A PTY line carrying invalid UTF-8 bytes ``b'\\xc3\\x28'``         (the classic "** (1 connections) — `tests/integration/test_r6_encoding_roundtrip.py`
- *... and 1 more nodes in this community*

## Relationships

- [JsonLineStream](JsonLineStream.md) (4 shared connections)
- [run_playbook](run_playbook.md) (3 shared connections)
- [_compute_mode_label](_compute_mode_label.md) (2 shared connections)
- [renderer.py](renderer.py.md) (2 shared connections)
- [json.py](json.py.md) (1 shared connections)

## Source Files

- `tests/integration/test_r6_encoding_roundtrip.py`

## Audit Trail

- EXTRACTED: 73 (89%)
- INFERRED: 9 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*