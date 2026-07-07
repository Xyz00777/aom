"""Crash-recovery regression tests (Phase 8 / Task 8.2).

What this test pins
-------------------

When a run is interrupted mid-write — power loss, OOM kill, ``SIGKILL`` —
the on-disk session is left in a partially-written state. The most common
shape is:

* ``<session_dir>/<id>/events.jsonl`` exists with some events.
* ``<session_dir>/<id>/meta.json`` is either **missing** (the run died
  before ``end_session`` could rewrite it) or **partially written**
  (truncated JSON).

The replay command is the user-visible read path for that directory. The
contract we want is *degradation, not perfection*: the user should get a
warning and a best-effort replay, not a hard crash. This test proves
that contract.

Test structure
--------------

``TestLoadSessionMissingMeta`` (unit-level) — calls ``load_session``
directly with a session dir that has events but no meta. Asserts:

* It returns a non-None dict (graceful continue).
* It emits ``logger.warning`` mentioning the session id and the missing
  file.
* The events from ``events.jsonl`` are still parsed into
  ``result["events"]``.

``TestReplayContinuesWithMissingMeta`` (driver-level) — drives
``replay_session`` against the same broken session with a mock
renderer. Asserts:

* Exit code 0.
* Every event from the on-disk file was replayed.
* ``handle_completion`` was called.
* A warning was logged on the ``ansible_aom.session.store`` logger.

``TestSubprocessReplayAfterSigkill`` (subprocess-level) — the headline
test. Spawns a real Python subprocess that writes events to disk in a
loop (mimicking a SessionManager-style writer), kills it with
``SIGKILL`` mid-run, then invokes ``aom replay`` as a fresh subprocess
against the partial session. Asserts:

* The replay subprocess exits 0 (continue, not crash).
* Stderr contains a warning about the missing meta.json.
* The event count in the renderer (driven by a re-load of the session)
  is non-zero, i.e. events survived the crash.

Why a real subprocess + SIGKILL (not a unit stub)
------------------------------------------------

A unit stub would prove the code path, but the plan explicitly calls
for "simulate a real crash, not a unit stub" because the original bug
mode is *kernel-level*: the writer thread is killed mid-``fsync``, the
process never runs atexit, and the on-disk files have whatever
buffering state the kernel happened to flush. The subprocess variant
is slow (≈ 1-2 s) but catches regressions where the "graceful" path
quietly depends on something ``atexit`` registered.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers (kept local to the test file per the plan's "if the test needs a
# helper to create an intentionally incomplete session directory, keep it
# local to the test file").
# ---------------------------------------------------------------------------


def _make_partial_session(
    base: Path,
    session_id: str,
    events: list[dict] | None = None,
) -> Path:
    """Create ``base/<session_id>/events.jsonl`` and *deliberately* skip meta.json.

    Mirrors the on-disk state after a crash between
    ``SessionManager.start_session`` (which creates the directory and
    touches ``events.jsonl``) and ``SessionManager.end_session`` (which
    rewrites ``meta.json`` with the final status). ``end_session`` is
    the only call that writes ``meta.json`` for the first time when the
    run completes, so a SIGKILL before it lands leaves a directory
    without ``meta.json`` at all.

    Returns the session directory path.
    """
    if events is None:
        events = [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-07-01T10:00:00Z"},
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-07-01T10:00:00.1Z",
                "play": {"id": "p1", "name": "Crash test"},
            },
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-07-01T10:00:00.2Z",
                "task": {"id": "t1", "name": "Halfway through"},
            },
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-07-01T10:00:01Z",
                "task": {"id": "t1", "name": "Halfway through"},
                "hosts": {"web1": {"changed": False}},
            },
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-07-01T10:00:02Z",
            },
        ]

    session_path = base / session_id
    session_path.mkdir(parents=True)
    events_file = session_path / "events.jsonl"
    with open(events_file, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    # Deliberately do NOT write meta.json.
    return session_path


def _spawn_killed_writer(
    state_dir: Path,
    session_id: str,
    n_events: int = 200,
    sleep_per_event: float = 0.005,
    pre_kill_settle: float = 1.0,
) -> subprocess.CompletedProcess[str]:
    """Spawn a real Python subprocess that writes events, then SIGKILL it.

    The subprocess mimics ``SessionManager.record_event``: it creates
    ``<state_dir>/<session_id>/events.jsonl`` and appends N events with
    a tiny sleep between writes, so a SIGKILL interrupts it mid-loop.

    We pass ``SIGKILL`` (not ``SIGTERM``) because ``SIGTERM`` can be
    trapped by Python and an ``atexit`` handler could write the meta
    file. ``SIGKILL`` is uncatchable — the kernel kills the process
    without running any cleanup, which is the realistic crash mode we
    want to exercise.

    We poll for the writer to create the events file (with at least
    one line) before issuing ``SIGKILL``. Polling is more robust than
    a fixed sleep: on a cold CI runner (or under xdist load) the
    fork + import can take 100-500 ms — a fixed ``time.sleep(0.05)``
    would race. The ``pre_kill_settle`` cap (1 s) keeps the test
    fast on fast machines and the polling loop bounded on slow ones.
    The default 1 s is generous; it covers the worst case observed
    in the v1-verbosity xdist setup where 4 workers each spawn
    several subprocesses.

    Returns the completed process. We don't assert on it directly; the
    caller verifies the on-disk state is partial.
    """
    code = textwrap.dedent(
        f"""
        import json, os, sys, time
        from pathlib import Path

        state_dir = Path({str(state_dir)!r})
        session_id = {session_id!r}
        n = {n_events}
        sleep_s = {sleep_per_event}

        session_path = state_dir / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        events_file = session_path / "events.jsonl"
        events_file.touch()

        # Write events in a loop with a small sleep. A SIGKILL
        # arrives partway through, leaving events.jsonl in a
        # partial state and no meta.json.
        for i in range(n):
            event = {{
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-07-01T10:00:0{{}}Z".format(i),
                "task": {{"id": "t1", "name": "crash test"}},
                "hosts": {{"web{{}}".format(i % 4): {{"changed": False}}}},
            }}
            with open(events_file, "a") as f:
                f.write(json.dumps(event) + "\\n")
            time.sleep(sleep_s)
        # The process is killed before this line normally runs.
        sys.exit(0)
        """
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # Poll until the writer has at least one event on disk, up to
    # ``pre_kill_settle`` seconds. This is far more robust than a
    # fixed sleep on cold CI runners or under xdist contention
    # where the fork + import can take 100-500 ms.
    events_file = state_dir / session_id / "events.jsonl"
    deadline = time.monotonic() + pre_kill_settle
    while time.monotonic() < deadline:
        try:
            if events_file.exists() and events_file.stat().st_size > 0:
                break
        except FileNotFoundError:
            pass
        time.sleep(0.02)
    proc.send_signal(signal.SIGKILL)
    # Reap without blocking forever.
    try:
        stdout, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.wait()
        stdout, stderr = "", ""
    return subprocess.CompletedProcess(
        args=proc.args,
        returncode=proc.returncode,
        stdout=stdout or "",
        stderr=stderr or "",
    )


# ---------------------------------------------------------------------------
# Unit tests — load_session() with missing meta.json
# ---------------------------------------------------------------------------


class TestLoadSessionMissingMeta:
    """``load_session`` degrades gracefully when meta.json is missing."""

    def test_load_session_returns_non_none_for_missing_meta(self, tmp_path: Path) -> None:
        """A directory with only events.jsonl still loads (returns a dict)."""
        from ansible_aom.session.store import load_session

        _make_partial_session(tmp_path, "crash-001")

        session = load_session("crash-001", tmp_path)

        assert session is not None, (
            "load_session must not return None when events.jsonl is recoverable; "
            "missing meta.json should be a warning, not a failure."
        )
        # When meta.json is absent, ``load_session`` returns an empty
        # base dict (no "playbook" / "status" keys at all). Replay and
        # inspect already tolerate absence — see drivers/replay.py for
        # the ``str(session.get("status") or "completed")`` default
        # and inspect/text.py for ``session.get("playbook", "")``.
        assert "playbook" not in session
        assert "status" not in session

    def test_load_session_parses_events_when_meta_missing(self, tmp_path: Path) -> None:
        """Events from events.jsonl are still loaded into the result."""
        from ansible_aom.session.store import load_session

        _make_partial_session(tmp_path, "crash-002")

        session = load_session("crash-002", tmp_path)
        assert session is not None
        assert len(session.get("events", [])) == 5
        assert session["events"][0]["_event"] == "v2_playbook_on_start"
        assert session["events"][-1]["_event"] == "v2_playbook_on_stats"

    def test_load_session_warns_when_meta_missing(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The crash-recovery warning is emitted at WARNING level.

        This is the user-visible contract: a missing meta.json must be
        loud enough that a CI script piping ``aom replay`` output to
        ``jq`` notices. We assert on the *session.store* logger so
        other modules' warnings don't trip the check.
        """
        from ansible_aom.session.store import load_session

        _make_partial_session(tmp_path, "crash-003")

        with caplog.at_level(logging.WARNING, logger="ansible_aom.session.store"):
            session = load_session("crash-003", tmp_path)

        assert session is not None
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert warnings, "expected at least one WARNING record from load_session"
        # The message must mention both the session id and the missing
        # file so users can locate the corrupt session in a directory
        # of dozens.
        msg = warnings[0].getMessage()
        assert "meta.json" in msg, f"warning text should mention meta.json: {msg!r}"
        assert "crash-003" in msg, f"warning text should mention the session id: {msg!r}"


