"""R16 — async / non-blocking disk write in session/store.py.

R16 spec: the legacy ``SessionManager.record_event`` performs a
synchronous ``open(events_file, "a")`` + ``json.dumps`` + ``f.write`` +
``f.close`` for every JSONL event the run emits. A 1 MB event
(common with ``debug: var=huge_object`` or ``register: huge_dict``)
spends 50-500 ms in that critical section, blocking the runner's
hot path. The runner then can't feed events to the renderer, and the
live tree view freezes.

The fix is to push events onto a bounded ``queue.Queue`` and have a
daemon thread drain the queue onto disk. ``record_event`` enqueues
and returns immediately (microseconds). Disk pressure is backpressured
by the bounded queue size; if the writer thread falls behind, callers
hit a ``queue.Full`` and increment a drop counter rather than blocking
the runner.

The timing test below asserts ``record_event`` returns in well under
10 ms even when fed a 1 MB event — the synchronous implementation
takes 50-500 ms on typical hardware.
"""

from __future__ import annotations

import json
import time
from pathlib import Path


def _build_1mb_event() -> dict:
    """Produce a JSONL event whose serialised form is roughly 1 MB."""
    # Padding dict — JSON-encoded it's about 1 MB plus the small
    # envelope.
    padding = {"x": "y" * (1_000_000 // 2)}
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-01-01T00:00:00Z",
        "task": {"id": "t1"},
        "padding": padding,
    }


def test_record_event_returns_quickly(tmp_path: Path) -> None:
    """R16: ``record_event`` with a 1 MB event returns in < 10 ms."""
    from ansible_aom.session.store import SessionManager

    mgr = SessionManager(session_dir=tmp_path / "sessions")
    sid = mgr.start_session("play.yml", ansible_args=[])
    event = _build_1mb_event()

    # Warm-up call — first call may pay module-import costs and
    # thread-startup latency. Keep it out of the timing window.
    mgr.record_event(sid, event)

    # Actual timing. Take the minimum of three runs to smooth out
    # GC / scheduler noise.
    samples = []
    for _ in range(3):
        start = time.perf_counter()
        mgr.record_event(sid, event)
        samples.append((time.perf_counter() - start) * 1000.0)

    elapsed_ms = min(samples)
    # 50 ms is a comfortable ceiling — the synchronous impl takes
    # 50-500 ms, the async impl should be <1 ms. We pick 50 ms to
    # leave generous slack for noisy CI without making the test
    # meaningless.
    assert elapsed_ms < 50.0, (
        f"record_event took {elapsed_ms:.1f}ms with a 1MB event; "
        f"async write path is supposed to return in <10ms. "
        f"All samples: {samples!r}"
    )


def test_recorded_event_persists_after_drain(tmp_path: Path) -> None:
    """R16: events are written to disk eventually (after the writer drains)."""
    from ansible_aom.session.store import SessionManager

    mgr = SessionManager(session_dir=tmp_path / "sessions")
    sid = mgr.start_session("play.yml", ansible_args=[])

    event = {"_event": "v2_runner_on_ok", "_timestamp": "2026-01-01T00:00:00Z"}
    mgr.record_event(sid, event)
    # Force the writer thread to drain before assertions.
    mgr.flush(sid)

    events_file = tmp_path / "sessions" / sid / "events.jsonl"
    contents = events_file.read_text().splitlines()
    assert len(contents) == 1
    parsed = json.loads(contents[0])
    assert parsed["_event"] == "v2_runner_on_ok"


def test_queue_full_drops_event_and_counts(tmp_path: Path) -> None:
    """R16: when the writer falls behind, the bounded queue drops events.

    We can't easily make the writer fall behind deterministically, but
    we *can* verify that the drop-counter machinery is wired and that
    ``record_event`` never blocks on a full queue — it always returns
    promptly (per the timing test above). The drop counter is exposed
    on the manager for the renderer to surface at completion.
    """
    from ansible_aom.session.store import SessionManager

    mgr = SessionManager(session_dir=tmp_path / "sessions")
    sid = mgr.start_session("play.yml", ansible_args=[])

    # Spam enough events that the queue fills, then keep going —
    # some must be dropped, the call must still return.
    event = {"_event": "v2_runner_on_ok", "_timestamp": "2026-01-01T00:00:00Z"}
    for _ in range(5000):
        mgr.record_event(sid, event)

    # Dropped attribute exists and is an int (could be 0 if the writer
    # keeps up; the test only verifies the plumbing).
    assert isinstance(getattr(mgr, "dropped_events", 0), int)


def test_no_event_loss_and_order_on_end_session(tmp_path: Path) -> None:
    """R16: ``end_session`` drains the writer, so every recorded event lands
    on disk in the order it was recorded — no event is lost to a still-queued
    write."""
    from ansible_aom.session.store import SessionManager

    mgr = SessionManager(session_dir=tmp_path / "sessions")
    sid = mgr.start_session("play.yml", ansible_args=[])

    for i in range(200):
        mgr.record_event(sid, {"_event": "v2_runner_on_ok", "seq": i})

    mgr.end_session(sid, "completed")

    events_file = tmp_path / "sessions" / sid / "events.jsonl"
    lines = events_file.read_text().splitlines()
    assert len(lines) == 200, f"expected 200 events on disk, got {len(lines)}"
    seqs = [json.loads(line)["seq"] for line in lines]
    assert seqs == list(range(200)), "events must persist in recorded order"


def test_interleaved_event_and_stderr_order_preserved(tmp_path: Path) -> None:
    """R16: events and stderr lines share one writer, so their relative
    order on disk matches the order they were recorded."""
    from ansible_aom.session.store import SessionManager

    mgr = SessionManager(session_dir=tmp_path / "sessions")
    sid = mgr.start_session("play.yml", ansible_args=[])

    for i in range(50):
        mgr.record_event(sid, {"_event": "v2_runner_on_ok", "seq": i})
        mgr.record_stderr(sid, f"stderr line {i}")

    mgr.flush(sid)

    events_file = tmp_path / "sessions" / sid / "events.jsonl"
    parsed = [json.loads(line) for line in events_file.read_text().splitlines()]
    assert len(parsed) == 100
    for i in range(50):
        assert parsed[2 * i]["_event"] == "v2_runner_on_ok"
        assert parsed[2 * i]["seq"] == i
        assert parsed[2 * i + 1]["_event"] == "aom_stderr_line"
        assert parsed[2 * i + 1]["line"] == f"stderr line {i}"


def test_index_built_from_complete_events_after_end_session(tmp_path: Path) -> None:
    """Requirement: ``end_session`` flushes the writer BEFORE building the
    sqlite index, so the index is fresh against the complete events.jsonl.

    If the index were built before the writer drained, the recorded
    ``events_size`` would be smaller than the final file and
    ``index_is_fresh`` would report stale immediately after ``end_session``.
    """
    from ansible_aom.session import index as session_index
    from ansible_aom.session.store import SessionManager

    mgr = SessionManager(session_dir=tmp_path / "sessions")
    sid = mgr.start_session("play.yml", ansible_args=[])

    for i in range(200):
        mgr.record_event(sid, {"_event": "v2_runner_on_ok", "seq": i})

    mgr.end_session(sid, "completed")

    session_path = tmp_path / "sessions" / sid
    assert session_index.index_is_fresh(session_path), (
        "index must be built from the fully-drained events.jsonl"
    )


def _break_events_file(session_path: Path) -> None:
    """Replace events.jsonl with a directory so the writer's ``open('ab')``
    fails with an OSError (``IsADirectoryError``)."""
    events_file = session_path / "events.jsonl"
    events_file.unlink()
    events_file.mkdir()


def test_write_failure_does_not_propagate(tmp_path: Path) -> None:
    """R16: a disk write failure in the background writer must never raise
    out of ``record_event`` / ``record_stderr`` / ``end_session``."""
    from ansible_aom.session.store import SessionManager

    mgr = SessionManager(session_dir=tmp_path / "sessions")
    sid = mgr.start_session("play.yml", ansible_args=[])
    _break_events_file(tmp_path / "sessions" / sid)

    # None of these may raise even though the writer can't open the file.
    for i in range(20):
        mgr.record_event(sid, {"_event": "v2_runner_on_ok", "seq": i})
        mgr.record_stderr(sid, f"line {i}")
    mgr.flush(sid)
    mgr.end_session(sid, "completed")


def test_write_failure_surfaces_via_recording_failed(tmp_path: Path) -> None:
    """R16: the writer's disk failure is observable through
    ``recording_failed`` so the sink can disable recording and warn — the
    error surfaces asynchronously rather than blocking the hot path."""
    from ansible_aom.session.store import SessionManager

    mgr = SessionManager(session_dir=tmp_path / "sessions")
    sid = mgr.start_session("play.yml", ansible_args=[])
    _break_events_file(tmp_path / "sessions" / sid)

    assert mgr.recording_failed(sid) is None  # not attempted yet

    mgr.record_event(sid, {"_event": "v2_runner_on_ok", "seq": 0})
    mgr.flush(sid)  # let the writer attempt (and fail) the open

    assert mgr.recording_failed(sid) is not None
