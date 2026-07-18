"""Session manager and artifact reader/writer.

File I/O for session recording, artifact creation, and listing. The
pure post-mortem projections (failed/unreachable/changed host
collectors, display summaries) live in :mod:`ansible_aom.session.summary`.

See SPECIFICATION.md Section 6.3 for the on-disk layout.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import shutil
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ansible_aom import __version__ as _AOM_VERSION
from ansible_aom.core import diagnostics
from ansible_aom.core.stderr_classifier import classify
from ansible_aom.core.timestamp import parse_iso_timestamp
from ansible_aom.session import index as session_index

logger = logging.getLogger(__name__)

# Env vars worth snapshotting alongside the session diagnostics. Kept
# deliberately small to avoid leaking sensitive shell env into a
# user-visible JSON; AOM_* flags answer "what diagnostics knobs was the
# user running with" and ANSIBLE_STDOUT_CALLBACK + TERM answer "what
# was the rendering pipeline".
_DIAGNOSTICS_ENV_SNAPSHOT_KEYS = (
    "TERM",
    "ANSIBLE_STDOUT_CALLBACK",
    "AOM_DEBUG",
    "AOM_WATCHDOG",
    "AOM_PROFILE",
    "AOM_TRACEMALLOC",
)


# R16: bounded queue size for the async event writer. Picked to be
# generous enough to absorb a normal burst (the runner feeds events at
# the JSONL callback rate, which tops out around 5000/s on a fast
# machine) without growing the queue's memory footprint materially.
_EVENT_QUEUE_SIZE = 1000


# R17 note: events are recorded verbatim, NOT stripped to a lean subset.
# The inspect index (session/index.py) stores byte-offset ``EventRef``s
# into events.jsonl and fetches full payloads on demand via
# ``read_event`` (seek + read the whole line) for the detail pane. A
# lean projection that dropped ``msg`` / ``module_stdout`` / ``results[]``
# would break that lazy full-payload read, so the on-disk record keeps
# every field. Payload volume is handled by the async writer below (the
# hot path never blocks on the write), not by discarding data.


_uuidv7_counter = 0
_uuidv7_last_ms = 0


def generate_uuidv7() -> str:
    """Generate a UUIDv7 session ID.

    UUIDv7 is time-sortable, which allows sessions to be ordered chronologically
    by their ID alone. The first 48 bits contain a timestamp, making the first
    8 characters suitable for display in list views.

    Returns:
        UUIDv7 string in standard format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    """
    global _uuidv7_counter, _uuidv7_last_ms

    now_ms = int(time.time() * 1000)

    if now_ms == _uuidv7_last_ms:
        _uuidv7_counter = (_uuidv7_counter + 1) & 0xFFF
        if _uuidv7_counter == 0:
            now_ms += 1
    else:
        _uuidv7_counter = 0
        _uuidv7_last_ms = now_ms

    rand_bytes = uuid.uuid4().bytes

    result = bytearray(16)
    result[0] = (now_ms >> 40) & 0xFF
    result[1] = (now_ms >> 32) & 0xFF
    result[2] = (now_ms >> 24) & 0xFF
    result[3] = (now_ms >> 16) & 0xFF
    result[4] = (now_ms >> 8) & 0xFF
    result[5] = now_ms & 0xFF
    result[6] = (0x70) | ((_uuidv7_counter >> 8) & 0x0F)
    result[7] = _uuidv7_counter & 0xFF
    result[8] = (rand_bytes[8] & 0x3F) | 0x80
    result[9:] = rand_bytes[9:16]

    return str(uuid.UUID(bytes=bytes(result)))


class _AsyncEventWriter:
    """Background thread that drains events onto disk.

    R16: ``record_event`` enqueues a serialised line onto a bounded
    ``queue.Queue`` and returns immediately. This class's daemon thread
    drains the queue onto the events.jsonl file. The runner's hot path
    never blocks on disk I/O.

    On queue overflow (``put_nowait`` raises ``queue.Full``), the
    caller increments a drop counter instead of blocking. The
    filesystem can't keep up — we prefer to lose recording for a few
    events than to stall the renderer for seconds.

    Thread is a daemon so it doesn't keep the process alive at
    shutdown; ``shutdown`` is the explicit stop signal that drains
    the queue and joins the thread.
    """

    def __init__(self, events_file: Path) -> None:
        self._events_file = events_file
        self._queue: queue.Queue[bytes | None] = queue.Queue(maxsize=_EVENT_QUEUE_SIZE)
        self._dropped = 0
        self._error: str | None = None
        self._lock = threading.Lock()
        self._closed = False
        self._thread = threading.Thread(
            target=self._run,
            name="aom-event-writer",
            daemon=True,
        )
        self._thread.start()

    def enqueue(self, line: bytes) -> None:
        """Enqueue a serialised JSONL line. Returns immediately.

        Drops the line and bumps the drop counter if the queue is
        full. The runner's hot path always returns promptly — this
        matters because a 1 MB event used to spend 50-500 ms in a
        synchronous ``f.write`` call, freezing the live tree view.
        """
        if self._closed:
            return
        try:
            self._queue.put_nowait(line)
        except queue.Full:
            with self._lock:
                self._dropped += 1

    @property
    def dropped(self) -> int:
        """Cumulative count of events dropped because the queue was full."""
        with self._lock:
            return self._dropped

    @property
    def error(self) -> str | None:
        """Reason string if the writer thread hit a disk error, else None.

        Set once by the writer thread when ``open``/``write`` raises
        OSError; read by the manager so the failure can surface to the
        renderer asynchronously (the hot path never sees the error).
        """
        with self._lock:
            return self._error

    def flush(self) -> None:
        """Wait until the queue is fully drained.

        Used by tests that need to assert on the on-disk file before
        the writer has caught up. Production callers go through
        ``end_session`` (which calls ``shutdown``).
        """
        self._queue.join()

    def shutdown(self) -> None:
        """Signal the writer thread to drain and exit."""
        if self._closed:
            return
        self._closed = True
        # Sentinel None terminates the consumer loop. ``put`` blocks
        # until space is available so we don't lose any pending events
        # between enqueue and the sentinel.
        self._queue.put(None)
        self._thread.join()

    def _set_error(self, reason: str) -> None:
        with self._lock:
            if self._error is None:
                self._error = reason

    def _drain_after_failure(self) -> None:
        """Consume the rest of the queue as no-ops after a disk error.

        We can't write the pending items, but every ``get`` still needs
        a matching ``task_done`` so a concurrent ``flush`` (``queue.join``)
        can unblock. Returns when the ``shutdown`` sentinel arrives.
        """
        while True:
            item = self._queue.get()
            self._queue.task_done()
            if item is None:
                return

    def _run(self) -> None:
        """Drain the queue, writing each line to events.jsonl.

        Any disk error (``open`` or ``write``) records the reason and
        drains the remaining queue as no-ops — the failure must never
        crash the writer thread or block the producers.
        """
        try:
            # Open the file once for the lifetime of the writer; a crash
            # mid-run loses at most the last un-flushed write, the same
            # trade-off the synchronous impl had.
            handle = self._events_file.open("ab", buffering=0)
        except OSError as exc:
            logger.debug("async writer could not open events file", exc_info=True)
            self._set_error(str(exc))
            self._drain_after_failure()
            return
        with handle:
            while True:
                item = self._queue.get()
                if item is None:
                    self._queue.task_done()
                    return
                try:
                    handle.write(item)
                except OSError as exc:
                    logger.debug("async writer hit OSError; draining queue", exc_info=True)
                    self._set_error(str(exc))
                    self._queue.task_done()
                    self._drain_after_failure()
                    return
                self._queue.task_done()


class SessionManager:
    """Manages session recording and artifact creation.

    Sessions are stored during execution at:
        ~/.local/state/aom/sessions/{uuidv7}/
        ├── events.jsonl      # All JSONL events (incl. aom_stderr_line)
        └── meta.json         # Session metadata

    After completion, sessions are consolidated to:
        ~/.local/state/aom/artifacts/{uuidv7}.aom

    Attributes:
        session_id: The current session ID (UUIDv7)
        session_dir: The session directory path
    """

    def __init__(
        self,
        session_dir: Path | None = None,
        artifacts_dir: Path | None = None,
        playbook: str = "",
    ) -> None:
        self._session_dir = session_dir
        self._artifacts_dir = artifacts_dir
        self._playbook = playbook
        self._session_id: str | None = None
        self._events_file: Path | None = None
        self._meta_file: Path | None = None
        self._start_time: datetime | None = None
        self._active_sessions: dict[str, dict[str, Any]] = {}
        # R16: per-session async writer for events.jsonl. Created lazily
        # on the first ``record_*`` call so a session that records no
        # events (e.g. a test that only exercises ``end_session``) never
        # pays the thread-startup cost.
        self._writers: dict[str, _AsyncEventWriter] = {}

    @property
    def session_id(self) -> str | None:
        return self._session_id

    def _writer_for(self, session_id: str) -> _AsyncEventWriter:
        """Return the session's async writer, creating it on first use."""
        writer = self._writers.get(session_id)
        if writer is None:
            events_file = self._active_sessions[session_id]["events_file"]
            writer = _AsyncEventWriter(events_file)
            self._writers[session_id] = writer
        return writer

    @property
    def dropped_events(self) -> int:
        """Total events dropped across all sessions because a queue was full."""
        return sum(writer.dropped for writer in self._writers.values())

    def recording_failed(self, session_id: str) -> str | None:
        """Reason string if the session's background writer hit a disk error.

        Returns ``None`` when recording is healthy or no event was ever
        recorded. The runner's sink polls this after ``end_session`` to
        surface a disk failure to the renderer — the error can only be
        observed asynchronously because ``record_event`` never blocks on
        (or waits for) the write.
        """
        writer = self._writers.get(session_id)
        return writer.error if writer is not None else None

    @property
    def session_dir(self) -> Path | None:
        return self._session_dir

    def start_session(self, playbook: str, ansible_args: list[str] | None = None) -> str:
        """Create a new session and return the session ID (UUIDv7).

        Creates the session directory structure with events.jsonl
        and meta.json files.

        Args:
            playbook: Path to the playbook being executed
            ansible_args: The argv tail passed to ansible-playbook (e.g.
                ``["-i", "inv.ini", "--tags", "web"]``). Persisted to
                ``meta.json`` so ``aom rerun`` can replay the original
                invocation. Defaults to ``[]`` for callers that don't yet
                track the args.

        Returns:
            The session ID (UUIDv7 format)
        """
        session_id = generate_uuidv7()
        self._session_id = session_id
        self._playbook = playbook
        self._start_time = datetime.now(timezone.utc)

        if ansible_args is None:
            ansible_args = []

        assert self._session_dir is not None, "Session directory must be set"
        session_path = self._session_dir / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        session_path.chmod(0o755)

        self._events_file = session_path / "events.jsonl"
        self._meta_file = session_path / "meta.json"

        self._events_file.touch()
        self._events_file.chmod(0o644)

        meta = {
            "playbook": playbook,
            "ansible_args": list(ansible_args),
            "start_time": self._start_time.isoformat().replace("+00:00", "Z"),
            "version": "1.2",
            "session_id": session_id,
            # v1 (Phase 1 / Task 1.1): explicit meta.json schema marker.
            # Distinct from ``version`` (AOM package). ``load_session``
            # defaults a missing field to ``1`` for legacy sessions.
            "_schema_version": 2,
        }
        with open(self._meta_file, "w") as f:
            json.dump(meta, f)
        self._meta_file.chmod(0o644)

        self._active_sessions[session_id] = {
            "session_path": session_path,
            "events_file": self._events_file,
            "meta_file": self._meta_file,
            "start_time": self._start_time,
            "playbook": playbook,
            "ansible_args": list(ansible_args),
        }

        return session_id

    def record_event(self, session_id: str, event: dict[str, Any]) -> None:
        """Enqueue a JSONL event for the background writer.

        R16: returns immediately — the event is serialised and pushed
        onto the session's bounded queue; a daemon thread drains it to
        ``events.jsonl``. A 1 MB event used to spend 50-500 ms in a
        synchronous ``f.write`` here, freezing the live tree view. A
        disk failure in the writer never propagates out of this call;
        it surfaces asynchronously via :meth:`recording_failed`.

        Args:
            session_id: The session ID
            event: The event dictionary to record
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        self._writer_for(session_id).enqueue((json.dumps(event) + "\n").encode("utf-8"))

    def record_stderr(self, session_id: str, line: str) -> None:
        """Classify *line* and persist it as an ``aom_stderr_line`` event.

        Phase 4.4: stderr is no longer written to ``stderr.log``. Each line
        is run through the v1 :func:`classify` (see
        :mod:`ansible_aom.core.stderr_classifier`) and appended to
        ``events.jsonl`` as a synthetic ``aom_stderr_line`` event. The
        contract matches the shape the parser emits from
        ``_handle_plaintext`` so ``load_session()`` can derive
        ``session["stderr"]`` from a single source of truth.

        The store layer does not have access to the parser's connection
        tracking map, so ``connection_id`` is recorded as ``None`` and
        ``attribution_confidence`` defaults to ``"unique"`` — the same
        defaults the parser uses before connection tracking is wired in
        (Task 4.3). The original line text (ANSI-stripped or otherwise)
        is preserved verbatim in the ``line`` field.
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        classified = classify(line)
        stderr_event: dict[str, Any] = {
            "_event": "aom_stderr_line",
            "_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "line": line,
            "source": classified.source.value,
            "level": classified.level.value,
            "host": classified.host,
            "connection_id": None,
            "attribution_confidence": "unique",
        }

        # Shares the session's writer with ``record_event`` so events and
        # stderr lines keep their interleaved on-disk order.
        self._writer_for(session_id).enqueue((json.dumps(stderr_event) + "\n").encode("utf-8"))

    def flush(self, session_id: str) -> None:
        """Block until every queued event for *session_id* has hit disk.

        Delegates to the session's async writer (``queue.join``). A
        no-op for a session that recorded nothing (no writer yet).
        """
        writer = self._writers.get(session_id)
        if writer is not None:
            writer.flush()

    def end_session(
        self,
        session_id: str,
        status: str,
        *,
        preflight_task_count: int | None = None,
        resolved_host_count: int | None = None,
    ) -> None:
        """Finalize session and update metadata.

        Args:
            session_id: The session ID.
            status: Final status ("completed", "failed", "crashed").
            preflight_task_count: Preflight-derived task count (sum
                across plays). Persisted to ``meta.json`` so a future
                run with the same run configuration can show
                "last run: N tasks in T". ``None`` when preflight
                didn't yield definitions (e.g. early failure). Named to
                match the persisted field — the value comes from
                ``--list-tasks``, not from a post-run event tally.
            resolved_host_count: Union of ``resolved_hosts`` across all
                plays from preflight. Used as a secondary filter when
                matching prior runs — two runs with the same config but
                different inventory sizes bucket separately.
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        # Drain and stop the background writer BEFORE anything reads
        # events.jsonl (the sqlite index build below streams it): the
        # file must be complete first, or the index would be built from
        # a truncated log and read as stale immediately.
        writer = self._writers.get(session_id)
        if writer is not None:
            writer.shutdown()

        session_info = self._active_sessions[session_id]
        meta_file = session_info["meta_file"]
        start_time = session_info["start_time"]

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        with open(meta_file) as f:
            meta = json.load(f)

        meta["status"] = status
        meta["end_time"] = end_time.isoformat().replace("+00:00", "Z")
        meta["duration_seconds"] = duration
        meta["preflight_task_count"] = preflight_task_count
        meta["resolved_host_count"] = resolved_host_count

        with open(meta_file, "w") as f:
            json.dump(meta, f)

        # Write diagnostics.json (phase 5). Best-effort: if disk write
        # fails the run already succeeded, so swallow OSError rather
        # than turn a clean run into a crashed one.
        try:
            self._write_diagnostics_json(
                session_id=session_id,
                preflight_task_count=preflight_task_count,
                resolved_host_count=resolved_host_count,
            )
        except OSError as exc:
            logger.debug("diagnostics.json write failed for %s: %s", session_id, exc)

        # Build the derived sqlite index while the run's data is hot, so
        # the first `aom inspect` never pays the full-log streaming pass.
        # Best-effort: build_index swallows OSError/sqlite errors and
        # returns False — an index failure must not turn a finished run
        # into a crashed one; inspect rebuilds lazily.
        session_index.build_index(session_info["session_path"])

        # Dump cProfile output when AOM_PROFILE=1 (phase 7). Lands in
        # ~/.local/state/aom/profile/ rather than the session dir so
        # the session is easy to ship without the (much larger) pstats.
        try:
            profile_dir = Path.home() / ".local" / "state" / "aom" / "profile"
            diagnostics.dump_profile(profile_dir / f"{session_id}.pstats")
        except OSError as exc:
            logger.debug("profile dump failed for %s: %s", session_id, exc)

    def _write_diagnostics_json(
        self,
        *,
        session_id: str,
        preflight_task_count: int | None,
        resolved_host_count: int | None,
    ) -> None:
        """Build and write ``diagnostics.json`` next to ``meta.json``.

        Reads the in-process diagnostics module for the most recent run's
        accumulator and renderer snapshot — both default to fresh zeroed
        values when nothing was published (e.g. a recording-disabled
        codepath or an early-failure run that never got a renderer).
        """
        run_diag = diagnostics.get_last_run_diagnostics()
        renderer_stats = diagnostics.get_last_renderer_stats()

        events_received = run_diag.events_received if run_diag is not None else 0
        pty_bytes = run_diag.pty_bytes if run_diag is not None else 0
        pexpect_timeouts = run_diag.pexpect_timeouts if run_diag is not None else 0
        stall_count_max = run_diag.stall_count_max if run_diag is not None else 0
        preflight_ms = run_diag.preflight_ms if run_diag is not None else 0
        event_histogram = dict(run_diag.event_histogram) if run_diag is not None else {}

        render_calls = renderer_stats.render_calls if renderer_stats is not None else 0
        log_writes = renderer_stats.log_writes if renderer_stats is not None else 0

        stats = diagnostics.RendererStats(
            events_received=events_received,
            render_calls=render_calls,
            log_writes=log_writes,
            pty_bytes=pty_bytes,
            stall_count_max=stall_count_max,
            pexpect_timeouts=pexpect_timeouts,
            preflight_ms=preflight_ms,
            tracemalloc_peak_kb=diagnostics.get_tracemalloc_peak_kb(),
        )

        env_snapshot = {
            key: os.environ[key] for key in _DIAGNOSTICS_ENV_SNAPSHOT_KEYS if key in os.environ
        }

        record = diagnostics.build_diagnostics_record(
            session_id=session_id,
            aom_version=_AOM_VERSION,
            lifecycle_marks_ns=diagnostics.get_lifecycle_marks(),
            stats=stats,
            event_histogram=event_histogram,
            env_snapshot=env_snapshot,
            host_count=resolved_host_count,
            playbook_task_count=preflight_task_count,
            session_recording_disabled=diagnostics.session_recording_disabled(),
            session_disable_reason=diagnostics.session_disable_reason(),
            psutil_disabled_reason=diagnostics.psutil_disabled_reason(),
        )

        diag_file = self._active_sessions[session_id]["session_path"] / "diagnostics.json"
        with open(diag_file, "w") as f:
            json.dump(record, f)

    def create_artifact(self, session_id: str) -> Path:
        """Create .aom artifact file from session.

        The artifact format is JSONL with:
        - First line: metadata header
        - Middle lines: events
        - Last line: stats summary

        Args:
            session_id: The session ID

        Returns:
            Path to the created artifact file
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        # Ensure any queued events have hit disk before we read the log.
        # (No-op after ``end_session`` already drained the writer.)
        self.flush(session_id)

        session_info = self._active_sessions[session_id]
        session_path = session_info["session_path"]

        if self._artifacts_dir is None:
            raise ValueError("artifacts_dir not set")

        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = self._artifacts_dir / f"{session_id}.aom"

        events_file = session_path / "events.jsonl"
        meta_file = session_path / "meta.json"

        with open(meta_file) as f:
            meta = json.load(f)

        events = []
        if events_file.exists():
            with open(events_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))

        stats_event = None
        for event in reversed(events):
            if event.get("_event") == "v2_playbook_on_stats":
                stats_event = event
                break

        with open(artifact_path, "w") as f:
            metadata_line = {
                "type": "metadata",
                "playbook": meta["playbook"],
                "version": meta.get("version", "1.0"),
                "created": meta.get(
                    "end_time", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                ),
                "session_id": session_id,
            }
            f.write(json.dumps(metadata_line) + "\n")

            for event in events:
                event_line = {"type": "event", **event}
                f.write(json.dumps(event_line) + "\n")

            if stats_event:
                stats_line = {
                    "type": "stats",
                    **stats_event.get("stats", {}),
                }
            else:
                stats_line = {"type": "stats"}
            f.write(json.dumps(stats_line) + "\n")

        artifact_path.chmod(0o600)

        return artifact_path


