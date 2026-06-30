"""Phase 14/15: every-100th event stderr counter (under AOM_DEBUG).

Logs ``[aom-trace-events] count=N type=…`` every Nth event so users
spotting an event storm don't have to wait for completion. Folded
into ``AOM_DEBUG`` in phase 15 — no separate AOM_TRACE_EVENTS flag.
"""

from __future__ import annotations

import io
import sys
from unittest.mock import MagicMock

import pytest

from ansible_aom.core import diagnostics
from ansible_aom.core.parser import PtyStreamParser, StreamPhase


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    yield
    diagnostics._reset_for_testing()


def _execution_parser() -> PtyStreamParser:
    parser = PtyStreamParser()
    parser.phase = StreamPhase.EXECUTION
    return parser


class _FakeSink:
    def record_event(self, event: dict) -> None: ...
    def record_stderr(self, line: str) -> None: ...
    def end(self, status: str) -> None: ...


_LINE = (
    '{"_event": "v2_runner_on_ok", "_timestamp": "2026-01-01T00:00:00Z",'
    ' "task": {"id": "t1"}, "hosts": {"web1": {"ok": true}}}\n'
)


def _feed_many(n: int, *, diag: diagnostics.RunDiagnostics) -> str:
    from ansible_aom.ansible.runner import _feed
    from ansible_aom.core.run_state import RunState

    renderer = MagicMock()
    parser = _execution_parser()
    state = RunState(playbook="x")
    sink = _FakeSink()
    captured = io.StringIO()
    original = sys.stderr
    sys.stderr = captured
    try:
        for _ in range(n):
            _feed(_LINE, parser, state, renderer, sink, diag=diag)
    finally:
        sys.stderr = original
    return captured.getvalue()


def test_trace_events_silent_when_debug_off() -> None:
    diagnostics.install_from_env(env={})
    diag = diagnostics.RunDiagnostics()
    out = _feed_many(250, diag=diag)
    assert "aom-trace-events" not in out


def test_trace_events_emits_every_100th_event_under_debug() -> None:
    diagnostics.install_from_env(env={"AOM_DEBUG": "1"})
    diag = diagnostics.RunDiagnostics()
    out = _feed_many(250, diag=diag)
    lines = [ln for ln in out.splitlines() if "aom-trace-events" in ln]
    # Events 100 and 200 trip the every-100th gate; 250 does not.
    assert len(lines) == 2
    assert "count=100" in lines[0]
    assert "count=200" in lines[1]
    assert "v2_runner_on_ok" in lines[0]
