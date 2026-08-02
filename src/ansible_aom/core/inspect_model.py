"""Pure builders over session dicts for the inspect TUI and text renderer.

This module owns the view logic that turns a session dict (as produced by
``core.session.load_session``) into the data structures the UI consumes:
``RunSummary`` (left pane), ``TaskTreeNode`` (middle pane), and
``DetailBlock`` (right pane).

The module is intentionally pure: it never reads from disk, never imports
Textual or Rich, and never mutates its inputs. The TUI and the text-mode
renderer both consume the same builders, which is what guarantees they
render the same information for the same session.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, Mapping, NamedTuple

from ansible_aom.core._async_poll import is_async_poll_payload
from ansible_aom.core.timestamp import parse_iso_timestamp


class StatusCounts(NamedTuple):
    """Aggregate status tally over (task × host) pairs.

    Each ``v2_runner_on_*`` event contributes exactly one bump. A task
    that ran on three hosts with two OK + one failed adds ``ok=2,
    failed=1`` to its parent's totals.

    NamedTuple rather than frozen dataclass: index-backed tree loads
    construct one per (task, host) row plus roll-ups — six-figure counts
    on large runs — and tuple construction is several times cheaper.
    """

    ok: int = 0
    changed: int = 0
    failed: int = 0
    skipped: int = 0
    unreachable: int = 0

    @property
    def total(self) -> int:
        return self.ok + self.changed + self.failed + self.skipped + self.unreachable

    def add_event(self, event_type: str, *, changed: bool) -> "StatusCounts":
        """Return a new StatusCounts with the bump for one runner event."""
        if event_type == "v2_runner_on_ok":
            if changed:
                return self._replace(changed=self.changed + 1)
            return self._replace(ok=self.ok + 1)
        if event_type == "v2_runner_on_failed":
            return self._replace(failed=self.failed + 1)
        if event_type == "v2_runner_on_skipped":
            return self._replace(skipped=self.skipped + 1)
        if event_type == "v2_runner_on_unreachable":
            return self._replace(unreachable=self.unreachable + 1)
        return self

    def merge(self, other: "StatusCounts") -> "StatusCounts":
        return StatusCounts(
            ok=self.ok + other.ok,
            changed=self.changed + other.changed,
            failed=self.failed + other.failed,
            skipped=self.skipped + other.skipped,
            unreachable=self.unreachable + other.unreachable,
        )

    def is_all_ok(self) -> bool:
        """True if no failure / unreachable. Skipped counts as OK for collapse decisions."""
        return self.failed == 0 and self.unreachable == 0


class _MutCounts:
    """Mutable accumulator behind ``StatusCounts``.

    ``StatusCounts.add_event`` allocates a new tuple per bump — pure
    churn when a session has hundreds of thousands of runner events.
    Builders accumulate on this plain-slots class and ``freeze()`` to
    the public immutable type once per aggregate.
    """

    __slots__ = ("ok", "changed", "failed", "skipped", "unreachable")

    def __init__(self) -> None:
        self.ok = 0
        self.changed = 0
        self.failed = 0
        self.skipped = 0
        self.unreachable = 0

    def add_event(self, event_type: str, *, changed: bool) -> None:
        if event_type == "v2_runner_on_ok":
            if changed:
                self.changed += 1
            else:
                self.ok += 1
        elif event_type == "v2_runner_on_failed":
            self.failed += 1
        elif event_type == "v2_runner_on_skipped":
            self.skipped += 1
        elif event_type == "v2_runner_on_unreachable":
            self.unreachable += 1

    def add_counts(self, other: "StatusCounts") -> None:
        self.ok += other.ok
        self.changed += other.changed
        self.failed += other.failed
        self.skipped += other.skipped
        self.unreachable += other.unreachable

    def freeze(self) -> StatusCounts:
        return StatusCounts(
            ok=self.ok,
            changed=self.changed,
            failed=self.failed,
            skipped=self.skipped,
            unreachable=self.unreachable,
        )


def _freeze_map(counts: dict[str, _MutCounts]) -> dict[str, StatusCounts]:
    return {key: mut.freeze() for key, mut in counts.items()}


@dataclass(frozen=True)
class RunSummary:
    """Per-session view consumed by the Runs pane and the text-mode header."""

    session_id: str
    short_id: str
    playbook: str
    start_time: datetime | None
    end_time: datetime | None
    duration: timedelta | None
    status: str  # "completed" | "failed" | "crashed" | "running"
    host_counts: Mapping[str, StatusCounts]
    failed_task_count: int


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return parse_iso_timestamp(value)


def build_run_summary(session: dict) -> RunSummary:
    """Derive a ``RunSummary`` from a session dict (output of ``load_session``)."""
    session_id = session.get("session_id", "")
    status = session.get("status") or ("running" if not session.get("end_time") else "unknown")
    start_time = _parse_iso(session.get("start_time"))
    end_time = _parse_iso(session.get("end_time"))
    duration_seconds = session.get("duration_seconds")
    duration = timedelta(seconds=duration_seconds) if duration_seconds is not None else None

    host_counts: dict[str, _MutCounts] = {}
    failed_task_ids: set[str] = set()

    for event in session.get("events", []):
        event_type = event.get("_event", "")
        if event_type not in (
            "v2_runner_on_ok",
            "v2_runner_on_failed",
            "v2_runner_on_skipped",
            "v2_runner_on_unreachable",
        ):
            continue
        hosts = event.get("hosts") or {}
        task_data = event.get("task")
        task_id = task_data.get("id", "") if isinstance(task_data, dict) else ""
        for host, result in hosts.items():
            changed = bool(result.get("changed", False)) if isinstance(result, dict) else False
            current = host_counts.get(host)
            if current is None:
                current = host_counts[host] = _MutCounts()
            current.add_event(event_type, changed=changed)
        if event_type == "v2_runner_on_failed" and task_id:
            failed_task_ids.add(task_id)

    return RunSummary(
        session_id=session_id,
        short_id=session_id[:8],
        playbook=session.get("playbook", ""),
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        status=status,
        host_counts=_freeze_map(host_counts),
        failed_task_count=len(failed_task_ids),
    )


def build_run_summaries(sessions: list[dict]) -> list[RunSummary]:
    """Map a list of session dicts to RunSummary, sorted newest-first by start_time.

    Sessions with no start_time sort to the end. Used by the Runs pane.
    """
    summaries = [build_run_summary(s) for s in sessions]
    summaries.sort(
        key=lambda s: s.start_time or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return summaries


class EventRef(NamedTuple):
    """Byte span of one event line inside ``events.jsonl``.

    The streaming loader records where each retained event lives instead
    of keeping the parsed dict — the detail pane seeks and re-parses the
    single line on demand, so memory stays bounded by tasks×hosts rather
    than payload bytes.
    """

    offset: int
    length: int


class TaskTreeNode(NamedTuple):
    """Hierarchical view of a session's tasks.

    Levels: run → play → group → task → host. ``group`` is the
    role-or-source bucket (see ``_group_key``); when a task has no
    natural grouping the bucket key is ``"_root"`` and renders as a
    flat list under the play.

    Exactly one of ``raw_event`` / ``raw_ref`` is set on task and host
    nodes (both ``None`` for structural nodes): the in-memory path keeps
    the event dict, the streaming path keeps only its byte span.

    NamedTuple for the same construction-cost reason as ``StatusCounts``
    — one node per (task, host) pair on index-backed loads. The shared
    ``{}`` default for ``per_host`` is safe because nodes are immutable
    by convention (mutate via ``_replace``).
    """

    kind: Literal["run", "play", "group", "task", "host"]
    label: str
    stats: StatusCounts = StatusCounts()
    per_host: Mapping[str, StatusCounts] = {}
    children: tuple["TaskTreeNode", ...] = ()
    path: str | None = None
    duration: timedelta | None = None
    raw_event: dict | None = None
    task_id: str | None = None  # so the detail pane can fetch the underlying event
    raw_ref: EventRef | None = None


_ROLE_PATH_RE = re.compile(r"roles/([^/]+)/")


def _group_key(task: dict) -> str:
    """Determine the grouping bucket for a task.

    Ansible's posix.jsonl callback does NOT include ``task.role`` on
    runner events even for tasks inside a role — the only reliable signal
    is the path. We look for ``roles/<name>/`` anywhere in the path
    (handles both relative and absolute paths). Top-level playbook tasks
    fall through to ``"_root"`` and render flat under the play.
    """
    role = task.get("role")
    if role:
        return str(role)
    path = task.get("path") or ""
    m = _ROLE_PATH_RE.search(path)
    if m:
        return m.group(1)
    return "_root"


def _path_file(path: str | None) -> str | None:
    """Return the file part of a ``task.path`` (``"file.yml:42"`` → ``"file.yml"``)."""
    if not path:
        return None
    return path.rsplit(":", 1)[0]


def _nest_includes(tasks: list[TaskTreeNode]) -> list[TaskTreeNode]:
    """Reconstruct ``include_tasks`` nesting from task ``path`` transitions.

    Ansible's ``posix.jsonl`` does not emit a usable include payload, but
    every task carries a ``task.path`` rooted in the file it lives in. Tasks
    execute depth-first, so a task whose file differs from the current file
    means we either descended into a freshly-included file (nest the new
    tasks under the directive that preceded them) or returned to an ancestor
    file (pop back to it). This rebuilds that hierarchy.

    *tasks* is the play's flat, execution-ordered task list. The returned
    list contains only the top-level (playbook-file) tasks; included tasks
    are attached as ``task``-kind children of the directive that pulled them
    in, after the directive's own ``host`` children. A directive's ``stats``
    / ``per_host`` are rolled up to include its nested descendants so
    failures deep in an include still surface on the collapsed directive row.

    Tasks with no path are treated as siblings at the current level.
    """
    if not tasks:
        return tasks

    # Each frame: file it represents, the directive node that opened it
    # (None for the root playbook frame), and the children accumulated so
    # far (already-finalised nodes for any sub-includes that have closed).
    @dataclass
    class _Frame:
        file: str | None
        directive: TaskTreeNode | None
        children: list[TaskTreeNode]

    def _finalise(frame: _Frame) -> TaskTreeNode:
        """Fold a closed include frame back into its directive node."""
        directive = frame.directive
        assert directive is not None  # root frame is never finalised
        stats = directive.stats
        per_host: dict[str, StatusCounts] = dict(directive.per_host)
        for child in frame.children:
            stats = stats.merge(child.stats)
            for host, counts in child.per_host.items():
                per_host[host] = per_host.get(host, StatusCounts()).merge(counts)
        return directive._replace(
            children=directive.children + tuple(frame.children),
            stats=stats,
            per_host=per_host,
        )

    root = _Frame(file=_path_file(tasks[0].path), directive=None, children=[])
    stack: list[_Frame] = [root]

    for task in tasks:
        file = _path_file(task.path)
        if file is None or file == stack[-1].file:
            stack[-1].children.append(task)
            continue

        ancestor_idx = next(
            (i for i in range(len(stack) - 1, -1, -1) if stack[i].file == file), None
        )
        if ancestor_idx is not None:
            # Returning to a file already open further up the stack: close
            # every frame below it, folding each into its parent's children.
            while len(stack) - 1 > ancestor_idx:
                closed = stack.pop()
                stack[-1].children[-1] = _finalise(closed)
            stack[-1].children.append(task)
            continue

        # Descending into a newly-included file. The directive that opened
        # it is the last task appended at the current level.
        if not stack[-1].children:
            stack[-1].children.append(task)  # no directive to nest under
            continue
        directive = stack[-1].children[-1]
        stack.append(_Frame(file=file, directive=directive, children=[task]))

    while len(stack) > 1:
        closed = stack.pop()
        stack[-1].children[-1] = _finalise(closed)
    return root.children


def _runner_event_type(event: dict) -> str | None:
    et = str(event.get("_event", ""))
    if et in (
        "v2_runner_on_ok",
        "v2_runner_on_failed",
        "v2_runner_on_skipped",
        "v2_runner_on_unreachable",
    ):
        return et
    return None


class StderrRow(NamedTuple):
    """One ``aom_stderr_line`` event, reduced to the fields verbose scoping needs.

    NamedTuple rather than dataclass: verbose runs carry hundreds of
    thousands of stderr lines and tuple construction is the accumulator's
    hottest allocation.
    """

    line: str
    source: str | None
    connection_id: str | None
    ambiguous: bool


class TaskHostRow(NamedTuple):
    """Aggregate for one (task, host) pair plus the last event seen for it."""

    host: str
    counts: StatusCounts
    raw_event: dict | None
    raw_ref: EventRef | None


@dataclass(frozen=True)
class TaskRow:
    """Aggregate for one task, hosts in first-event order."""

    task_id: str
    play_id: str
    name: str
    path: str | None
    group_key: str
    counts: StatusCounts
    hosts: tuple[TaskHostRow, ...]
    duration: timedelta | None
    raw_event: dict | None
    raw_ref: EventRef | None


@dataclass(frozen=True)
class PlayRow:
    play_id: str
    name: str


@dataclass(frozen=True)
class SessionIndex:
    """Everything the inspect views need, aggregated in one event pass.

    Bounded by tasks×hosts (+ stderr line count), never by payload
    bytes — large module outputs stay on disk behind ``EventRef``s when
    the accumulator is fed with refs.
    """

    plays: tuple[PlayRow, ...]
    tasks: tuple[TaskRow, ...]
    host_counts: Mapping[str, StatusCounts]
    failed_task_count: int
    stderr: tuple[StderrRow, ...]
    connections: Mapping[str, tuple[str, str]]  # connection_id -> (task_id, host)
    fallback_play_name: str


def stderr_row_from_event(event: dict) -> StderrRow:
    """Reduce an ``aom_stderr_line`` event to its verbose-scoping fields."""
    source = event.get("source")
    conn_id = event.get("connection_id")
    return StderrRow(
        str(event.get("line", "")),
        source if isinstance(source, str) else None,
        conn_id if isinstance(conn_id, str) else None,
        event.get("attribution_confidence") == "ambiguous",
    )


class _HostAcc:
    __slots__ = ("counts", "raw", "ref")

    def __init__(self) -> None:
        self.counts = _MutCounts()
        self.raw: dict | None = None
        self.ref: EventRef | None = None


class _TaskAcc:
    __slots__ = ("label", "path", "group", "play_id", "counts", "hosts", "raw", "ref", "last_ts")

    def __init__(self, label: str, path: str | None, group: str, play_id: str) -> None:
        self.label = label
        self.path = path
        self.group = group
        self.play_id = play_id
        self.counts = _MutCounts()
        self.hosts: dict[str, _HostAcc] = {}
        self.raw: dict | None = None
        self.ref: EventRef | None = None
        self.last_ts: datetime | None = None


class SessionIndexAccumulator:
    """Single-pass, constant-per-event aggregation over a session's events.

    ``feed`` each event in file order, then ``finish()`` for the
    ``SessionIndex``. Pass ``ref`` (the event's byte span in
    events.jsonl) to record a seekable reference instead of retaining
    the event dict — the streaming loader does this so memory does not
    scale with payload size. Without ``ref`` the dict is kept, matching
    the legacy in-memory behavior the TUI detail pane relies on.

    Ansible's posix.jsonl emits ``v2_playbook_on_play_start`` only when
    the play opens; subsequent task/runner events do NOT carry the
    ``play`` key. The current play is tracked as a sliding window and
    tasks are attributed to whatever play was last active. Same for
    task_start timestamps used for duration.
    """

    def __init__(self, *, collect_stderr: bool = True) -> None:
        # collect_stderr=False for consumers that persist stderr rows
        # elsewhere as they stream (the sqlite index builder) — verbose
        # runs carry 100k+ lines and holding them all is the single
        # biggest memory term.
        self._collect_stderr = collect_stderr
        self._plays: list[PlayRow] = []
        self._play_seen: set[str] = set()
        self._task_start_ts: dict[str, datetime] = {}
        self._tasks: dict[str, _TaskAcc] = {}
        self._host_counts: dict[str, _MutCounts] = {}
        self._failed_task_ids: set[str] = set()
        self._stderr: list[StderrRow] = []
        self._connections: dict[str, tuple[str, str]] = {}
        self._current_pid = ""
        self._current_play_name = ""

    def feed(self, event: dict, *, ref: EventRef | None = None) -> None:
        et = event.get("_event", "")

        if et == "v2_playbook_on_play_start":
            play = event.get("play") or {}
            pid = str(play.get("id", ""))
            pname = str(play.get("name", "unnamed play"))
            if pid and pid not in self._play_seen:
                self._play_seen.add(pid)
                self._plays.append(PlayRow(play_id=pid, name=pname))
            self._current_pid = pid
            self._current_play_name = pname
            return

        if et == "v2_playbook_on_task_start":
            task_data = event.get("task")
            tid = str(task_data.get("id", "")) if isinstance(task_data, dict) else ""
            if tid:
                ts = _parse_iso(event.get("_timestamp"))
                if ts is not None:
                    self._task_start_ts[tid] = ts
                elif tid in self._task_start_ts:
                    # A later start event without a parseable timestamp
                    # overrides an earlier one, like the dict-of-events
                    # implementation this replaced.
                    del self._task_start_ts[tid]
            return

        if et == "aom_connection_acquired":
            conn_id = event.get("connection_id")
            task_id = event.get("task_id") or event.get("task_uuid")
            host = event.get("host")
            if isinstance(conn_id, str) and isinstance(task_id, str):
                # First-wins per connection id. Verbose scoping relies on a
                # connection id never being reused for a second (task, host)
                # pair — guaranteed today because aom_connection derives the
                # id deterministically from (task_uuid, host).
                self._connections.setdefault(
                    conn_id, (task_id, host if isinstance(host, str) else "")
                )
            return

        if et == "aom_stderr_line":
            if self._collect_stderr:
                self._stderr.append(stderr_row_from_event(event))
            return

        runner_et = _runner_event_type(event)
        if not runner_et:
            return

        hosts = event.get("hosts") or {}
        task = event.get("task")
        tid = str(task.get("id", "")) if isinstance(task, dict) else ""

        # Run-level per-host tally counts every runner event, even ones
        # without a task id (matches build_run_summary's behavior).
        for host, result in hosts.items():
            changed = bool(result.get("changed", False)) if isinstance(result, dict) else False
            current = self._host_counts.get(host)
            if current is None:
                current = self._host_counts[host] = _MutCounts()
            current.add_event(runner_et, changed=changed)

        if runner_et == "v2_runner_on_failed" and tid:
            self._failed_task_ids.add(tid)

        if not isinstance(task, dict) or not tid:
            return

        rec = self._tasks.get(tid)
        if rec is None:
            # Prefer the current sliding-window play; fall back to anything
            # the event itself carries (older fixtures + future ansible
            # versions that might attach play to runner events).
            pid = self._current_pid
            if not pid:
                evt_play = event.get("play") or {}
                pid = str(evt_play.get("id", ""))
            rec = self._tasks[tid] = _TaskAcc(
                label=str(task.get("name") or "unnamed task"),
                path=task.get("path"),
                group=_group_key(task),
                play_id=pid,
            )

        # Duration counts per-host results only: an event with hosts:{}
        # carries no outcome and must not stretch the task's window
        # (matches the per-host-entry semantics of the pre-streaming
        # implementation).
        if hosts:
            event_ts = _parse_iso(event.get("_timestamp"))
            if event_ts is not None and (rec.last_ts is None or event_ts > rec.last_ts):
                rec.last_ts = event_ts

        raw = None if ref is not None else event
        for host, result in hosts.items():
            changed = bool(result.get("changed", False)) if isinstance(result, dict) else False
            host_key = str(host)
            hacc = rec.hosts.get(host_key)
            if hacc is None:
                hacc = rec.hosts[host_key] = _HostAcc()
            hacc.counts.add_event(runner_et, changed=changed)
            hacc.raw = raw
            hacc.ref = ref
            rec.counts.add_event(runner_et, changed=changed)
            rec.raw = raw
            rec.ref = ref

    def finish(self) -> SessionIndex:
        tasks: list[TaskRow] = []
        for tid, rec in self._tasks.items():
            duration: timedelta | None = None
            start = self._task_start_ts.get(tid)
            if start is not None and rec.last_ts is not None:
                duration = rec.last_ts - start
            tasks.append(
                TaskRow(
                    task_id=tid,
                    play_id=rec.play_id,
                    name=rec.label,
                    path=rec.path,
                    group_key=rec.group,
                    counts=rec.counts.freeze(),
                    hosts=tuple(
                        TaskHostRow(
                            host=host,
                            counts=hacc.counts.freeze(),
                            raw_event=hacc.raw,
                            raw_ref=hacc.ref,
                        )
                        for host, hacc in rec.hosts.items()
                    ),
                    duration=duration,
                    raw_event=rec.raw,
                    raw_ref=rec.ref,
                )
            )
        return SessionIndex(
            plays=tuple(self._plays),
            tasks=tuple(tasks),
            host_counts=_freeze_map(self._host_counts),
            failed_task_count=len(self._failed_task_ids),
            stderr=tuple(self._stderr),
            connections=dict(self._connections),
            fallback_play_name=self._current_play_name,
        )


def summary_from_index(index: SessionIndex, meta: Mapping) -> RunSummary:
    """Derive a ``RunSummary`` from a ``SessionIndex`` plus meta.json fields."""
    session_id = str(meta.get("session_id", ""))
    status = str(meta.get("status") or ("running" if not meta.get("end_time") else "unknown"))
    duration_seconds = meta.get("duration_seconds")
    return RunSummary(
        session_id=session_id,
        short_id=session_id[:8],
        playbook=str(meta.get("playbook", "")),
        start_time=_parse_iso(meta.get("start_time")),
        end_time=_parse_iso(meta.get("end_time")),
        duration=timedelta(seconds=duration_seconds) if duration_seconds is not None else None,
        status=status,
        host_counts=dict(index.host_counts),
        failed_task_count=index.failed_task_count,
    )


def tree_from_index(index: SessionIndex, *, playbook: str) -> TaskTreeNode:
    """Assemble the hierarchical task tree from a ``SessionIndex``."""
    play_order: list[tuple[str, str]] = [(p.play_id, p.name) for p in index.plays]

    # If no play_start events were captured but tasks exist, synthesise a
    # placeholder play so the tree still renders.
    if not play_order and index.tasks:
        play_order.append(("", index.fallback_play_name or "(no play header)"))

    # Build per-play, per-group structure preserving task insertion order.
    play_groups: dict[str, dict[str, list[TaskTreeNode]]] = {pid: {} for pid, _ in play_order}
    play_group_order: dict[str, list[str]] = {pid: [] for pid, _ in play_order}

    for row in index.tasks:
        pid = row.play_id
        if pid not in play_groups:
            # Task with no matching play_start — attribute to a synthetic
            # play so it still renders. Label intentionally indicates the
            # missing-header condition rather than "unknown" so users can
            # distinguish "ansible didn't emit play_start" from "we don't
            # know which play this belongs to". Normalise the key BEFORE
            # the membership re-check: with the raw ``""`` key, every
            # subsequent orphan re-created (and wiped) the synthetic play.
            pid = pid or "_orphans"
            if pid not in play_groups:
                play_order.append((pid, "(orphan tasks)"))
                play_groups[pid] = {}
                play_group_order[pid] = []
        per_host_counts = {h.host: h.counts for h in row.hosts}
        host_nodes = [
            TaskTreeNode(
                kind="host",
                label=h.host,
                stats=h.counts,
                raw_event=h.raw_event,
                task_id=row.task_id,
                raw_ref=h.raw_ref,
            )
            for h in row.hosts
        ]
        task_node = TaskTreeNode(
            kind="task",
            label=row.name,
            stats=row.counts,
            per_host=per_host_counts,
            children=tuple(host_nodes),
            path=row.path,
            duration=row.duration,
            raw_event=row.raw_event,
            task_id=row.task_id,
            raw_ref=row.raw_ref,
        )
        grp = row.group_key
        if grp not in play_groups[pid]:
            play_group_order[pid].append(grp)
            play_groups[pid][grp] = []
        play_groups[pid][grp].append(task_node)

    # Assemble groups into plays.
    play_nodes: list[TaskTreeNode] = []
    for pid, pname in play_order:
        groups = play_groups.get(pid, {})
        order = play_group_order.get(pid, [])
        group_nodes: list[TaskTreeNode] = []
        mut_play_stats = _MutCounts()
        mut_play_per_host: dict[str, _MutCounts] = {}
        for gkey in order:
            tasks = groups[gkey]
            mut_grp_stats = _MutCounts()
            mut_grp_per_host: dict[str, _MutCounts] = {}
            for t in tasks:
                mut_grp_stats.add_counts(t.stats)
                for host, counts in t.per_host.items():
                    current = mut_grp_per_host.get(host)
                    if current is None:
                        current = mut_grp_per_host[host] = _MutCounts()
                    current.add_counts(counts)
            mut_play_stats.add_counts(mut_grp_stats.freeze())
            grp_stats = mut_grp_stats.freeze()
            grp_per_host = _freeze_map(mut_grp_per_host)
            for host, counts in grp_per_host.items():
                current = mut_play_per_host.get(host)
                if current is None:
                    current = mut_play_per_host[host] = _MutCounts()
                current.add_counts(counts)
            if gkey == "_root":
                # Top-level (non-role) tasks may include dynamic
                # ``include_tasks``; reconstruct that nesting from paths.
                group_nodes.extend(_nest_includes(tasks))
            else:
                group_nodes.append(
                    TaskTreeNode(
                        kind="group",
                        label=gkey,
                        stats=grp_stats,
                        per_host=grp_per_host,
                        children=tuple(tasks),
                    )
                )
        play_nodes.append(
            TaskTreeNode(
                kind="play",
                label=pname,
                stats=mut_play_stats.freeze(),
                per_host=_freeze_map(mut_play_per_host),
                children=tuple(group_nodes),
            )
        )

    mut_run_stats = _MutCounts()
    mut_run_per_host: dict[str, _MutCounts] = {}
    for p in play_nodes:
        mut_run_stats.add_counts(p.stats)
        for host, counts in p.per_host.items():
            current = mut_run_per_host.get(host)
            if current is None:
                current = mut_run_per_host[host] = _MutCounts()
            current.add_counts(counts)

    return TaskTreeNode(
        kind="run",
        label=playbook,
        stats=mut_run_stats.freeze(),
        per_host=_freeze_map(mut_run_per_host),
        children=tuple(play_nodes),
    )


def accumulate_session_events(events: list[dict]) -> SessionIndex:
    """Fold an in-memory event list into a ``SessionIndex`` (no refs)."""
    acc = SessionIndexAccumulator()
    for event in events:
        acc.feed(event)
    return acc.finish()


def build_task_tree(session: dict) -> TaskTreeNode:
    """Build the hierarchical task tree for one session dict.

    In-memory convenience wrapper over ``SessionIndexAccumulator`` /
    ``tree_from_index`` — the streaming loader uses the same pair
    directly, so both paths aggregate identically by construction.
    """
    index = accumulate_session_events(session.get("events", []))
    return tree_from_index(index, playbook=session.get("playbook", ""))


@dataclass(frozen=True)
class LoopItem:
    """One entry from a task's loop ``results[]`` array."""

    label: str
    failed: bool
    changed: bool
    msg: str | None
    stderr: str | None