def cleanup_old_sessions(
    session_dir: Path,
    keep_count: int = 100,
    keep_days: int = 30,
) -> int:
    """Remove old sessions based on policy.

    Sessions are cleaned up based on:
    - Count: Keep the most recent N sessions
    - Age: Remove sessions older than D days

    Args:
        session_dir: Directory containing session directories
        keep_count: Maximum number of sessions to keep (default 100)
        keep_days: Maximum age in days (default 30)

    Returns:
        Number of sessions deleted
    """
    if not session_dir.exists():
        return 0

    sessions = []
    for session_path in session_dir.iterdir():
        if not session_path.is_dir():
            continue

        # mtime fallback for directories without a usable meta.json. Using
        # datetime.now() here would assign every fallback session the same
        # microsecond, making the eventual sort order non-deterministic
        # whenever many fallbacks coexist (TC-228 used to fail for this
        # reason). The directory mtime is set at creation and updated on
        # writes, which is good enough to order by recency.
        fallback_time = datetime.fromtimestamp(session_path.stat().st_mtime, tz=timezone.utc)

        meta_file = session_path / "meta.json"
        if meta_file.exists():
            try:
                with open(meta_file) as f:
                    meta = json.load(f)
                start_time_str = meta.get("start_time", "")
                if start_time_str:
                    start_time = parse_iso_timestamp(start_time_str)
                    sessions.append((session_path, start_time, session_path.name, meta))
                    continue
            except json.JSONDecodeError, ValueError:
                pass
        sessions.append((session_path, fallback_time, session_path.name, {}))

    sessions.sort(key=lambda x: (x[1], x[2]), reverse=True)

    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)

    to_delete = []
    for i, (session_path, start_time, _, _meta) in enumerate(sessions):
        if i >= keep_count or start_time < cutoff:
            to_delete.append(session_path)

    deleted = 0
    for session_path in to_delete:
        shutil.rmtree(session_path)
        deleted += 1

    return deleted


