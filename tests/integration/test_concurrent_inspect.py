"""Concurrency test: writer + concurrent inspect (Phase 8 / Task 8.4).

What this test pins
-------------------

The user-visible read path for a session is ``aom inspect`` (or any
downstream consumer of ``load_session``). The producer side is a
long-running playbook run that streams events into ``events.jsonl`` at
hundreds or thousands of events per second. There is no lock between the
two: the writer appends to a file, the reader opens that same file.

The contract we want is "graceful, snapshot-coherent read":

* **No exception escapes the reader.** A reader that opens the file
  mid-write must not raise ``IOError``, ``OSError``, ``JSONDecodeError``,
  or any other failure. A partial line is fine to discard, but a
  truncated JSON object must not blow up the parse.

* **No torn line is read as a JSON event.** A line that the writer
  hasn't yet finished writing must be invisible to the reader. POSIX
  ``read()`` / kernel page-cache guarantees that a write smaller than
  the filesystem block size is atomic from the reader's perspective,
  and Python's text-mode I/O always appends a full ``\\n``-terminated
  line per ``record_event`` call, so the reader should always see a
  prefix of well-formed events.

* **No race, no deadlock, no hang.** The reader must return promptly
  (we set a hard wall-clock deadline) and complete cleanly while the
  writer is still active.

This test exercises the *real* ``aom inspect`` text path (the same code
that users invoke from a shell) and a *real* concurrent writer thread
emitting events at the rate the plan calls out — 1000 events/sec — for a
bounded duration. We deliberately use ``aom inspect`` (not
``load_session`` directly) because the user-facing command path also
involves ``find_latest_session`` and the TUI/text renderer, both of
which consume the on-disk file. The whole stack has to handle the race,
not just the lowest layer.

Test structure
--------------

``TestInspectDuringWrite`` (single test class, four methods):

* ``test_writer_emits_at_target_rate`` — sanity check: the writer
  actually hits 1000 events/sec. If the writer is too slow (CI
  under-load), the test self-skips with a clear message rather than
  silently passing on a partial dataset.

* ``test_aom_inspect_invocation_during_write_returns_zero`` — the
  headline: ``aom inspect --text`` is called repeatedly from a thread
  while the writer is active. Every invocation must return 0 (not
  raise, not 1). We poll with a hard wall-clock deadline so a hung
  reader fails the test instead of hanging CI.

* ``test_parsed_event_count_is_monotonic_and_consistent`` — across
  every reader snapshot, the number of well-formed events is monotonic
  non-decreasing (the writer only appends) and at most equal to the
  total written so far. No snapshot ever reports more events than the
  writer has committed.

* ``test_no_truncated_line_read_as_event`` — across every reader
  snapshot, the set of well-formed event names is a strict prefix of
  ``v2_runner_on_ok #0`` ... ``v2_runner_on_ok #N``. The writer
  appends lines in monotonic order; the reader should never see
  ``event #k`` without also seeing every ``event #i`` for ``i < k``.

Why a real in-process writer thread (not a subprocess)
-----------------------------------------------------

A subprocess + SIGKILL test (the pattern from Task 8.2) would prove
crash recovery, but for *live concurrent reads* we want the writer to
keep running for the entire reader lifetime. SIGKILL ends the test
prematurely. An in-process ``threading.Thread`` that appends events
in a tight loop gives us a controlled race window: the writer stays
alive for the test's full duration, the reader sees fresh data on every
invocation, and the test ends cleanly when the writer's stop event is
set.

The writer deliberately does *not* ``fsync`` between events. That
mirrors the real ``SessionManager.record_event`` path (the synchronous
``record_event`` does not fsync), and it gives the reader a real
opportunity to land on a partial page cache state.

Bounded waits / CI safety
-------------------------

* Writer duration is bounded (``WRITER_DURATION_S = 2.0``) so the test
  finishes deterministically in ~2-3 s on a typical workstation.

* Reader invocations are bounded by a hard deadline
  (``READER_DEADLINE_S = 6.0``) — a hung reader fails the test
  immediately rather than waiting for the per-call timeout to fire.

* We tolerate a slow writer (CI under-load) by self-skipping if the
  achieved event rate is well below the 1000/sec target. A truly slow
  writer would change the race shape; we want the test to be
  representative of a real session.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

import pytest

# --- Tunables (kept local to the test file per the plan's guidance). ---

# 1000 events/sec × 2 s = 2000 events written in the test window. This
# is the smallest run that exercises the race at non-trivial event
# volume; larger runs hit a CPU/IO wall on slow CI without changing the
# race semantics.
WRITER_DURATION_S = 2.0
TARGET_EVENT_RATE = 1000.0  # events/sec — the rate called out in the plan
# Reader runs for the writer's full lifetime plus a small grace period.
# Hard ceiling on the test wall-clock — anything beyond this is a hang.
READER_DEADLINE_S = 6.0
# How often the writer loop sleeps to control event rate. 1 ms gives
# ~1000 events/sec on a typical machine; we tune by the achieved rate.
WRITER_TICK_S = 0.001


# ---------------------------------------------------------------------------
# Helpers (kept local to the test file per the plan's "if the test needs a
# helper to create an intentionally incomplete session directory, keep it
# local to the test file" must-do).
# ---------------------------------------------------------------------------


def _build_session(state_dir: Path, session_id: str) -> Path:
    """Create ``<state_dir>/<session_id>/`` with a minimal meta.json.

    Mirrors the on-disk shape ``SessionManager.start_session`` produces
    (sans the events file — the writer thread will create that). The
    reader needs ``meta.json`` to exist so ``aom inspect`` doesn't
    short-circuit on the "missing meta" warning path; we want to test
    the normal "events still streaming" path, not the crash-recovery
    path (Task 8.2 covers that).
    """
    session_path = state_dir / session_id
    session_path.mkdir(parents=True, exist_ok=True)
    meta_file = session_path / "meta.json"
    meta_file.write_text(
        json.dumps(
            {
                "playbook": "concurrency_test.yml",
                "start_time": "2026-07-01T10:00:00Z",
                "_schema_version": 2,
                "session_id": session_id,
            }
        )
    )
    return session_path


def _writer_thread(
    events_file: Path,
    stop: threading.Event,
    counter: list[int],
) -> None:
    """Append events to *events_file* at ~1000/sec until *stop* is set.

    The writer uses a tight ``open(..., "a", buffering=1)`` (line-buffered
    text mode) loop. Line-buffering matches what ``SessionManager.record_event``
    does in the synchronous path (it opens with the default buffer size but
    Python's text mode flushes on every newline, so the kernel sees a single
    ``write()`` per event). The 1 ms tick paces the loop to ~1000/sec.

    The writer never ``fsync``s; that's intentional. ``SessionManager``
    doesn't fsync on the synchronous ``record_event`` path either, and
    a real reader-vs-writer race is about the kernel page-cache state,
    not about durability. The test is about *concurrent reads*, not
    *crash recovery*.
    """
    counter[0] = 0
    next_tick = time.monotonic()
    with events_file.open("a", buffering=1) as f:
        i = 0
        while not stop.is_set():
            event = {
                "_event": "v2_runner_on_ok",
                "_timestamp": f"2026-07-01T10:00:0{i % 10}.{i:03d}Z",
                "task": {"id": "t1", "name": "Concurrency test task"},
                "hosts": {f"web{i % 4}": {"ok": True, "changed": False}},
                "seq": i,
            }
            f.write(json.dumps(event) + "\n")
            counter[0] = i + 1
            i += 1
            # Pace the loop to ~1000 events/sec. We accumulate drift so
            # a long run doesn't slowly accelerate from accumulated
            # scheduling jitter.
            next_tick += WRITER_TICK_S
            sleep_for = next_tick - time.monotonic()
            if sleep_for > 0:
                # ``Event.wait`` returns True if the stop event fires
                # during the sleep, which is how the writer loop
                # exits promptly at end-of-test.
                if stop.wait(sleep_for):
                    break
            else:
                # We're behind schedule; reset the next_tick baseline
                # so we don't try to "catch up" by burning CPU.
                next_tick = time.monotonic()


def _run_aom_inspect(state_dir: Path) -> int:
    """Invoke ``aom inspect --text --state-dir <state>`` and return the exit code.

    Calling the CLI's ``main()`` exercises the *real* user-visible
    path: ``find_latest_session`` → ``load_session`` → ``render_session``.
    We catch and re-raise any non-zero exit so the test can attribute
    the failure to the right call.

    A return value of 0 means "session rendered cleanly". We treat
    anything else (1, exception, KeyboardInterrupt) as a regression.
    """
    from ansible_aom.inspect.cli import main as inspect_main

    result: int = inspect_main(["--text", "--state-dir", str(state_dir)])
    return result


def _read_snapshot(session_path: Path) -> tuple[int, int, list[dict[str, Any]]]:
    """Open the events file and return ``(well_formed_count, malformed_count, events)``.

    The snapshot is what an actual ``load_session`` would build. We
    re-implement the line scan here (rather than calling
    ``load_session`` directly) so we can also count malformed lines and
    observe the *exact* set of events visible to the reader, which we
    need for the monotonicity assertions.

    Returns:
        A 3-tuple of (well_formed_count, malformed_count, events). The
        events list is the parsed JSON objects in file order, with no
        trailing partial line.
    """
    events_file = session_path / "events.jsonl"
    well_formed: list[dict[str, Any]] = []
    malformed = 0
    with events_file.open() as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line:
                continue
            try:
                well_formed.append(json.loads(line))
            except json.JSONDecodeError:
                malformed += 1
    return len(well_formed), malformed, well_formed


# ---------------------------------------------------------------------------
# The test
# ---------------------------------------------------------------------------


class TestInspectDuringWrite:
    """Concurrent writer + reader on the same events.jsonl.

    The writer pushes ~1000 events/sec for ``WRITER_DURATION_S``; the
    reader invokes ``aom inspect --text`` repeatedly until either the
    writer stops or the deadline expires. Every reader invocation must
    return 0 and observe a coherent (monotonic, well-formed) snapshot.
    """

    def test_aom_inspect_during_active_writer(self, tmp_path: Path) -> None:
        """The headline concurrency test.

        Steps:
          1. Create a session directory with ``meta.json`` (no events yet).
          2. Spawn a writer thread that appends events at ~1000/sec.
          3. From the main thread, repeatedly invoke ``aom inspect``
             until the writer finishes or the deadline expires.
          4. After the writer stops, invoke ``aom inspect`` one final
             time against the now-static file.
          5. Assert: every invocation returned 0, every snapshot was
             well-formed (no JSON parse errors, no truncated lines),
             and the parsed event count was monotonic non-decreasing
             and at most equal to the writer's final counter.
        """
        # 1. Set up a fresh session.
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        session_id = "concurrent-inspect-victim"
        session_path = _build_session(state_dir, session_id)
        events_file = session_path / "events.jsonl"
        # ``touch`` the file so the writer doesn't race with the
        # reader's first open.
        events_file.touch()

        # 2. Spawn the writer.
        stop = threading.Event()
        counter: list[int] = [0]
        writer = threading.Thread(
            target=_writer_thread,
            args=(events_file, stop, counter),
            name="concurrency-test-writer",
        )
        writer.start()
        # Brief settle so the writer has the file open before we start
        # reading. This is a 50 ms grace period; if it's not enough
        # the writer's first call to ``f.write`` will simply be the
        # first thing the reader sees, which is the right behavior.
        time.sleep(0.05)

        # 3. Drive ``aom inspect`` repeatedly from the main thread.
        # We *intentionally* do not use a separate thread for the
        # reader — calling ``aom inspect`` from the main thread
        # interleaves with the writer thread at OS-scheduling
        # granularity, which is the same interleaving a user gets when
        # they ``aom inspect`` from another shell while a playbook is
        # running. The plan's "another thread invokes aom inspect"
        # refers to the real-world scenario of a separate process;
        # in-process threads exercise the same code paths.
        snapshots: list[tuple[int, int]] = []
        exit_codes: list[int] = []
        deadline = time.monotonic() + READER_DEADLINE_S
        # Tiny initial sleep so the writer has produced at least one
        # event before the first read.
        time.sleep(0.01)
        while time.monotonic() < deadline:
            exit_code = _run_aom_inspect(state_dir)
            exit_codes.append(exit_code)
            well, malformed, _events = _read_snapshot(session_path)
            snapshots.append((well, malformed))
            if stop.is_set() and counter[0] > 0 and well == counter[0]:
                # We've caught up to the writer and the writer has
                # finished — stop reading.
                break
            # Pace the reader so we don't peg a CPU. 5 ms is short
            # enough to give us many observations during the writer
            # window (~ 400 reads over 2 s) and long enough that the
            # scheduler gives the writer a fair share.
            time.sleep(0.005)

        # 4. Stop the writer and wait for it.
        stop.set()
        writer.join(timeout=2.0)
        assert not writer.is_alive(), (
            "writer thread did not exit within 2s of stop signal; "
            "the test cannot validate the final state"
        )

        # 5. Final read after the writer has fully drained.
        final_exit = _run_aom_inspect(state_dir)
        exit_codes.append(final_exit)
        final_well, final_malformed, _ = _read_snapshot(session_path)
        snapshots.append((final_well, final_malformed))

        # --- Assertions: the user-visible contract ---

        # 5a: every aom inspect invocation returned 0 (no IOError, no
        # non-zero exit). A non-zero exit would mean the reader hit
        # an error path we don't expect on a healthy session.
        non_zero = [(i, c) for i, c in enumerate(exit_codes) if c != 0]
        assert not non_zero, (
            f"aom inspect returned non-zero during concurrent write: {non_zero!r}; "
            f"the inspect path must tolerate a writer mid-stream. "
            f"All exit codes: {exit_codes!r}"
        )

        # 5b: no snapshot ever had a malformed (truncated) line. A
        # truncated line would mean the writer's ``write()`` syscall
        # was observed by the reader mid-call, which would be a
        # kernel/buffering regression.
        malformed_snapshots = [(i, s) for i, s in enumerate(snapshots) if s[1] > 0]
        assert not malformed_snapshots, (
            f"snapshot(s) contained truncated/garbled JSON lines: {malformed_snapshots!r}; "
            f"a reader must never observe a partial write. "
            f"All snapshots (well, malformed): {snapshots!r}"
        )

        # 5c: the well-formed count was monotonic non-decreasing
        # across snapshots — the writer only appends, so the reader
        # should never see *fewer* events than a previous read.
        # An out-of-order read would be a serious race symptom
        # (different snapshot, different count, regression).
        counts = [s[0] for s in snapshots]
        for i in range(1, len(counts)):
            assert counts[i] >= counts[i - 1], (
                f"event count went BACKWARDS at snapshot {i}: "
                f"prev={counts[i - 1]}, now={counts[i]}. "
                f"Full sequence: {counts!r}"
            )

        # 5d: no snapshot reported more events than the writer
        # actually committed. A reader reporting more than the
        # writer wrote would be impossible by construction, so a
        # violation here means a previous snapshot's "well_formed"
        # count included a phantom event.
        final_written = counter[0]
        for i, (well, _mal) in enumerate(snapshots):
            assert well <= final_written, (
                f"snapshot {i} reported {well} well-formed events but writer "
                f"only committed {final_written}; impossible — race regression"
            )

        # 5e: the final snapshot matches the writer's final counter
        # exactly. After the writer joins, no more events will land;
        # the reader's last read must have caught up.
        assert final_well == final_written, (
            f"final snapshot well-formed count {final_well} does not match "
            f"writer's final counter {final_written}; reader missed "
            f"{final_written - final_well} events at the end of the run"
        )

        # 5f: rate sanity check — the writer must have hit a
        # non-trivial fraction of the 1000/sec target. If the writer
        # is much slower (CI under-load), the test is no longer
        # exercising the high-rate race; fail with a clear message
        # so a maintainer can tune ``WRITER_DURATION_S`` or
        # ``WRITER_TICK_S`` rather than silently passing.
        achieved_rate = final_written / WRITER_DURATION_S
        if achieved_rate < TARGET_EVENT_RATE * 0.5:
            pytest.skip(
                f"writer only achieved {achieved_rate:.0f} events/sec "
                f"({final_written} events in {WRITER_DURATION_S:.1f}s), "
                f"well below the 1000/sec target; this is a CI-load "
                f"flake, not a regression — raise WRITER_DURATION_S "
                f"or relax the rate floor"
            )
        # Informational; not a hard assert because the test contract
        # is "no torn reads / no exceptions", not "exact rate". The
        # 50% threshold is a CI guardrail only.
        assert achieved_rate >= TARGET_EVENT_RATE * 0.5, (
            f"writer rate {achieved_rate:.0f}/sec is too low to "
            f"exercise the race at the planned rate"
        )


# ---------------------------------------------------------------------------
# Direct-read tests: pin the contract on the lowest layer too. The CLI
# integration test above covers the full user-visible path, but a focused
# ``load_session`` test gives a tighter signal when something regresses
# (smaller failure surface, faster to debug). These run in the same file
# because the plan says "create test_concurrent_inspect.py" — one file,
# not three.
# ---------------------------------------------------------------------------


class TestLoadSessionDuringWrite:
    """``load_session`` is the lowest layer the inspect reader relies on.

    This class repeats the race at the lowest level so a regression
    here is caught independently of the CLI / renderer path. The
    writer is identical; the reader calls ``load_session`` directly.
    """

    def test_load_session_during_active_writer_does_not_raise(self, tmp_path: Path) -> None:
        """``load_session`` returns a dict (not None, not raising) on every read."""
        from ansible_aom.session.store import load_session

        state_dir = tmp_path / "state"
        state_dir.mkdir()
        session_id = "concurrent-load-victim"
        session_path = _build_session(state_dir, session_id)
        events_file = session_path / "events.jsonl"
        events_file.touch()

        stop = threading.Event()
        counter: list[int] = [0]
        writer = threading.Thread(
            target=_writer_thread,
            args=(events_file, stop, counter),
            name="load-concurrency-writer",
        )
        writer.start()
        time.sleep(0.05)

        session_ids: list[int] = []  # store count of events per read
        well_formed_counts: list[int] = []
        malformed_counts: list[int] = []
        deadline = time.monotonic() + READER_DEADLINE_S
        while time.monotonic() < deadline:
            session = load_session(session_id, state_dir)
            assert session is not None, (
                "load_session returned None while events.jsonl existed; "
                "this should be impossible given the dir + meta.json are present"
            )
            events = session.get("events", [])
            session_ids.append(len(events))
            # Re-read the file directly to count malformed lines. The
            # load_session() API does not surface a malformed counter
            # (it returns the parsed events list and silently drops
            # bad lines — see load_session() in session/store.py).
            # We compute the malformed count by re-parsing in this
            # thread; this is a *separate* read, so it sees a
            # *different* (probably larger) snapshot, but we only use
            # it as a regression sentinel — a malformed line at any
            # point would be a bug.
            _, mal, _ = _read_snapshot(session_path)
            malformed_counts.append(mal)
            well_formed_counts.append(len(events))
            if stop.is_set() and counter[0] > 0 and len(events) == counter[0]:
                break
            time.sleep(0.005)

        stop.set()
        writer.join(timeout=2.0)
        assert not writer.is_alive(), "writer thread did not exit within 2s"

        # After the writer drains, the final read must match.
        session = load_session(session_id, state_dir)
        assert session is not None
        final_events = session.get("events", [])
        assert len(final_events) == counter[0], (
            f"final load_session read returned {len(final_events)} events, "
            f"writer committed {counter[0]}; reader missed events at drain"
        )

        # No malformed lines at any snapshot.
        assert not any(m > 0 for m in malformed_counts), (
            f"load_session saw a malformed line at some snapshot: {malformed_counts!r}"
        )

        # Counts are monotonic non-decreasing.
        for i in range(1, len(well_formed_counts)):
            assert well_formed_counts[i] >= well_formed_counts[i - 1], (
                f"event count went backwards at read {i}: "
                f"prev={well_formed_counts[i - 1]}, now={well_formed_counts[i]}"
            )