@dataclass(frozen=True)
class DetailBlock:
    """Right-pane data for a focused (task, host) pair.

    Everything here is *per task × host*. Session-wide info
    (``stderr.log``, overall stats) belongs elsewhere — including the
    session stderr in this block was confusing because it didn't change
    when navigating between tasks.
    """

    task_name: str
    file_line: str | None
    host: str | None
    duration: timedelta | None
    status: str  # "ok" | "changed" | "failed" | "skipped" | "unreachable"
    action: str | None  # the ansible module that ran (e.g. "command", "homebrew_cask")
    msg: str | None
    verbose_vars: tuple[tuple[str, str], ...]  # (key, rendered value), source order
    failed_items: tuple[LoopItem, ...]
    ok_items: tuple[LoopItem, ...]
    module_stdout: str | None
    module_stderr: str | None
    warnings: tuple[str, ...]
    raw_event: dict | None


# Keys of the standard ansible result envelope. Everything here is either
# rendered by its own section of the detail pane (``msg``, ``stdout``,
# ``warnings``, ``results``) or is bookkeeping the user did not ask to see
# (``rc``, ``delta``, ``invocation``). What remains on a verbose-always
# result is the payload ``debug: var=`` produced under the variable's own
# name — the only place that value exists in the JSONL.
_RESULT_ENVELOPE_KEYS = frozenset(
    {
        "action",
        "changed",
        "cmd",
        "delta",
        "deprecations",
        "end",
        "exception",
        "failed",
        "invocation",
        "item",
        "module_stderr",
        "module_stdout",
        "msg",
        "rc",
        "results",
        "skipped",
        "start",
        "stderr",
        "stderr_lines",
        "stdout",
        "stdout_lines",
        "warnings",
    }
)