def list_sessions(session_dir: Path) -> list[dict[str, Any]]:
    """List all sessions in the state directory.

    Returns sessions sorted by start time (newest first).

    Args:
        session_dir: Directory containing session directories

    Returns:
        List of session summary dictionaries, each containing:
        - session_id: Full UUID
        - short_id: First 8 characters for display
        - playbook: Playbook name
        - start_time: Start time string
        - status: Session status
        - duration_seconds: Duration in seconds (if completed)
    """
    if not session_dir.exists():
        return []

    sessions = []
    for session_path in session_dir.iterdir():
        if not session_path.is_dir():
            continue

        meta_file = session_path / "meta.json"
        if not meta_file.exists():
            continue

        try:
            with open(meta_file) as f:
                meta = json.load(f)

            session_id = session_path.name
            sessions.append(
                {
                    "session_id": session_id,
                    "short_id": session_id[:8],
                    "playbook": meta.get("playbook", ""),
                    "start_time": meta.get("start_time", ""),
                    "status": meta.get("status", ""),
                    "duration_seconds": meta.get("duration_seconds"),
                }
            )
        except json.JSONDecodeError, KeyError:
            continue

    sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)

    return sessions


def load_session_meta(session_id: str, session_dir: Path) -> dict[str, Any] | None:
    """Load a session's cheap metadata: meta.json + diagnostics.json only.

    Same fields and defaults as :func:`load_session` minus ``events`` /
    ``stderr`` / ``malformed_lines`` — never opens ``events.jsonl``, so
    it is safe to call for every session on disk regardless of log size.
    Returns None if the session directory doesn't exist.
    """
    session_path = session_dir / session_id
    if not session_path.exists():
        return None

    meta_file = session_path / "meta.json"

    result: dict[str, Any] = {}
    if meta_file.exists():
        try:
            with open(meta_file) as f:
                result = json.load(f)
        except json.JSONDecodeError:
            result = {"playbook": "", "status": ""}

    if "_schema_version" not in result:
        result["_schema_version"] = 1

    diag_file = session_path / "diagnostics.json"
    if diag_file.exists():
        try:
            with open(diag_file) as f:
                result["diagnostics"] = json.load(f)
        except OSError, json.JSONDecodeError:
            result["diagnostics"] = None
    else:
        result["diagnostics"] = None

    result["session_id"] = session_id
    return result