# ---------------------------------------------------------------------------
# Driver-level test — replay_session() with missing meta.json
# ---------------------------------------------------------------------------


class TestReplayContinuesWithMissingMeta:
    """``replay_session`` continues the replay instead of exploding."""

    def test_replay_exits_zero_with_missing_meta(self, tmp_path: Path) -> None:
        """replay_session() returns 0 against a partial session."""
        from ansible_aom.drivers.replay import replay_session

        _make_partial_session(tmp_path, "crash-replay-1")

        renderer = MagicMock()
        exit_code = replay_session(
            session_dir=tmp_path,
            session_id="crash-replay-1",
            renderer=renderer,
            speed=0,  # no sleeps
        )

        assert exit_code == 0, (
            f"replay_session should return 0 even with missing meta.json, "
            f"got {exit_code}; renderer activity: "
            f"start={renderer.start.call_count} "
            f"update_state={renderer.update_state.call_count} "
            f"completion={renderer.handle_completion.call_count}"
        )

    def test_replay_still_drives_renderer_with_missing_meta(self, tmp_path: Path) -> None:
        """Every event on disk reaches the renderer, even with no meta."""
        from ansible_aom.drivers.replay import replay_session

        _make_partial_session(tmp_path, "crash-replay-2")

        renderer = MagicMock()
        replay_session(
            session_dir=tmp_path,
            session_id="crash-replay-2",
            renderer=renderer,
            speed=0,
        )

        # start() was called once with the empty-playbook fallback.
        renderer.start.assert_called_once_with("", [])
        # update_state() called once per event.
        assert renderer.update_state.call_count == 5
        # handle_completion() called once with the (0, "completed")
        # default, since the missing meta → status is empty →
        # "completed" fallback in drivers/replay.py.
        renderer.handle_completion.assert_called_once_with(0, "completed")

    def test_replay_warns_when_meta_missing(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The warning is logged when ``aom replay`` hits a missing meta."""
        from ansible_aom.drivers.replay import replay_session

        _make_partial_session(tmp_path, "crash-replay-3")

        renderer = MagicMock()
        with caplog.at_level(logging.WARNING, logger="ansible_aom.session.store"):
            replay_session(
                session_dir=tmp_path,
                session_id="crash-replay-3",
                renderer=renderer,
                speed=0,
            )

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("meta.json" in r.getMessage() for r in warnings), (
            f"expected a meta.json warning in caplog, got: "
            f"{[r.getMessage() for r in caplog.records]!r}"
        )


# ---------------------------------------------------------------------------
# Subprocess test — the headline SIGKILL-then-replay scenario
# ---------------------------------------------------------------------------


class TestSubprocessReplayAfterSigkill:
    """The headline test: a real subprocess is SIGKILLed mid-write, then
    a fresh ``aom replay`` subprocess replays the partial session.

    The point of using a real subprocess (not ``load_session`` directly)
    is to catch regressions where the "graceful" path depends on
    ``atexit`` handlers or thread-cleanup logic that the unit stub
    doesn't exercise.
    """

    def test_replay_subprocess_survives_sigkill(self, tmp_path: Path) -> None:
        """End-to-end: SIGKILL a writer, replay the partial session.

        Steps:
          1. Spawn a writer subprocess (real Python) that writes events
             to ``<state>/<id>/events.jsonl`` in a loop.
          2. SIGKILL it after ~50ms (kernel-level, uncatchable).
          3. Verify the on-disk state is partial (events present,
             meta.json absent).
          4. Spawn ``aom replay <id> --state-dir <state>`` as a fresh
             subprocess.
          5. Assert it exits 0 and stderr contains a meta.json warning.

        This test is ~ 1-2 s on a typical workstation (mostly the
        SIGKILL wait + the two subprocess spawns). The ``timeout=15``
        argument to ``subprocess.run`` is the real safety net: if the
        replay subprocess ever hangs (regression in graceful-degrade
        path), the test fails with ``TimeoutExpired`` instead of
        hanging the suite.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        session_id = "sigkill-victim"

        # Step 1+2: spawn + SIGKILL.
        killed = _spawn_killed_writer(state_dir, session_id, n_events=400, sleep_per_event=0.005)
        # SIGKILL ⇒ returncode is the negative signal number on POSIX.
        # -9 == SIGKILL. We don't strictly need this assertion — the
        # real contract is on the on-disk state — but a non-SIGKILL
        # exit would mean the writer finished, which means the test
        # wasn't really exercising the crash path.
        if os.name == "posix":
            assert killed.returncode == -9, (
                f"expected SIGKILL (-9) on the writer, got {killed.returncode}; "
                f"the test can't validate crash recovery if the writer finished cleanly"
            )

        # Step 3: verify the on-disk state is partial.
        session_path = state_dir / session_id
        assert session_path.is_dir(), f"writer subprocess did not create {session_path}"
        events_file = session_path / "events.jsonl"
        assert events_file.exists(), f"writer subprocess did not create {events_file}"
        meta_file = session_path / "meta.json"
        assert not meta_file.exists(), f"SIGKILL should leave meta.json absent; found {meta_file}"
        # The writer might have written zero events if SIGKILL landed
        # before the first fsync. We want *some* events to make the
        # replay meaningful; if none made it, skip the replay step.
        on_disk_lines = events_file.read_text().splitlines()
        if not on_disk_lines:
            pytest.skip(
                "writer was killed before any events made it to disk; "
                "this is a timing flake, not a regression"
            )

        # Step 4: spawn aom replay as a fresh subprocess.
        replay = subprocess.run(
            [
                sys.executable,
                "-m",
                "ansible_aom",
                "replay",
                session_id,
                "--state-dir",
                str(state_dir),
                "--speed",
                "0",  # no sleeps; we don't care about timing here
            ],
            capture_output=True,
            text=True,
            timeout=15,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )

        # Step 5: assert the user-visible contract.
        # 5a: replay continues — exit 0, not 1 (session-not-found) and
        # not 130 (KeyboardInterrupt). A SIGKILL-victim session is
        # loadable; the only "error" is the missing meta.
        assert replay.returncode == 0, (
            f"aom replay returned {replay.returncode} on a session that survived "
            f"SIGKILL; expected 0 (graceful continue).\n"
            f"stdout: {replay.stdout!r}\nstderr: {replay.stderr!r}"
        )
        # 5b: a warning surfaces in stderr. The store logger writes
        # via Python's logging module, which by default sends WARNING+
        # to stderr. We look for the substring rather than the exact
        # format string so the test isn't tied to a specific log
        # formatter.
        combined = (replay.stdout + replay.stderr).lower()
        assert "meta.json" in combined, (
            f"expected a meta.json warning in replay output; got:\n"
            f"stdout: {replay.stdout!r}\nstderr: {replay.stderr!r}"
        )
        # 5c: the event stream survived — when we re-load the session
        # in the parent process, events.jsonl still has the same
        # number of lines the writer left behind (no truncation by
        # the replay subprocess, no "directory cleanup" surprise).
        from ansible_aom.session.store import load_session

        session = load_session(session_id, state_dir)
        assert session is not None
        assert len(session.get("events", [])) == len(on_disk_lines), (
            f"event count drift across replay: "
            f"before={len(on_disk_lines)}, after={len(session.get('events', []))}"
        )