def _render_value(value: object) -> str:
    """Render a result value for display: strings raw, everything else JSON.

    Strings pass through untouched so a multi-line ``msg`` reads as the
    lines the playbook author wrote rather than one escaped ``\\n`` blob —
    the exact thing that makes ansible's own default callback painful. Every
    other shape is pretty-printed JSON, which keeps a var's type visible
    (``"1"`` vs ``1``) — the reason someone reached for ``debug: var=`` in
    the first place.
    """
    if isinstance(value, str):
        return value
    return json.dumps(value, indent=2, ensure_ascii=False)


def _verbose_vars(host_data: dict) -> tuple[tuple[str, str], ...]:
    """Extract the ``debug: var=`` payload from a verbose-always result.

    Gated on the same flags as the compact view's inline body
    (``compact/format.py:_verbose_ok_body``): ``_ansible_verbose_always``
    marks a task whose purpose is to inform, and
    ``_ansible_verbose_override`` is ansible's opt-out. Without that gate
    every ``command`` result would spray its module fields into the pane.

    Order is the payload's own key order, so it matches the playbook.
    """
    if host_data.get("_ansible_verbose_always") is not True:
        return ()
    if host_data.get("_ansible_verbose_override") is True:
        return ()
    return tuple(
        (key, _render_value(value))
        for key, value in host_data.items()
        if not key.startswith("_") and key not in _RESULT_ENVELOPE_KEYS
    )


