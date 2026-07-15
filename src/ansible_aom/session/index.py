"""Derived per-session sqlite index over ``events.jsonl``.

``events.jsonl`` remains the source of truth; ``index.db`` is a
disposable acceleration structure built from one streaming pass. It
stores what the inspect views need — per-play / per-task / per-(task,
host) aggregates, run-level host counts, verbose rows, and byte spans
(``EventRef``) of the events the detail pane may want — so re-opening a
session never re-parses the log, and payload bytes stay on disk until a
specific event is requested.

Freshness is keyed on the events file's ``(size, mtime_ns)``: a session
that grew (still running, or resumed) simply goes stale and is rebuilt
on next access. Writes go to a temp file and are atomically renamed so
a crash mid-build never leaves a torn index.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import timedelta
from pathlib import Path
from typing import Any, Iterator, Literal, Mapping

from ansible_aom.core.inspect_model import (
    EventRef,
    PlayRow,
    RunSummary,
    SessionIndex,
    SessionIndexAccumulator,
    StatusCounts,
    TaskHostRow,
    TaskRow,
    TaskTreeNode,
    stderr_row_from_event,
    summary_from_index,
    task_ids_by_play,
    tree_from_index,
)

logger = logging.getLogger(__name__)

INDEX_SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE host_counts (
    host TEXT PRIMARY KEY,
    ok INTEGER, changed INTEGER, failed INTEGER, skipped INTEGER, unreachable INTEGER
);
CREATE TABLE plays (seq INTEGER PRIMARY KEY, play_id TEXT, name TEXT);
CREATE TABLE tasks (
    seq INTEGER PRIMARY KEY,
    task_id TEXT, play_id TEXT, name TEXT, path TEXT, group_key TEXT,
    ok INTEGER, changed INTEGER, failed INTEGER, skipped INTEGER, unreachable INTEGER,
    duration_us INTEGER,
    ref_offset INTEGER, ref_length INTEGER
);
CREATE TABLE task_hosts (
    task_seq INTEGER, seq INTEGER, host TEXT,
    ok INTEGER, changed INTEGER, failed INTEGER, skipped INTEGER, unreachable INTEGER,
    ref_offset INTEGER, ref_length INTEGER,
    PRIMARY KEY (task_seq, seq)
);
CREATE TABLE stderr (
    seq INTEGER PRIMARY KEY,
    line TEXT, source TEXT, connection_id TEXT, ambiguous INTEGER
);
CREATE TABLE connections (connection_id TEXT PRIMARY KEY, task_id TEXT, host TEXT);
"""


def index_path(session_path: Path) -> Path:
    return session_path / "index.db"


def _events_path(session_path: Path) -> Path:
    return session_path / "events.jsonl"


def events_stat(session_path: Path) -> tuple[int, int] | None:
    """(size, mtime_ns) of the session's events.jsonl, or None if absent.

    The freshness token for anything derived from the log — the index
    itself, and the TUI's cached fallback models for sessions that can't
    be indexed.
    """
    try:
        st = _events_path(session_path).stat()
    except OSError:
        return None
    return (st.st_size, st.st_mtime_ns)


def _read_meta_table(db_path: Path) -> dict[str, str] | None:
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        return dict(conn.execute("SELECT key, value FROM meta"))
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def index_is_fresh(session_path: Path) -> bool:
    """True when index.db exists and matches events.jsonl byte-for-byte.

    Any mismatch — missing file, schema bump, size or mtime drift — means
    "rebuild"; there is deliberately no partial-validity notion.
    """
    stat = events_stat(session_path)
    if stat is None or not index_path(session_path).exists():
        return False
    meta = _read_meta_table(index_path(session_path))
    if meta is None:
        return False
    return (
        meta.get("schema_version") == str(INDEX_SCHEMA_VERSION)
        and meta.get("events_size") == str(stat[0])
        and meta.get("events_mtime_ns") == str(stat[1])
    )


_STDERR_BATCH_SIZE = 10_000


