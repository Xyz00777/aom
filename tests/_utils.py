"""Shared test utilities.

Helpers that are useful across multiple test modules but don't belong
in any production package. Currently:

* ``normalize_render_output`` — strip timestamps, elapsed-time tokens,
  and ANSI cursor-position sequences so live and replay outputs can
  be compared byte-for-byte.
"""

from __future__ import annotations

import json
import re

# ISO 8601 timestamps emitted by ansible (e.g. ``2026-05-13T22:19:21.609416Z``
# or ``2026-05-13T22:19:21+00:00``). Match optional fractional seconds
# and either a literal ``Z`` or numeric offset suffix.
_ISO_TIMESTAMP_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})"
)

# Wall-clock prefixes the renderer prints at the head of post-task log
# lines: ``[HH:MM:SS]``.
_CLOCK_BRACKET_RE = re.compile(r"\[\d{2}:\d{2}:\d{2}\]")

# Elapsed-time tokens — variable on every run: ``0.0s``, ``1.6s``,
# ``12.4s``, ``1m04s``, ``0:00:01``, ``cum -2031967.8s`` (yes, that's
# real: when start_time isn't set the cumulative goes wildly negative).
_ELAPSED_RE = re.compile(r"\b\d+m\d{1,2}s\b|\b-?\d+(?:\.\d+)?s\b|\b\d+:\d{2}:\d{2}\b")

# ANSI cursor-position / movement sequences: CSI followed by digits/;
# and a terminator in {H, f, A, B, C, D}. We do NOT strip SGR (the
# ``m`` terminator) because colour codes are part of the rendered
# output we want to preserve.
_ANSI_CURSOR_RE = re.compile(r"\x1b\[[0-9;]*[HfABCD]")

# Cursor save/restore and DEC modes (e.g. ``\x1b[?2026h`` /
# ``\x1b[?2026l`` — synchronized output) — these vary purely with
# frame timing in the live render path; the replay-render path that
# operates on a different cadence emits them in a different
# distribution. Strip so a transient difference in panel-flush
# rhythm doesn't fail an otherwise byte-identical comparison.
_ANSI_DEC_MODE_RE = re.compile(r"\x1b\[\?[0-9;]+[hl]")
_ANSI_ERASE_RE = re.compile(r"\x1b\[[0-9;]*[JK]")


def normalize_render_output(text: str) -> str:
    """Return ``text`` with run-specific tokens stripped.

    Strips: ISO 8601 timestamps, ``[HH:MM:SS]`` clock brackets,
    elapsed-time tokens (``1.6s``, ``1m04s``, ``0:00:01``), ANSI
    cursor-position / erase / DEC-mode sequences. SGR colour codes
    are deliberately preserved.

    The aggressive stripping is intentional: live and replay drive
    the renderer through different code paths (pexpect newline-by-
    newline vs replay's tight loop) so frame-by-frame ANSI output
    diverges even when the logical content matches.
    """
    text = _ANSI_DEC_MODE_RE.sub("", text)
    text = _ANSI_CURSOR_RE.sub("", text)
    text = _ANSI_ERASE_RE.sub("", text)
    text = _ISO_TIMESTAMP_RE.sub("<TS>", text)
    text = _CLOCK_BRACKET_RE.sub("[<TIME>]", text)
    text = _ELAPSED_RE.sub("<DUR>", text)
    return text


def normalize_json_summary(text: str) -> str:
    """Normalise the ``RunSummary`` JSON line by zeroing run-specific fields.

    JsonRenderer emits a single JSON line on completion with
    ``started_at`` / ``ended_at`` / ``duration_s`` fields that
    legitimately differ between a live run and a replay (the replay
    starts wall-clock later). Replace those fields with constants so
    the rest of the payload (hosts, exit_code, tasks_failed) can be
    compared byte-for-byte.

    Returns the text unchanged when no JSON object is present.
    """
    line = text.strip()
    if not line.startswith("{"):
        return text
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return text
    for key in ("started_at", "ended_at"):
        if key in payload:
            payload[key] = "<TS>"
    if "duration_s" in payload:
        payload["duration_s"] = 0.0
    return json.dumps(payload, sort_keys=True)