def _status_from_event_type(event_type: str, changed: bool) -> str:
    if event_type == "v2_runner_on_ok":
        return "changed" if changed else "ok"
    if event_type == "v2_runner_on_failed":
        return "failed"
    if event_type == "v2_runner_on_skipped":
        return "skipped"
    if event_type == "v2_runner_on_unreachable":
        return "unreachable"
    return "unknown"


def _make_loop_item(raw: dict) -> LoopItem:
    if is_async_poll_payload(raw):
        job_id = raw.get("ansible_job_id", "?")
        label = f"(async, job_id={job_id})"
    else:
        label = str(raw.get("_ansible_item_label") or raw.get("item") or "")
    return LoopItem(
        label=label,
        failed=bool(raw.get("failed", False)),
        changed=bool(raw.get("changed", False)),
        msg=raw.get("msg"),
        stderr=raw.get("stderr") or raw.get("module_stderr"),
    )


def build_detail_block(
    session: dict,
    task_node: TaskTreeNode,
    host_node: TaskTreeNode | None,
) -> DetailBlock:
    """Build the right-pane DetailBlock for a focused (task, host) pair.

    ``host_node`` may be None to aggregate over all hosts that ran the
    task. In aggregate mode the first failed host's event is used, falling
    back to any event.

    ``session`` is accepted for symmetry / future use but no longer read —
    everything in the block is per (task, host).
    """
    del session  # session-wide content lives elsewhere now

    raw_event: dict | None = None
    host_label: str | None = None
    if host_node is not None and host_node.kind == "host":
        host_label = host_node.label
        raw_event = host_node.raw_event
    else:
        raw_event = task_node.raw_event

    event_type = (raw_event or {}).get("_event", "")
    host_data: dict = {}
    if raw_event and host_label and host_label in (raw_event.get("hosts") or {}):
        host_data = raw_event["hosts"][host_label]
    elif raw_event:
        hosts = raw_event.get("hosts") or {}
        if hosts:
            host_label = host_label or next(iter(hosts))
            host_data = hosts.get(host_label, {})

    changed = bool(host_data.get("changed", False))
    status = _status_from_event_type(event_type, changed)
    msg = host_data.get("msg")
    action = host_data.get("action") or host_data.get("invocation", {}).get("module_name")

    failed_items: list[LoopItem] = []
    ok_items: list[LoopItem] = []
    for raw in host_data.get("results") or []:
        if not isinstance(raw, dict):
            continue
        item = _make_loop_item(raw)
        (failed_items if item.failed else ok_items).append(item)

    warnings_raw = host_data.get("warnings") or []
    warnings = tuple(str(w) for w in warnings_raw if isinstance(w, (str, bytes)))

    return DetailBlock(
        task_name=task_node.label,
        file_line=task_node.path,
        host=host_label,
        duration=task_node.duration,
        status=status,
        action=str(action) if action else None,
        # A YAML-list ``msg:`` is a list, not a str — rendering it rather
        # than dropping it is why this goes through _render_value.
        msg=None if msg is None else _render_value(msg),
        verbose_vars=_verbose_vars(host_data),
        failed_items=tuple(failed_items),
        ok_items=tuple(ok_items),
        module_stdout=host_data.get("stdout"),
        module_stderr=host_data.get("stderr") or host_data.get("module_stderr"),
        warnings=warnings,
        raw_event=raw_event,
    )


