"""Tests for ``RunDiagnostics`` and the runner-side instrumentation.

Phase 3 of docs/superpowers/specs/2026-05-21-diagnostics-layer-design.md.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ansible_aom.core import diagnostics
from ansible_aom.core.parser import PtyStreamParser, StreamPhase


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    yield
    diagnostics._reset_for_testing()


# ---- RunDiagnostics value-object tests ------------------------------------


def test_note_event_increments_counter_and_histogram() -> None:
    diag = diagnostics.RunDiagnostics()
    diag.note_event("v2_runner_on_ok")
    diag.note_event("v2_runner_on_ok")
    diag.note_event("v2_runner_on_failed")
    assert diag.events_received == 3
    assert diag.event_histogram == {"v2_runner_on_ok": 2, "v2_runner_on_failed": 1}


def test_note_event_records_first_event_lifecycle_mark_once() -> None:
    diagnostics.install_from_env(env={"AOM_DEBUG": "1"})
    diag = diagnostics.RunDiagnostics()
    diag.note_event("v2_playbook_on_start")
    diag.note_event("v2_runner_on_ok")
    diag.note_event("v2_playbook_on_stats")
    marks = [name for name, _ in diagnostics.get_lifecycle_marks()]
    assert marks.count("first_event") == 1


def test_note_event_first_event_records_mark_regardless_of_debug() -> None:
    """Lifecycle marks are now always-on (phase 15); the first event mark
    fires without needing AOM_DEBUG. AOM_DEBUG only controls the stderr
    summary, not the marks themselves."""
    diagnostics.install_from_env(env={})
    diag = diagnostics.RunDiagnostics()
    diag.note_event("v2_playbook_on_start")
    marks = [name for name, _ in diagnostics.get_lifecycle_marks()]
    assert marks == ["first_event"]
    assert diag.events_received == 1


def test_note_timeout_increments() -> None:
    diag = diagnostics.RunDiagnostics()
    diag.note_timeout()
    diag.note_timeout()
    diag.note_timeout()
    assert diag.pexpect_timeouts == 3


def test_note_stall_tracks_max() -> None:
    diag = diagnostics.RunDiagnostics()
    diag.note_stall(2)
    diag.note_stall(5)
    diag.note_stall(3)
    diag.note_stall(1)
    assert diag.stall_count_max == 5


def test_note_pty_bytes_accumulates() -> None:
    diag = diagnostics.RunDiagnostics()
    diag.note_pty_bytes(100)
    diag.note_pty_bytes(50)
    diag.note_pty_bytes(7)
    assert diag.pty_bytes == 157


def test_last_run_diagnostics_registry() -> None:
    assert diagnostics.get_last_run_diagnostics() is None
    diag = diagnostics.RunDiagnostics()
    diag.note_event("v2_playbook_on_stats")
    diagnostics.set_last_run_diagnostics(diag)
    fetched = diagnostics.get_last_run_diagnostics()
    assert fetched is diag
    assert fetched.events_received == 1


def test_last_run_diagnostics_cleared_on_reset() -> None:
    diag = diagnostics.RunDiagnostics()
    diagnostics.set_last_run_diagnostics(diag)
    diagnostics._reset_for_testing()
    assert diagnostics.get_last_run_diagnostics() is None


# ---- _feed wiring ---------------------------------------------------------


def _execution_parser() -> PtyStreamParser:
    parser = PtyStreamParser()
    parser.phase = StreamPhase.EXECUTION
    return parser


class _FakeSink:
    def record_event(self, event: dict) -> None: ...
    def record_stderr(self, line: str) -> None: ...
    def end(self, status: str) -> None: ...


def test_feed_with_diag_increments_histogram() -> None:
    from ansible_aom.ansible.runner import _feed
    from ansible_aom.core.run_state import RunState

    renderer = MagicMock()
    parser = _execution_parser()
    state = RunState(playbook="x")
    sink = _FakeSink()
    diag = diagnostics.RunDiagnostics()

    line = (
        '{"_event": "v2_runner_on_ok", "_timestamp": "2026-01-01T00:00:00Z",'
        ' "task": {"id": "t1"}, "hosts": {"web1": {"ok": true}}}\n'
    )

    _feed(line, parser, state, renderer, sink, diag=diag)

    assert diag.events_received == 1
    assert diag.event_histogram == {"v2_runner_on_ok": 1}
    assert diag.pty_bytes == len(line)


def test_feed_without_diag_does_not_crash() -> None:
    """Backwards-compat: existing call sites that don't pass diag still work."""
    from ansible_aom.ansible.runner import _feed
    from ansible_aom.core.run_state import RunState

    renderer = MagicMock()
    parser = PtyStreamParser()
    state = RunState(playbook="x")
    sink = _FakeSink()
    _feed("PLAY [test] *** \n", parser, state, renderer, sink)  # no diag kwarg
    assert renderer.note_pty_bytes.called


# ---- run_playbook lifecycle marks -----------------------------------------


def _fake_ansible_command(events: list[dict], exit_code: int = 0) -> tuple[str, list[str]]:
    import json
    import sys

    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"sys.exit({exit_code})"
    )
    return sys.executable, ["-c", code]


def test_run_playbook_records_lifecycle_marks_with_debug(tmp_path: object) -> None:
    """End-to-end: a real spawn with debug on emits the standard markers."""
    from unittest.mock import patch

    from ansible_aom.ansible.runner import run_playbook

    diagnostics.install_from_env(env={"AOM_DEBUG": "1"})

    renderer = MagicMock()
    cmd, args = _fake_ansible_command(
        [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
        ],
        exit_code=0,
    )

    with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
        run_playbook("playbook.yml", [], renderer, record=False)

    marks = {name for name, _ in diagnostics.get_lifecycle_marks()}
    # The four headline checkpoints must all fire for a successful run.
    assert {"preflight_start", "preflight_end", "spawn", "completion"} <= marks


def test_run_playbook_publishes_last_run_diagnostics() -> None:
    """After a run, get_last_run_diagnostics() exposes the accumulator."""
    from unittest.mock import patch

    from ansible_aom.ansible.runner import run_playbook

    renderer = MagicMock()
    cmd, args = _fake_ansible_command(
        [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
        ],
        exit_code=0,
    )

    with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
        run_playbook("playbook.yml", [], renderer, record=False)

    diag = diagnostics.get_last_run_diagnostics()
    assert diag is not None
    assert diag.events_received >= 2  # start + stats at minimum
    assert "v2_playbook_on_start" in diag.event_histogram
    assert "v2_playbook_on_stats" in diag.event_histogram
