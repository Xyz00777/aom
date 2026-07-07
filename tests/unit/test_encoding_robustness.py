"""Batch E item #10a — R6 encoding robustness.

The PTY-side decode (``pexpect.spawn(encoding="utf-8", codec_errors="replace")``
in ``runner.py``) converts bytes to str via ``str.decode(..., errors="replace")``
before any line reaches the parser. The parser therefore never sees raw bytes
on the real code path — but it must still survive the resulting strings, which
can include U+FFFD replacement characters, embedded BOMs, and mojibake from
locale-mismatched ansible plugins.

These tests target the parser layer with strings that simulate what pexpect's
decoder produces from realistic mis-encoded byte streams. The contract is:

1. Surrounding valid JSONL events still parse.
2. No exception escapes ``feed_line``.
3. Non-JSON garbage lines route through the non-JSON handler or are silently
   dropped — never crash.
"""

from __future__ import annotations

import json

from ansible_aom.core.parser import JsonLineStream, PtyStreamParser, StreamPhase


def _decode_pexpect_style(raw: bytes) -> str:
    """Mimic pexpect's ``codec_errors='replace'`` decode."""
    return raw.decode("utf-8", errors="replace")


class TestJsonLineStreamSurvivesMojibake:
    """``JsonLineStream.feed_line`` must not crash on mojibake interleaved
    with real JSONL events, and must still yield the surrounding events."""

    def test_invalid_utf8_byte_between_events_does_not_drop_surroundings(self) -> None:
        stream = JsonLineStream()
        before = json.dumps({"_event": "v2_playbook_on_start"})
        # b"\xc3\x28" — a classic invalid UTF-8 sequence (lone continuation
        # byte after a 2-byte lead). pexpect would decode this to "�("
        # via errors="replace".
        garbage = _decode_pexpect_style(b"\xc3\x28 noisy plugin output")
        after = json.dumps({"_event": "v2_playbook_on_stats"})

        out_before = stream.feed_line(before)
        out_garbage = stream.feed_line(garbage)
        out_after = stream.feed_line(after)

        assert len(out_before) == 1 and out_before[0]["_event"] == "v2_playbook_on_start"
        assert out_garbage == []  # not JSON, returns empty list
        assert len(out_after) == 1 and out_after[0]["_event"] == "v2_playbook_on_stats"

    def test_utf8_bom_at_line_start_does_not_break_parse(self) -> None:
        """A UTF-8 BOM (``\\ufeff``) mid-stream must not corrupt subsequent
        lines. The BOM-prefixed line itself may be classified as non-JSON
        (it no longer starts with ``{``); the next line must parse cleanly.
        """
        stream = JsonLineStream()
        bom_line = _decode_pexpect_style(b'\xef\xbb\xbf{"_event": "v2_playbook_on_start"}')
        # bom_line now starts with ﻿ — JsonLineStream's `startswith("{")`
        # check will treat it as non-JSON. That's acceptable; the contract
        # is "doesn't crash and doesn't poison subsequent reads".
        out_bom = stream.feed_line(bom_line)
        assert out_bom == []

        # Subsequent valid event still parses.
        out_next = stream.feed_line(json.dumps({"_event": "v2_playbook_on_stats"}))
        assert len(out_next) == 1 and out_next[0]["_event"] == "v2_playbook_on_stats"

    def test_latin1_bytes_decoded_via_replace_do_not_raise(self) -> None:
        """Latin-1 bytes (``b'\\xe9\\xe8\\xea'`` for ``éèê``) interpreted
        as UTF-8 with ``errors='replace'`` become U+FFFD characters. The
        parser must accept the resulting string without raising
        ``UnicodeDecodeError`` (it shouldn't — feed_line takes str — but
        we assert it explicitly because R6 demands the defensive contract).
        """
        stream = JsonLineStream()
        latin1_line = _decode_pexpect_style(b"plugin emitted \xe9\xe8\xea here")

        # Just calling feed_line must not raise.
        result = stream.feed_line(latin1_line)
        assert result == []

    def test_partial_multibyte_sequence_does_not_break_carry(self) -> None:
        """A truncated UTF-8 lead byte (``b'\\xc3'``) followed by a real
        JSONL event must not leave the carry buffer wedged."""
        stream = JsonLineStream()
        truncated = _decode_pexpect_style(b"\xc3")  # becomes "�"
        stream.feed_line(truncated)

        out = stream.feed_line(json.dumps({"_event": "v2_playbook_on_stats"}))
        assert len(out) == 1 and out[0]["_event"] == "v2_playbook_on_stats"


class TestPtyStreamParserSurvivesMojibake:
    """The 3-phase ``PtyStreamParser`` must also tolerate mojibake at any
    phase boundary."""

    def test_mojibake_in_execution_phase_keeps_state(self) -> None:
        parser = PtyStreamParser()
        # Drive into EXECUTION phase.
        start_event = json.dumps({"_event": "v2_playbook_on_start"})
        parser.feed_line(start_event)
        assert parser.phase == StreamPhase.EXECUTION

        # Inject a line of pure mojibake — it's legitimate stderr plaintext
        # and should emit an aom_stderr_line event, not crash.
        garbage = _decode_pexpect_style(b"\xc3\x28\xff\xfe random bytes")
        out = parser.feed_line(garbage)
        assert len(out) == 1
        assert out[0]["_event"] == "aom_stderr_line"
        assert parser.phase == StreamPhase.EXECUTION  # phase preserved

        # Next valid event still routes correctly.
        stats = json.dumps({"_event": "v2_playbook_on_stats"})
        out_stats = parser.feed_line(stats)
        assert len(out_stats) == 1
        assert parser.phase == StreamPhase.POST_RUN_RECAP

    def test_replacement_char_in_plaintext_line_is_recorded_not_crashed(self) -> None:
        """U+FFFD replacement chars in a plaintext warning line must flow
        through ``_handle_plaintext`` without raising."""
        parser = PtyStreamParser()
        # Drive into EXECUTION phase first.
        parser.feed_line(json.dumps({"_event": "v2_playbook_on_start"}))

        mojibake_warning = _decode_pexpect_style(
            b"[WARNING]: deprecated plugin reported \xc3\x28 status"
        )
        parser.feed_line(mojibake_warning)

        # The warning was captured (the [WARNING]: prefix anchors before
        # the mojibake), even if the message body contains U+FFFD.
        assert len(parser.warnings) == 1
        assert "�" in parser.warnings[0].message