def load_session(session_id: str, session_dir: Path) -> dict[str, Any] | None:
    """Load a session by ID.

    Args:
        session_id: The session ID to load
        session_dir: Directory containing session directories

    Returns:
        Session dictionary containing:
        - metadata fields (playbook, status, etc.)
        - events: List of parsed event dictionaries
        - stderr: List of stderr lines
        - malformed_lines: Count of malformed JSONL lines
        Returns None if session not found.
    """
    session_path = session_dir / session_id
    result = load_session_meta(session_id, session_dir)
    if result is None:
        return None

    if not (session_path / "meta.json").exists():
        # v1 (Phase 8 / Task 8.2): crash-recovery contract. When
        # ``meta.json`` is missing the run was almost certainly
        # interrupted mid-write (kernel OOM, power loss, SIGKILL)
        # between ``start_session`` creating the directory and
        # ``end_session`` rewriting the meta dict. The event stream in
        # ``events.jsonl`` is the authoritative record of what
        # happened, so we degrade gracefully: warn loudly, return
        # what we have (empty meta + parsed events), and let
        # ``aom replay`` / ``aom inspect`` continue. Replay reads
        # ``status`` with a "completed" default (drivers/replay.py),
        # inspect treats empty ``playbook`` as "no name available".
        logger.warning(
            "Session %s is missing meta.json; replaying from events.jsonl only. "
            "The run was likely interrupted before end_session completed.",
            session_id,
        )

    events_file = session_path / "events.jsonl"
    events = []
    malformed_lines = 0

    if events_file.exists():
        with open(events_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    malformed_lines += 1

    result["events"] = events
    result["malformed_lines"] = malformed_lines

    # Phase 4 (v1 verbosity): stderr is now embedded in events.jsonl as
    # ``aom_stderr_line`` synthetic events. Extract them here so callers
    # that read ``result["stderr"]`` (inspect text, TUI) keep working
    # without changes. Legacy sessions without ``aom_stderr_line`` events
    # produce an empty list.
    stderr_lines: list[str] = []
    for ev in result.get("events", []):
        if ev.get("_event") == "aom_stderr_line":
            stderr_lines.append(ev.get("line", ""))
    result["stderr"] = stderr_lines

    return result


def find_latest_session(session_dir: Path) -> str | None:
    """Return the session_id of the most-recently-started session, or None.

    Reuses ``list_sessions`` (which already sorts newest-first) and returns
    just the top entry's id. Sessions without a parseable ``start_time`` are
    ignored. Returns ``None`` when no sessions exist or the directory is
    missing.
    """
    sessions = list_sessions(session_dir)
    if not sessions:
        return None
    return sessions[0].get("session_id")