def build_index(session_path: Path) -> bool:
    """Stream events.jsonl into a fresh index.db. Returns False when the
    session has no events file; sqlite/OS errors also return False (the
    index is an optimization — callers fall back to the slow path).

    stderr rows go straight into sqlite in batches as the file streams
    (``collect_stderr=False``), so peak memory is bounded by tasks×hosts
    even for verbose runs with hundreds of thousands of stderr lines.
    """
    events_path = _events_path(session_path)
    # Stat BEFORE parsing: if the file grows while we read (running
    # session), the recorded size is smaller than reality and the index
    # correctly reads as stale on the next freshness check.
    stat = events_stat(session_path)
    if stat is None:
        return False

    # PID+TID-unique temp name: a concurrent build of the same session
    # (background backfill racing a selection-triggered load) must not
    # share a half-written file. Both produce identical content; last
    # os.replace wins.
    tmp_path = index_path(session_path).with_suffix(
        f".tmp-{os.getpid()}-{threading.get_ident()}.db"
    )
    acc = SessionIndexAccumulator(collect_stderr=False)
    malformed = 0
    try:
        tmp_path.unlink(missing_ok=True)
        conn = sqlite3.connect(tmp_path)
        try:
            # The temp db is disposable (atomically renamed on success,
            # deleted on failure), so durability guarantees are wasted
            # cost here — a crash mid-build just means "no index yet".
            conn.execute("PRAGMA journal_mode = OFF")
            conn.execute("PRAGMA synchronous = OFF")
            conn.executescript(_SCHEMA)
            stderr_batch: list[tuple[int, str, str | None, str | None, int]] = []
            stderr_seq = 0
            offset = 0
            with open(events_path, "rb") as f:
                for line in f:
                    length = len(line)
                    stripped = line.strip()
                    if stripped:
                        try:
                            event = json.loads(stripped)
                        except json.JSONDecodeError:
                            malformed += 1
                        else:
                            if not isinstance(event, dict):
                                malformed += 1
                            elif event.get("_event") == "aom_stderr_line":
                                row = stderr_row_from_event(event)
                                stderr_batch.append(
                                    (
                                        stderr_seq,
                                        row.line,
                                        row.source,
                                        row.connection_id,
                                        int(row.ambiguous),
                                    )
                                )
                                stderr_seq += 1
                                if len(stderr_batch) >= _STDERR_BATCH_SIZE:
                                    conn.executemany(
                                        "INSERT INTO stderr VALUES (?, ?, ?, ?, ?)", stderr_batch
                                    )
                                    stderr_batch.clear()
                            else:
                                acc.feed(event, ref=EventRef(offset=offset, length=length))
                    offset += length
            if stderr_batch:
                conn.executemany("INSERT INTO stderr VALUES (?, ?, ?, ?, ?)", stderr_batch)
            _write_index_db(conn, acc.finish(), events_stat=stat, malformed=malformed)
        finally:
            conn.close()
        os.replace(tmp_path, index_path(session_path))
    except (OSError, sqlite3.Error) as exc:
        logger.debug("index build failed for %s: %s", session_path, exc)
        tmp_path.unlink(missing_ok=True)
        return False
    return True


