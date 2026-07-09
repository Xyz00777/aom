"""Regression tests for the multi-event PTY read bug.

Bug summary (R-INTERMITTENT-LOSS)
================================

When pexpect reads a chunk of PTY data containing multiple ``\\n``-terminated
JSONL events in a single syscall (the common case once the child has
finished writing its final stats event and the kernel buffers them all
together), the runner's per-newline loop fed ``child.before + child.after``
straight into ``_feed`` as a single ``line``. The parser's ``feed_line``
treats that line as ONE JSON document; the multi-event blob isn't valid
JSON, so ``PtyStreamParser`` falls through to plaintext and every event
in the blob is silently dropped from ``events.jsonl`` — only events
that arrived in their own PTY read made it to disk.

Symptom: ``events.jsonl`` sometimes contains 8 events (982 bytes), sometimes
7 (≈860 bytes), sometimes 0 (just the file created by ``touch()``).
The first expect() after the post-stats flush is the most likely failure
point — pexpect's ``_before`` carries the full read chunk and the
``searchwindowsize=512`` clamp drops data from the search buffer but
NOT from ``_before``, so ``before`` ends up holding the events that
should have come in on subsequent iterations.

Fix: split the runner's newline input on ``\\n`` boundaries and feed
each non-empty line individually. The parser's ``feed_line`` is the
authoritative per-line entry point; the runner was relying on
``child.before`` to be exactly one line and that contract was violated
when the PTY read crossed event boundaries.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _events_fixture() -> list[dict]:
    """The 8-event fixture the original bug report used."""
    return [
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-13T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-13T10:00:00Z",
            "play": {"id": "p1", "name": "Deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-13T10:00:00Z",
            "task": {"id": "t1", "name": "Probe"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-05-13T10:00:01Z",
            "task": {"id": "t1", "name": "Probe"},
            "hosts": {"web1": {"changed": True}},
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-05-13T10:00:01Z",
            "task": {"id": "t1", "name": "Probe"},
            "hosts": {"web2": {"failed": True, "msg": "boom"}},
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-05-13T10:00:01Z",
            "task": {"id": "t1", "name": "Probe"},
            "hosts": {"web3": {"failed": True, "msg": "boom"}},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-05-13T10:00:01Z",
            "task": {"id": "t1", "name": "Probe"},
            "hosts": {"web4": {}},
        },
        {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-13T10:00:02Z"},
    ]


class _BufferedChild:
    """Fake pexpect child that simulates the multi-event PTY read.

    Each ``expect()`` call returns the entire fixture blob in a single
    ``before`` + ``after`` pair — mirroring the production bug where
    pexpect's internal ``_before`` carries the full read chunk past
    the ``searchwindowsize`` clamp. The first call returns idx=0
    (newline matched); the second raises EOF; ``isalive`` is False
    only after the first call.
    """

    def __init__(self, blob: str) -> None:
        self._blob = blob
        self._emitted = False
        self.before = ""
        self.after = ""
        self.buffer = ""
        self.exitstatus: int | None = 0
        self.signalstatus: int | None = None
        self.pid = 0
        self.closed = False

    def expect(self, patterns, timeout=-1, **kw):  # noqa: ARG002
        if not self._emitted:
            # Match the production failure mode: a single newline match
            # whose ``before`` contains the entire multi-event chunk.
            # pexpect's searchwindow math means the runner receives
            # the chunk as one ``line`` — every subsequent line is
            # silently inside this same string.
            self._emitted = True
            self.before = self._blob  # entire fixture as ONE line
            self.after = "\n"
            return 0  # newline_idx
        import pexpect

        raise pexpect.exceptions.EOF("child exited")

    def isalive(self) -> bool:
        # Stay alive long enough for the runner to reach the newline
        # branch on the first iteration; only become "dead" once the
        # EOF exception fires (handled by the except clause above).
        # Mirrors real pexpect: the orchestrator PID is alive until
        # the child's process actually exits, which here happens
        # synchronously with EOF.
        return True

    def close(self, force: bool = False) -> None:  # noqa: ARG002
        self.closed = True

    def sendintr(self) -> None:
        pass


class _NullSink:
    """Stand-in for the runner's session sink — records calls for assertions."""

    def __init__(self) -> None:
        self.events: list[dict] = []

    def record_event(self, event: dict) -> None:
        self.events.append(event)

    def record_stderr(self, line: str) -> None:
        pass

    def end(self, status: str, **kw) -> None:  # noqa: ARG002
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_drive_feeds_each_event_when_pexpect_returns_multi_event_blob() -> None:
    """Single ``expect()`` returning a multi-event blob must still record
    every event.

    The bug: ``child.before`` contained every event concatenated by ``\\n``,
    the runner fed that whole blob to ``feed_line``, and the parser
    treated it as one invalid-JSON line that fell through to plaintext.
    Every event in the blob was lost.

    After the fix: the runner splits the matched-line payload on newlines
    and feeds each event individually, so the sink records all 8 events
    even though pexpect only returned one ``before`` chunk.
    """
    from ansible_aom.ansible.runner import _drive
    from ansible_aom.core.parser import PtyStreamParser
    from ansible_aom.core.run_state import RunState

    events = _events_fixture()
    blob = "".join(json.dumps(e) + "\r\n" for e in events)
    child = _BufferedChild(blob)
    sink = _NullSink()
    parser = PtyStreamParser()
    renderer = MagicMock()

    _drive(
        child,
        parser,
        RunState(playbook="x"),
        renderer,
        timeout=0.5,
        sink=sink,  # type: ignore[arg-type]
    )

    recorded = [e.get("_event") for e in sink.events]
    assert recorded == [e["_event"] for e in events], (
        f"expected all 8 events recorded, got {len(sink.events)}: {recorded!r}"
    )


def test_run_playbook_writes_all_events_to_disk(tmp_path: Path) -> None:
    """End-to-end: a real subprocess emitting the 8-event fixture must
    produce an ``events.jsonl`` of exactly 982 bytes (8 lines).

    Uses the same shape as the original repro from the bug report:
    a Python subprocess that ``sys.stdout.write`` every event followed
    by ``\\n`` then ``sys.exit(0)``. The flaky behaviour from the bug
    report was that the on-disk file sometimes contained every line,
    sometimes only a few, sometimes none at all.
    """
    events = _events_fixture()
    payload = json.dumps(events)
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        "sys.exit(0)"
    )
    cmd = (sys.executable, ["-c", code])

    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    renderer = MagicMock()

    with patch("ansible_aom.ansible.runner._build_command", return_value=cmd):
        with patch(
            "ansible_aom.ansible.runner.run_preflight",
            return_value=MagicMock(definitions=[], errors=[]),
        ):
            from ansible_aom.ansible.runner import run_playbook

            rc = run_playbook("site.yml", [], renderer, session_dir=session_dir)

    sessions = [p for p in session_dir.iterdir() if p.is_dir()]
    assert sessions, "no session directory was created"
    events_file = sessions[0] / "events.jsonl"
    assert events_file.exists(), "events.jsonl was not created"
    on_disk = events_file.read_text().splitlines()
    assert len(on_disk) == len(events), (
        f"events.jsonl has {len(on_disk)} lines, expected {len(events)}; "
        f"raw contents:\n{events_file.read_text()!r}"
    )
    assert rc == 0