def task_ids_by_play(tree: TaskTreeNode) -> dict[str, set[str]]:
    """Return ``play_name -> task_id`` membership from an already-built tree.

    Callers that hold a tree (the TUI keeps one per selected session, the
    text renderer builds one for the failures section) pass this map to
    :func:`build_verbose_lines` so it doesn't rebuild the tree — a full
    O(events) pass on every verbose render.
    """
    memberships: dict[str, set[str]] = {}

    for play in tree.children:
        task_ids: set[str] = set()
        stack = list(play.children)
        while stack:
            node = stack.pop()
            if node.kind == "task" and node.task_id:
                task_ids.add(node.task_id)
            stack.extend(node.children)
        memberships.setdefault(play.label, set()).update(task_ids)

    return memberships


def verbose_lines_from_rows(
    stderr: tuple[StderrRow, ...],
    connections: Mapping[str, tuple[str, str]],
    *,
    level: Literal["run", "play", "task"],
    play_task_ids: Mapping[str, set[str]],
    play_name: str | None = None,
    task_id: str | None = None,
    host: str | None = None,
) -> tuple[str, ...]:
    """Scope verbose rows to a focus level.

    Shared by the in-memory path (:func:`build_verbose_lines`) and the
    sqlite-index path so both filter identically.

    Scope rules are explicit and deterministic:

    - ``run``: only rows whose source is ``run_level``.
    - ``play``: run-level rows plus rows whose connection maps to a task
      inside the selected play window.
    - ``task``: run-level rows plus rows for the focused
      ``(task_id, host)`` connection.

    Ambiguous attribution is surfaced with a leading ``?``.
    """
    selected_connection_id: str | None = None
    if level == "task" and task_id and host:
        # First acquisition for the (task, host) pair wins — connections
        # preserves acquisition order with first-wins per connection id.
        for conn_id, (conn_task, conn_host) in connections.items():
            if conn_task == task_id and conn_host == host:
                selected_connection_id = conn_id
                break

    selected_play_task_ids = play_task_ids.get(play_name or "", set())

    lines: list[str] = []
    for row in stderr:
        include = False
        if row.source == "run_level":
            include = True
        elif level == "play" and row.connection_id is not None:
            mapped = connections.get(row.connection_id)
            include = bool(mapped and mapped[0] in selected_play_task_ids)
        elif level == "task" and row.connection_id is not None:
            include = row.connection_id == selected_connection_id

        if include:
            lines.append(f"? {row.line}" if row.ambiguous else row.line)

    return tuple(lines)


def build_verbose_lines(
    session: dict,
    *,
    level: Literal["run", "play", "task"],
    play_name: str | None = None,
    task_id: str | None = None,
    host: str | None = None,
    play_task_ids: Mapping[str, set[str]] | None = None,
) -> tuple[str, ...]:
    """Build the verbose-panel body for one session dict and focus scope.

    In-memory wrapper over :func:`verbose_lines_from_rows` — see there
    for the scope rules.

    ``play_task_ids`` is the ``play_name -> task_ids`` membership map from
    :func:`task_ids_by_play`. Pass it when a task tree already exists;
    when omitted it is derived here (rebuilding the tree, O(events)).
    """
    events = list(session.get("events", []))
    if not events:
        return ()

    index = accumulate_session_events(events)
    if play_task_ids is None:
        play_task_ids = task_ids_by_play(tree_from_index(index, playbook=""))

    return verbose_lines_from_rows(
        index.stderr,
        index.connections,
        level=level,
        play_task_ids=play_task_ids,
        play_name=play_name,
        task_id=task_id,
        host=host,
    )