def _write_index_db(
    conn: sqlite3.Connection,
    index: SessionIndex,
    *,
    events_stat: tuple[int, int],
    malformed: int,
) -> None:
    """Write all tables except ``stderr`` (streamed in by the caller)
    into an already-schema'd connection, then commit."""
    conn.executemany(
        "INSERT INTO meta VALUES (?, ?)",
        [
            ("schema_version", str(INDEX_SCHEMA_VERSION)),
            ("events_size", str(events_stat[0])),
            ("events_mtime_ns", str(events_stat[1])),
            ("failed_task_count", str(index.failed_task_count)),
            ("fallback_play_name", index.fallback_play_name),
            ("malformed_lines", str(malformed)),
        ],
    )
    conn.executemany(
        "INSERT INTO host_counts VALUES (?, ?, ?, ?, ?, ?)",
        [
            (host, c.ok, c.changed, c.failed, c.skipped, c.unreachable)
            for host, c in index.host_counts.items()
        ],
    )
    conn.executemany(
        "INSERT INTO plays VALUES (?, ?, ?)",
        [(seq, p.play_id, p.name) for seq, p in enumerate(index.plays)],
    )
    task_rows = []
    task_host_rows = []
    for seq, task in enumerate(index.tasks):
        duration_us = (
            task.duration // timedelta(microseconds=1) if task.duration is not None else None
        )
        ref = task.raw_ref
        task_rows.append(
            (
                seq,
                task.task_id,
                task.play_id,
                task.name,
                task.path,
                task.group_key,
                task.counts.ok,
                task.counts.changed,
                task.counts.failed,
                task.counts.skipped,
                task.counts.unreachable,
                duration_us,
                ref.offset if ref else None,
                ref.length if ref else None,
            )
        )
        for host_seq, h in enumerate(task.hosts):
            href = h.raw_ref
            task_host_rows.append(
                (
                    seq,
                    host_seq,
                    h.host,
                    h.counts.ok,
                    h.counts.changed,
                    h.counts.failed,
                    h.counts.skipped,
                    h.counts.unreachable,
                    href.offset if href else None,
                    href.length if href else None,
                )
            )
    conn.executemany(
        "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", task_rows
    )
    conn.executemany("INSERT INTO task_hosts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", task_host_rows)
    conn.executemany(
        "INSERT INTO connections VALUES (?, ?, ?)",
        [(conn_id, task_id, host) for conn_id, (task_id, host) in index.connections.items()],
    )
    conn.commit()


def ensure_index(session_path: Path) -> bool:
    """Build the index if missing or stale. True when a fresh index exists."""
    if index_is_fresh(session_path):
        return True
    return build_index(session_path)


def sessions_needing_index(session_dir: Path) -> list[Path]:
    """Session directories with an events.jsonl but no fresh index.

    Newest first: session ids are UUIDv7 (time-sortable by name), and
    backfill consumers work the list in order — recent runs are the ones
    the user actually opens, so they get their indexes first.
    """
    if not session_dir.exists():
        return []
    stale: list[Path] = []
    for path in sorted(session_dir.iterdir(), reverse=True):
        if not path.is_dir() or not _events_path(path).exists():
            continue
        if not index_is_fresh(path):
            stale.append(path)
    return stale


# Below this combined log volume a process pool costs more than it saves
# (worker spawn + module import); build sequentially in-process instead.
_PARALLEL_MIN_BYTES = 64 * 1024 * 1024


def build_indexes(
    session_paths: list[Path],
    *,
    max_workers: int | None = None,
    parallel_min_bytes: int = _PARALLEL_MIN_BYTES,
) -> Iterator[tuple[Path, bool]]:
    """Build indexes for many sessions, yielding (path, ok) as each lands.

    Index builds are CPU-bound (json parsing dominates) and fully
    independent — one events.jsonl in, one index.db out — so large
    backlogs fan out over a process pool and scale with cores instead
    of being serialised behind the GIL. Small backlogs build inline.
    """
    total_bytes = 0
    for path in session_paths:
        stat = events_stat(path)
        if stat is not None:
            total_bytes += stat[0]

    if len(session_paths) <= 1 or total_bytes < parallel_min_bytes:
        for path in session_paths:
            yield (path, build_index(path))
        return

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(build_index, path): path for path in session_paths}
        for future in as_completed(futures):
            path = futures[future]
            try:
                ok = bool(future.result())
            except Exception as exc:  # worker died (OOM kill, interpreter error)
                logger.debug("parallel index build failed for %s: %s", path, exc)
                ok = False
            yield (path, ok)


def _counts(row: Any, base: int) -> StatusCounts:
    return StatusCounts(
        ok=row[base],
        changed=row[base + 1],
        failed=row[base + 2],
        skipped=row[base + 3],
        unreachable=row[base + 4],
    )


