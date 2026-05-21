"""TC-PERF-005..007 — orjson swap equivalency tests.

Pin behaviour of ``JsonLineStream.feed_line`` after the stdlib-json →
orjson swap. orjson must produce identical dicts to stdlib for every
fixture event, must still stash partials in the carry buffer when a
truncated JSON line arrives, and must still reject JSON top-level
values that are not objects.
"""

from __future__ import annotations

import json as stdlib_json
from pathlib import Path

import pytest

from ansible_aom.core.parser import JsonLineStream

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
JSONL_FIXTURES = sorted(FIXTURES_DIR.glob("*.jsonl"))


@pytest.mark.parametrize(
    "fixture_path",
    JSONL_FIXTURES,
    ids=[p.name for p in JSONL_FIXTURES],
)
def test_perf_005_parser_byte_equal_to_stdlib(fixture_path: Path) -> None:
    """TC-PERF-005: orjson swap is byte-equivalent for real-world fixtures."""
    stream = JsonLineStream()
    parsed: list[dict] = []
    reference: list[dict] = []

    with fixture_path.open() as f:
        for line in f:
            for event in stream.feed_line(line):
                parsed.append(event)
            line_stripped = line.strip()
            if line_stripped.startswith("{"):
                try:
                    ref = stdlib_json.loads(line_stripped)
                except stdlib_json.JSONDecodeError:
                    continue
                if isinstance(ref, dict) and "_event" in ref:
                    reference.append(ref)

    assert parsed == reference


def test_perf_006_carry_buffer_still_works_after_swap() -> None:
    """TC-PERF-006: truncated JSON head is stashed and re-joined.

    Equivalent behaviour to the pre-swap parser — orjson's decode error
    must still flow through the carry buffer path.
    """
    stream = JsonLineStream()
    head = '{"_event":"x","msg":"hel'
    tail = 'lo"}'

    assert stream.feed_line(head) == []
    assert stream._carry == head

    events = stream.feed_line(tail)
    assert len(events) == 1
    assert events[0]["_event"] == "x"
    assert events[0]["msg"] == "hello"
    assert stream._carry == ""


def test_perf_007_non_dict_json_rejected() -> None:
    """TC-PERF-007: top-level JSON that's not an object is rejected.

    A JSON top-level number/array/string is not an event. The parser
    must not yield it as if it were. orjson is stricter than stdlib in
    some edge cases — this test pins the contract.
    """
    stream = JsonLineStream()

    # Non-dict JSON should never produce an event. ``"42"`` does not
    # start with ``{`` so it never even enters the JSON path.
    assert stream.feed_line('"42"') == []

    # A JSON array also doesn't start with ``{`` — rejected at the
    # gate-keeper check.
    assert stream.feed_line("[1,2,3]") == []

    # A valid JSON object without ``_event`` is rejected as before.
    assert stream.feed_line('{"foo":"bar"}') == []
