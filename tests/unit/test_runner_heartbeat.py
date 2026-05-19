"""Tests for the runner's heartbeat wiring.

The runner is responsible for feeding three signals to the renderer's
heartbeat:

- ``note_pty_bytes()`` on every PTY line received (newline branch,
  EOF flush, password branch).
- ``reset_heartbeat()`` whenever a ``v2_playbook_on_task_start`` event
  is parsed out, so a stuck indicator from a previous task does not
  bleed into a fresh one.
- ``note_subprocess_active(active)`` on a periodic CPU sample
  (helper ``_sample_subprocess_active``); the helper itself returns
  False gracefully when psutil cannot inspect the pid (e.g. the
  child has exited or never existed).

See ``docs/superpowers/specs/2026-05-19-liveness-indicator-design.md``.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.core.parser import PtyStreamParser, StreamPhase
from ansible_aom.runner import _feed, _sample_subprocess_active


def _parser_in_execution_phase() -> PtyStreamParser:
    """Return a parser advanced past the PRE_RUN_PROMPTS gate.

    ``feed_line`` only emits events once the stream has seen the
    initial ``v2_playbook_on_start``; for unit tests it's simpler to
    poke the phase directly than to feed a real start event first.
    """
    parser = PtyStreamParser()
    parser.phase = StreamPhase.EXECUTION
    return parser


class _FakeSink:
    def __init__(self) -> None:
        self.events: list[dict] = []
        self.stderr: list[str] = []

    def record_event(self, event: dict) -> None:
        self.events.append(event)

    def record_stderr(self, line: str) -> None:
        self.stderr.append(line)

    def end(self, status: str) -> None: ...


class TestFeedNotesBytes:
    """Every successful line fed to ``_feed`` bumps the heartbeat."""

    def test_plaintext_line_notes_pty_bytes(self) -> None:
        renderer = MagicMock()
        parser = PtyStreamParser()
        sink = _FakeSink()

        _feed("PLAY [test] *** \n", parser, renderer, sink)

        assert renderer.note_pty_bytes.called

    def test_jsonl_event_line_notes_pty_bytes(self) -> None:
        renderer = MagicMock()
        parser = _parser_in_execution_phase()
        sink = _FakeSink()
        # Minimal JSONL event line.
        event_line = (
            '{"_event": "v2_runner_on_ok", "_timestamp": "2026-01-01T00:00:00Z",'
            ' "task": {"id": "t1"}, "hosts": {"web1": {"ok": true}}}\n'
        )

        _feed(event_line, parser, renderer, sink)

        assert renderer.note_pty_bytes.called
        assert renderer.update_state.called


class TestTaskStartResetsHeartbeat:
    """A task-start event drops any prior stuck signal for the new task."""

    def test_task_start_event_calls_reset_heartbeat(self) -> None:
        renderer = MagicMock()
        parser = _parser_in_execution_phase()
        sink = _FakeSink()
        event_line = (
            '{"_event": "v2_playbook_on_task_start",'
            ' "_timestamp": "2026-01-01T00:00:01Z",'
            ' "task": {"id": "t2", "name": "Install brew formulae"}}\n'
        )

        _feed(event_line, parser, renderer, sink)

        assert renderer.reset_heartbeat.called

    def test_non_task_start_event_does_not_reset(self) -> None:
        renderer = MagicMock()
        parser = _parser_in_execution_phase()
        sink = _FakeSink()
        event_line = (
            '{"_event": "v2_runner_on_ok", "_timestamp": "2026-01-01T00:00:00Z",'
            ' "task": {"id": "t1"}, "hosts": {"web1": {"ok": true}}}\n'
        )

        _feed(event_line, parser, renderer, sink)

        assert not renderer.reset_heartbeat.called


class TestSampleSubprocessActive:
    """The CPU sampler degrades gracefully and never raises."""

    def test_returns_false_for_nonexistent_pid(self) -> None:
        # A pid that almost certainly doesn't exist: 2^31-1.
        active = _sample_subprocess_active(2**31 - 1)
        assert active is False

    def test_returns_bool_for_own_pid(self) -> None:
        import os

        active = _sample_subprocess_active(os.getpid())
        # We can't assert True/False (depends on scheduling), but the
        # call must succeed and return a bool.
        assert isinstance(active, bool)