def _ref(offset: Any, length: Any) -> EventRef | None:
    if offset is None or length is None:
        return None
    return EventRef(offset=int(offset), length=int(length))


def load_structure(
    session_path: Path,
    *,
    failed_hosts_only: bool = False,
    include_task_ids: frozenset[str] | None = None,
) -> SessionIndex | None:
    """Load plays/tasks/hosts aggregates from index.db (no verbose rows).

    Verbose rows can number in the hundreds of thousands; they load
    on demand via :func:`query_verbose` instead of with the structure.
    Returns None when the index is missing or unreadable.

    ``failed_hosts_only`` skips host rows for tasks without failures —
    per-task aggregates are stored, so the text renderer (header +
    failures + verbose) doesn't need host rows for passing tasks, and
    the load becomes O(failures) instead of O(tasks × hosts).
    ``include_task_ids`` forces host rows for specific tasks regardless
    (the ``--task <name>`` verbose scope needs its task's hosts).
    """
    db_path = index_path(session_path)
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        meta = dict(conn.execute("SELECT key, value FROM meta"))
        plays = tuple(
            PlayRow(play_id=row[0], name=row[1])
            for row in conn.execute("SELECT play_id, name FROM plays ORDER BY seq")
        )
        host_counts = {
            row[0]: _counts(row, 1)
            for row in conn.execute(
                "SELECT host, ok, changed, failed, skipped, unreachable FROM host_counts"
            )
        }
        host_query = (
            "SELECT task_seq, host, ok, changed, failed, skipped, unreachable,"
            " ref_offset, ref_length FROM task_hosts"
        )
        params: list[str] = []
        if failed_hosts_only:
            included = sorted(include_task_ids or ())
            placeholders = ",".join("?" for _ in included)
            host_query += (
                " WHERE task_seq IN (SELECT seq FROM tasks"
                f" WHERE failed > 0 OR unreachable > 0 OR task_id IN ({placeholders}))"
            )
            params = included
        hosts_by_task: dict[int, list[TaskHostRow]] = {}
        for row in conn.execute(host_query + " ORDER BY task_seq, seq", params):
            hosts_by_task.setdefault(row[0], []).append(
                TaskHostRow(
                    host=row[1],
                    counts=_counts(row, 2),
                    raw_event=None,
                    raw_ref=_ref(row[7], row[8]),
                )
            )
        tasks = []
        for row in conn.execute(
            "SELECT seq, task_id, play_id, name, path, group_key,"
            " ok, changed, failed, skipped, unreachable,"
            " duration_us, ref_offset, ref_length FROM tasks ORDER BY seq"
        ):
            tasks.append(
                TaskRow(
                    task_id=row[1],
                    play_id=row[2],
                    name=row[3],
                    path=row[4],
                    group_key=row[5],
                    counts=_counts(row, 6),
                    hosts=tuple(hosts_by_task.get(row[0], [])),
                    duration=(timedelta(microseconds=row[11]) if row[11] is not None else None),
                    raw_event=None,
                    raw_ref=_ref(row[12], row[13]),
                )
            )
    except sqlite3.Error:
        return None
    finally:
        conn.close()
    return SessionIndex(
        plays=plays,
        tasks=tuple(tasks),
        host_counts=host_counts,
        failed_task_count=int(meta.get("failed_task_count", "0")),
        stderr=(),
        connections={},
        fallback_play_name=meta.get("fallback_play_name", ""),
    )


def find_task_id_by_name(session_path: Path, task_name: str) -> str | None:
    """First task id whose name matches, in execution order. None if absent."""
    db_path = index_path(session_path)
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        row = conn.execute(
            "SELECT task_id FROM tasks WHERE name = ? ORDER BY seq LIMIT 1", (task_name,)
        ).fetchone()
    except sqlite3.Error:
        return None
    finally:
        conn.close()
    return row[0] if row else None


def load_tree(session_path: Path, *, playbook: str) -> TaskTreeNode | None:
    """Assemble the task tree from index.db. None when no readable index."""
    index = load_structure(session_path)
    if index is None:
        return None
    return tree_from_index(index, playbook=playbook)


