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
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal, Mapping

from ansible_aom.core.inspect_model import (
    EventRef,
    PlayRow,
    RunSummary,
    SessionIndex,
    SessionIndexAccumulator,
    StatusCounts,
    StderrRow,
    TaskHostRow,
    TaskRow,
    TaskTreeNode,
    summary_from_index,
    task_ids_by_play,
    tree_from_index,
    verbose_lines_from_rows,
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


def _events_stat(session_path: Path) -> tuple[int, int] | None:
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
    stat = _events_stat(session_path)
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


def build_index(session_path: Path) -> bool:
    """Stream events.jsonl into a fresh index.db. Returns False when the
    session has no events file; sqlite/OS errors also return False (the
    index is an optimization — callers fall back to the slow path)."""
    events_path = _events_path(session_path)
    # Stat BEFORE parsing: if the file grows while we read (running
    # session), the recorded size is smaller than reality and the index
    # correctly reads as stale on the next freshness check.
    stat = _events_stat(session_path)
    if stat is None:
        return False

    acc = SessionIndexAccumulator()
    malformed = 0
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
                    if isinstance(event, dict):
                        acc.feed(event, ref=EventRef(offset=offset, length=length))
                    else:
                        malformed += 1
            offset += length
    index = acc.finish()

    tmp_path = index_path(session_path).with_suffix(".db.tmp")
    try:
        tmp_path.unlink(missing_ok=True)
        conn = sqlite3.connect(tmp_path)
        try:
            _write_index_db(conn, index, events_stat=stat, malformed=malformed)
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
    conn.executescript(_SCHEMA)
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
        "INSERT INTO stderr VALUES (?, ?, ?, ?, ?)",
        [
            (seq, r.line, r.source, r.connection_id, int(r.ambiguous))
            for seq, r in enumerate(index.stderr)
        ],
    )
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


def load_structure(session_path: Path) -> SessionIndex | None:
    """Load plays/tasks/hosts aggregates from index.db (no verbose rows).

    Verbose rows can number in the hundreds of thousands; they load
    on demand via :func:`query_verbose` instead of with the structure.
    Returns None when the index is missing or unreadable.
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
        hosts_by_task: dict[int, list[TaskHostRow]] = {}
        for row in conn.execute(
            "SELECT task_seq, host, ok, changed, failed, skipped, unreachable,"
            " ref_offset, ref_length FROM task_hosts ORDER BY task_seq, seq"
        ):
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


def load_tree(session_path: Path, *, playbook: str) -> TaskTreeNode | None:
    """Assemble the task tree from index.db. None when no readable index."""
    index = load_structure(session_path)
    if index is None:
        return None
    return tree_from_index(index, playbook=playbook)


def load_summary(session_path: Path, meta: Mapping) -> RunSummary | None:
    """Build a RunSummary from index.db aggregates plus meta.json fields."""
    index = load_structure(session_path)
    if index is None:
        return None
    return summary_from_index(index, meta)


def _load_verbose_rows(
    session_path: Path,
) -> tuple[tuple[StderrRow, ...], dict[str, tuple[str, str]]] | None:
    db_path = index_path(session_path)
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        stderr = tuple(
            StderrRow(row[0], row[1], row[2], bool(row[3]))
            for row in conn.execute(
                "SELECT line, source, connection_id, ambiguous FROM stderr ORDER BY seq"
            )
        )
        connections = {
            row[0]: (row[1], row[2])
            for row in conn.execute(
                "SELECT connection_id, task_id, host FROM connections ORDER BY rowid"
            )
        }
    except sqlite3.Error:
        return None
    finally:
        conn.close()
    return stderr, connections


def query_verbose(
    session_path: Path,
    *,
    tree: TaskTreeNode,
    level: Literal["run", "play", "task"],
    play_name: str | None = None,
    task_id: str | None = None,
    host: str | None = None,
) -> tuple[str, ...]:
    """Verbose lines for a focus scope, read from index.db.

    Delegates the scoping decision to the same core function the
    in-memory path uses, so both stay in lockstep.
    """
    rows = _load_verbose_rows(session_path)
    if rows is None:
        return ()
    stderr, connections = rows
    return verbose_lines_from_rows(
        stderr,
        connections,
        level=level,
        play_task_ids=task_ids_by_play(tree),
        play_name=play_name,
        task_id=task_id,
        host=host,
    )


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
