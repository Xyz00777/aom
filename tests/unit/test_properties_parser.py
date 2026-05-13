"""Property-based tests for the JSONL parser (Batch C, family #5a).

These tests assert two invariants that complement the example-based suite:

1. Arbitrary input (bytes decoded loosely to str, or arbitrary unicode) fed
   to :class:`JsonLineStream` and :class:`PtyStreamParser` never raises an
   uncaught exception. Real PTY streams can interleave colour escapes,
   half-written lines, and binary noise on broken hosts.

2. When valid JSONL events are interleaved with arbitrary garbage between
   them, every well-formed event still appears in the parser's drain
   output. The parser is allowed to skip garbage; it must never drop a
   well-formed event from a line of its own.

We use :mod:`hypothesis` to drive both invariants. Examples are capped to
keep the full suite under the CI budget.
"""

from __future__ import annotations

import json

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from ansible_aom.core.parser import JsonLineStream, PtyStreamParser

# --------------------------------------------------------------------------- #
# Strategies                                                                  #
# --------------------------------------------------------------------------- #

# Plausible event archetypes drawn from core/models.RunState.handle_event.
_EVENT_TYPES = (
    "v2_playbook_on_start",
    "v2_playbook_on_play_start",
    "v2_playbook_on_task_start",
    "v2_runner_on_ok",
    "v2_runner_on_failed",
    "v2_runner_on_unreachable",
    "v2_runner_on_skipped",
    "v2_playbook_on_stats",
)


def _hostname_strategy() -> st.SearchStrategy[str]:
    return st.text(
        alphabet=st.characters(min_codepoint=ord("a"), max_codepoint=ord("z")),
        min_size=1,
        max_size=12,
    )


def _identifier_strategy() -> st.SearchStrategy[str]:
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("Ll", "Lu", "Nd"),
            whitelist_characters="-_",
        ),
        min_size=1,
        max_size=16,
    )


@st.composite
def valid_event_dicts(draw: st.DrawFn) -> dict:
    """Build a realistic, JSON-encodable ansible event dict."""
    event_type = draw(st.sampled_from(_EVENT_TYPES))
    event: dict = {"_event": event_type, "_timestamp": "2026-01-01T00:00:00Z"}
    task_id = draw(_identifier_strategy())
    play_id = draw(_identifier_strategy())
    task_name = draw(st.text(min_size=0, max_size=20))
    play_name = draw(st.text(min_size=0, max_size=20))

    if event_type in ("v2_playbook_on_play_start",):
        event["play"] = {"id": play_id, "name": play_name}
    elif event_type == "v2_playbook_on_task_start":
        event["play"] = {"id": play_id, "name": play_name}
        event["task"] = {"id": task_id, "name": task_name}
    elif event_type in (
        "v2_runner_on_ok",
        "v2_runner_on_failed",
        "v2_runner_on_unreachable",
        "v2_runner_on_skipped",
    ):
        event["play"] = {"id": play_id, "name": play_name}
        event["task"] = {"id": task_id, "name": task_name}
        host = draw(_hostname_strategy())
        event["hosts"] = {host: {"changed": draw(st.booleans())}}
    elif event_type == "v2_playbook_on_stats":
        host = draw(_hostname_strategy())
        event["stats"] = {host: {"ok": 1, "failures": 0, "unreachable": 0}}

    return event


def _encode_event_line(event: dict) -> str:
    """Encode an event dict as a single JSONL line (no trailing newline)."""
    return json.dumps(event)


# Arbitrary noise that is unlikely to coincidentally form valid JSON with
# an "_event" key. The parser's `feed_line` is line-oriented and takes
# `str`, so we model byte-level noise via `text()` here.
_garbage_text = st.text(max_size=200)


# --------------------------------------------------------------------------- #
# Invariant 1: never crash                                                    #
# --------------------------------------------------------------------------- #


@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(blob=st.binary(max_size=4096))
def test_jsonline_stream_never_crashes_on_arbitrary_bytes(blob: bytes) -> None:
    """Arbitrary bytes (decoded loosely) never raise from JsonLineStream.feed_line."""
    text = blob.decode("utf-8", errors="replace")
    parser = JsonLineStream()
    for line in text.splitlines():
        # Must not raise. Return value is allowed to be anything.
        parser.feed_line(line)


@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(blob=st.binary(max_size=4096))
def test_pty_stream_parser_never_crashes_on_arbitrary_bytes(blob: bytes) -> None:
    """Arbitrary bytes (decoded loosely) never raise from PtyStreamParser.feed_line."""
    text = blob.decode("utf-8", errors="replace")
    parser = PtyStreamParser()
    for line in text.splitlines():
        parser.feed_line(line)


# --------------------------------------------------------------------------- #
# Invariant 2: valid events survive garbage interleaving                      #
# --------------------------------------------------------------------------- #


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    events=st.lists(valid_event_dicts(), min_size=1, max_size=12),
    garbage=st.lists(_garbage_text, max_size=12),
)
def test_valid_events_survive_garbage_interleaving(
    events: list[dict], garbage: list[str]
) -> None:
    """Well-formed events interleaved with arbitrary noise still drain in order.

    The parser may emit garbage lines via the non-JSON handler or drop them;
    what it must never do is fail to deliver a syntactically valid JSON line
    that carried an ``_event`` field.
    """
    # Filter garbage that could itself parse as a valid event-shaped JSON
    # object — that would inflate our expected count.
    safe_garbage: list[str] = []
    for g in garbage:
        g_stripped = g.strip()
        if not g_stripped or not g_stripped.startswith("{"):
            safe_garbage.append(g)
            continue
        try:
            obj = json.loads(g_stripped)
        except (json.JSONDecodeError, ValueError):
            safe_garbage.append(g)
            continue
        if isinstance(obj, dict) and "_event" in obj:
            # Skip — could be confused with a real event.
            continue
        safe_garbage.append(g)

    # Garbage lines must not themselves contain embedded newlines that
    # would split them into multiple lines (we feed line-by-line).
    safe_garbage = [g.replace("\n", " ").replace("\r", " ") for g in safe_garbage]

    encoded_events = [_encode_event_line(e) for e in events]
    # Interleave: alternate events and garbage, then strip empty.
    interleaved: list[str] = []
    g_iter = iter(safe_garbage)
    for ev_line in encoded_events:
        try:
            interleaved.append(next(g_iter))
        except StopIteration:
            pass
        interleaved.append(ev_line)
    interleaved.extend(g_iter)

    parser = JsonLineStream()
    collected: list[dict] = []
    for line in interleaved:
        collected.extend(parser.feed_line(line))

    # Every event we encoded as a clean JSON line must appear in the output
    # in the same order. Compare by JSON-canonical form to ignore dict
    # ordering nuances.
    assume(len(events) == len(encoded_events))
    canonical_in = [json.dumps(e, sort_keys=True) for e in events]
    canonical_out = [json.dumps(e, sort_keys=True) for e in collected]
    # The parser may emit additional events if a piece of "garbage" happened
    # to be valid JSON with an _event field after our filter — but our
    # filter excludes that. So the output should equal the input exactly.
    assert canonical_out == canonical_in