def load_summary(session_path: Path, meta: Mapping) -> RunSummary | None:
    """Build a RunSummary from index.db aggregates plus meta.json fields.

    Reads only the ``host_counts`` table and the meta keys — deliberately
    NOT :func:`load_structure` — so the Runs pane can summarise every
    session on disk without materialising tasks×hosts rows per session.
    """
    db_path = index_path(session_path)
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        db_meta = dict(conn.execute("SELECT key, value FROM meta"))
        host_counts = {
            row[0]: _counts(row, 1)
            for row in conn.execute(
                "SELECT host, ok, changed, failed, skipped, unreachable FROM host_counts"
            )
        }
    except sqlite3.Error:
        return None
    finally:
        conn.close()
    summary_index = SessionIndex(
        plays=(),
        tasks=(),
        host_counts=host_counts,
        failed_task_count=int(db_meta.get("failed_task_count", "0")),
        stderr=(),
        connections={},
        fallback_play_name="",
    )
    return summary_from_index(summary_index, meta)


def query_verbose(
    session_path: Path,
    *,
    tree: TaskTreeNode,
    level: Literal["run", "play", "task"],
    play_name: str | None = None,
    task_id: str | None = None,
    host: str | None = None,
) -> tuple[str, ...]:
    """Verbose lines for a focus scope, filtered inside sqlite.

    The WHERE clauses implement exactly the rules of core
    ``verbose_lines_from_rows`` (parity-pinned by tests) — pushing the
    filter into SQL avoids materialising hundreds of thousands of
    off-scope rows just to drop them:

    - run:  ``source = 'run_level'``
    - task: run-level OR the first connection acquired for the focused
      ``(task_id, host)`` pair
    - play: run-level OR any connection whose task belongs to the play
    """
    db_path = index_path(session_path)
    if not db_path.exists():
        return ()
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return ()
    try:
        if level == "task":
            selected: str | None = None
            if task_id and host:
                found = conn.execute(
                    "SELECT connection_id FROM connections WHERE task_id = ? AND host = ?"
                    " ORDER BY rowid LIMIT 1",
                    (task_id, host),
                ).fetchone()
                selected = found[0] if found else None
            cursor = conn.execute(
                "SELECT line, ambiguous FROM stderr"
                " WHERE source = 'run_level' OR connection_id = ? ORDER BY seq",
                (selected,),
            )
        elif level == "play":
            play_ids = sorted(task_ids_by_play(tree).get(play_name or "", set()))
            conn.execute("CREATE TEMP TABLE scope_tasks (task_id TEXT PRIMARY KEY)")
            conn.executemany(
                "INSERT OR IGNORE INTO scope_tasks VALUES (?)", [(t,) for t in play_ids]
            )
            cursor = conn.execute(
                "SELECT line, ambiguous FROM stderr"
                " WHERE source = 'run_level' OR connection_id IN"
                " (SELECT connection_id FROM connections"
                "  WHERE task_id IN (SELECT task_id FROM scope_tasks))"
                " ORDER BY seq"
            )
        else:
            cursor = conn.execute(
                "SELECT line, ambiguous FROM stderr WHERE source = 'run_level' ORDER BY seq"
            )
        return tuple(f"? {line}" if ambiguous else line for line, ambiguous in cursor)
    except sqlite3.Error:
        return ()
    finally:
        conn.close()


def read_event(session_path: Path, ref: EventRef) -> dict | None:
    """Seek one event line out of events.jsonl and parse it.

    None on any failure (truncated file, rewritten log, malformed span) —
    callers treat a missing event like a legacy session without payloads.
    """
    try:
        with open(_events_path(session_path), "rb") as f:
            f.seek(ref.offset)
            data = f.read(ref.length)
    except OSError:
        return None
    try:
        event = json.loads(data)
    except json.JSONDecodeError:
        return None
    return event if isinstance(event, dict) else None
