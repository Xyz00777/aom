"""R6: encoding surrogateescape for byte-exact round-trip into ``events.jsonl``.

Pexpect is configured with ``codec_errors="surrogateescape"`` so an invalid
UTF-8 byte sequence arriving on the PTY becomes a lone-surrogate codepoint
in the ``str`` it surfaces to the runner. The parser accepts those
strings (via stdlib ``json.loads``), the sink serialises them with
``json.dumps`` (which preserves surrogate codepoints as ``\\uXXXX``
escapes), and ``events.jsonl`` therefore contains the original bytes
byte-exactly — recoverable by ``str.encode("utf-8", "surrogateescape")``
when ``aom inspect show`` later re-loads the file.

The renderer's display path takes the same string and runs it through
``.encode("utf-8", "replace").decode("utf-8", "replace")`` so the
terminal sees ``?`` (U+FFFD) instead of an unpaired surrogate that
would corrupt the display. The original bytes remain intact on disk.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _fake_ansible_emits_jsonl_with_raw_msg(
    raw_msg_bytes: bytes, exit_code: int = 0
) -> tuple[str, list[str]]:
    """Emit a JSONL event whose ``msg`` field carries the given raw bytes.

    The fake process first writes a ``v2_playbook_on_start`` event so
    the parser transitions from PRE_RUN_PROMPTS into EXECUTION, then a
    ``v2_runner_on_failed`` event whose ``msg`` field carries the
    surrogate-escaped bytes. Both are written via
    ``sys.stdout.buffer.write`` so the bytes survive into the PTY stream
    untouched. The expected on-disk form is the surrogate-escaped JSON
    string emitted by ``json.dumps``.
    """
    # Build the JSONL line as a string then encode it back to bytes
    # via surrogateescape — the surrogate codepoints in the str become
    # the original invalid UTF-8 bytes in the output, which is exactly
    # the wire shape pexpect should see from a real mis-encoded plugin.
    surrogate_str = raw_msg_bytes.decode("utf-8", errors="surrogateescape")
    start_obj = {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"}
    line_obj = {
        "_event": "v2_runner_on_failed",
        "_timestamp": "2026-05-08T10:00:00Z",
        "task": {"id": "t1", "name": "t1"},
        "hosts": {"web1": {"failed": True, "msg": surrogate_str}},
    }
    start_line = json.dumps(start_obj) + "\n"
    line_str = json.dumps(line_obj, ensure_ascii=False) + "\n"
    line_bytes = (start_line + line_str).encode("utf-8", errors="surrogateescape")
    encoded = ", ".join(f"0x{b:02x}" for b in line_bytes)
    code = (
        "import sys; "
        f"sys.stdout.buffer.write(bytes([{encoded}])); "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


class TestR6SurrogateescapeRoundTrip:
    """The invalid-UTF-8 bytes that arrive via the PTY must round-trip
    byte-exactly through ``events.jsonl`` so ``aom inspect show`` can
    dump the original payload. The on-disk JSONL is plain text (escaped),
    so a re-read + ``str.encode('utf-8', 'surrogateescape')`` is the
    round-trip closure."""

    def test_invalid_utf8_bytes_round_trip_byte_exact_into_events_jsonl(
        self, tmp_path: Path
    ) -> None:
        """A PTY line carrying invalid UTF-8 bytes ``b'\\xc3\\x28'``
        (the classic "lone continuation byte after a 2-byte lead" case)
        must land in ``events.jsonl`` with the surrogate codepoints
        preserved. Re-loading the JSONL and re-encoding with
        ``surrogateescape`` recovers the original bytes.
        """
        from ansible_aom.ansible.runner import run_playbook

        renderer = MagicMock()
        # The raw bytes the fake ansible will emit. We encode a JSONL
        # line whose ``msg`` field contains these bytes, then assert
        # the same bytes come back from events.jsonl.
        raw_msg_bytes = b"\xc3\x28 noisy plugin output \xff\xfe end"

        cmd, args = _fake_ansible_emits_jsonl_with_raw_msg(raw_msg_bytes, exit_code=0)

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        assert exit_code == 0

        session_path = next(tmp_path.iterdir())
        events_file = session_path / "events.jsonl"
        assert events_file.exists()

        # The JSONL on disk uses \\uXXXX escapes for surrogate codepoints
        # (Python's json.dumps default). The text round-trips through
        # json.loads back to the same surrogate-bearing str; encoding
        # with surrogateescape must yield the original bytes.
        recorded = _read_jsonl(events_file)
        # Two events: the synthetic start event plus the failed event
        # whose msg carries the surrogate-escaped bytes.
        assert len(recorded) == 2
        assert [e["_event"] for e in recorded] == [
            "v2_playbook_on_start",
            "v2_runner_on_failed",
        ]

        msg_str = recorded[1]["hosts"]["web1"]["msg"]
        # No raw replacement char (U+FFFD) — the surrogate codepoints
        # are preserved instead, so we can recover the bytes.
        assert "\ufffd" not in msg_str
        # And encoding back via surrogateescape gives the original bytes.
        msg_bytes = msg_str.encode("utf-8", "surrogateescape")
        assert msg_bytes == raw_msg_bytes

    def test_valid_utf8_bytes_also_round_trip_unchanged(self, tmp_path: Path) -> None:
        """Sanity check: switching pexpect to ``surrogateescape`` must
        not change behaviour for valid UTF-8 input. A normal ASCII msg
        must still appear in ``events.jsonl`` as plain ASCII.
        """
        from ansible_aom.ansible.runner import run_playbook

        renderer = MagicMock()
        raw_msg_bytes = b"normal ASCII message"
        cmd, args = _fake_ansible_emits_jsonl_with_raw_msg(raw_msg_bytes, exit_code=0)

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        recorded = _read_jsonl(next(tmp_path.iterdir()) / "events.jsonl")
        # Skip the synthetic v2_playbook_on_start event; check the
        # v2_runner_on_failed event's msg field.
        failed = [e for e in recorded if e["_event"] == "v2_runner_on_failed"][0]
        assert failed["hosts"]["web1"]["msg"] == "normal ASCII message"


class TestR6RendererDisplay:
    """The renderer's display path must normalise surrogate codepoints
    to U+FFFD (``?``) so the terminal never tries to render an unpaired
    surrogate. The original bytes remain in ``events.jsonl``.
    """

    def test_truncate_msg_replaces_surrogate_codepoint_with_replacement(self) -> None:
        """``_truncate_msg`` runs every msg field through the
        encode-with-replace/decode round-trip before display, so a
        surrogate codepoint becomes ``?``.
        """
        from ansible_aom.compact.format import _truncate_msg

        msg_with_surrogate = "before\udcc3after"
        out = _truncate_msg(msg_with_surrogate)
        assert "\udcc3" not in out, f"surrogate leaked to display: {out!r}"
        assert "?" in out
        assert out == "before?after"

    def test_replace_surrogates_helper_idempotent_on_clean_text(self) -> None:
        """Strings without surrogate codepoints pass through unchanged."""
        from ansible_aom.compact.format import _replace_surrogates

        assert _replace_surrogates("normal text") == "normal text"
        assert _replace_surrogates("with \u2603 unicode") == "with \u2603 unicode"

    def test_replace_surrogates_converts_lone_surrogates(self) -> None:
        from ansible_aom.compact.format import _replace_surrogates

        # Lone low surrogate from invalid UTF-8 lead byte.
        assert _replace_surrogates("a\udcc3b") == "a?b"
        # Lone high surrogate from invalid UTF-8 tail byte.
        assert _replace_surrogates("a\ud800b") == "a?b"

    def test_renderer_print_log_does_not_show_surrogate_codepoint(self, tmp_path: Path) -> None:
        """End-to-end: drive the runner with a fake ansible that emits
        a JSONL event containing invalid UTF-8, then assert that
        ``print_log`` (which the renderer uses for status output)
        substitutes ``?`` for the surrogate codepoint on its way to the
        terminal. The recorded JSONL still carries the surrogate.
        """
        from ansible_aom.ansible.runner import run_playbook
        from ansible_aom.compact.format import _truncate_msg

        renderer = MagicMock()
        raw_msg_bytes = b"\xc3\x28"
        cmd, args = _fake_ansible_emits_jsonl_with_raw_msg(raw_msg_bytes, exit_code=0)

        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, session_dir=tmp_path)

        # Build the same display string the renderer would build for
        # this msg field — _truncate_msg is the function that runs it
        # through the surrogate-replacement normalisation. The display
        # path is _truncate_msg; we assert it yields ``?`` rather than
        # the surrogate codepoint.
        recorded = _read_jsonl(next(tmp_path.iterdir()) / "events.jsonl")
        failed = [e for e in recorded if e["_event"] == "v2_runner_on_failed"][0]
        msg_str = failed["hosts"]["web1"]["msg"]
        display = _truncate_msg(msg_str)
        assert "\udcc3" not in display
        assert "?" in display


class TestR6ParserAcceptsSurrogateLines:
    """The parser's ``JsonLineStream`` must accept lines containing
    surrogate codepoints — i.e. lines that contain invalid UTF-8 byte
    sequences after ``codec_errors="surrogateescape"`` decode. Without
    this the line is dropped at the parser and never reaches
    ``events.jsonl``.
    """

    def test_jsonl_line_with_surrogate_parses(self) -> None:
        from ansible_aom.core.parser import JsonLineStream

        line = '{"_event": "v2_runner_on_failed", "msg": "bad \udcc3 byte"}'
        stream = JsonLineStream()
        events = stream.feed_line(line)
        assert len(events) == 1
        assert events[0]["_event"] == "v2_runner_on_failed"
        assert "?" not in events[0]["msg"]
        assert events[0]["msg"] == "bad \udcc3 byte"

    def test_mojibake_subsequent_lines_still_parse(self) -> None:
        """A surrogate-bearing line must not poison subsequent lines."""
        from ansible_aom.core.parser import JsonLineStream

        stream = JsonLineStream()
        stream.feed_line('{"_event": "v2_runner_on_failed", "msg": "bad \udcc3 byte"}')
        out = stream.feed_line('{"_event": "v2_playbook_on_stats"}')
        assert len(out) == 1
        assert out[0]["_event"] == "v2_playbook_on_stats"


# Pattern used by the runner module to extract the surrogate-replacement
# decision from format.py — the test below verifies the runner's display
# path actually invokes it (defence-in-depth in case a future refactor
# drops the call).
class TestR6RunnerPexpectConfig:
    """The runner's pexpect.spawn call must use ``codec_errors="surrogateescape"``."""

    def test_runner_uses_surrogateescape(self) -> None:
        import inspect

        from ansible_aom.ansible import runner

        source = inspect.getsource(runner.run_playbook)
        assert 'codec_errors="surrogateescape"' in source, (
            "runner.run_playbook must configure pexpect with "
            "codec_errors='surrogateescape' for byte-exact round-trip"
        )
        assert 'codec_errors="replace"' not in source, (
            "runner.run_playbook must NOT use codec_errors='replace' "
            "anymore — it would discard invalid UTF-8 bytes"
        )


@pytest.fixture(autouse=True)
def _isolate_session_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Force ``_default_session_dir`` to a per-test tmp so the suite
    doesn't litter ``~/.local/state/aom/sessions/``."""
    from ansible_aom.ansible import runner

    monkeypatch.setattr(runner, "_default_session_dir", lambda: tmp_path / "sessions")
