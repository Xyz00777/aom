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

import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Literal, Mapping

from ansible_aom.core._async_poll import is_async_poll_payload
from ansible_aom.core.timestamp import parse_iso_timestamp


@dataclass(frozen=True)
class StatusCounts:
    """Aggregate status tally over (task × host) pairs.

    Each ``v2_runner_on_*`` event contributes exactly one bump. A task
    that ran on three hosts with two OK + one failed adds ``ok=2,
    failed=1`` to its parent's totals.
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
                return replace(self, changed=self.changed + 1)
            return replace(self, ok=self.ok + 1)
        if event_type == "v2_runner_on_failed":
            return replace(self, failed=self.failed + 1)
        if event_type == "v2_runner_on_skipped":
            return replace(self, skipped=self.skipped + 1)
        if event_type == "v2_runner_on_unreachable":
            return replace(self, unreachable=self.unreachable + 1)
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

    The frozen ``StatusCounts.add_event`` goes through
    ``dataclasses.replace`` — ~7 µs per call, which is seconds of pure
    allocation churn when a session has hundreds of thousands of runner
    events. Builders accumulate on this plain-slots class and ``freeze()``
    to the public frozen type once per aggregate.
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


@dataclass(frozen=True)
class TaskTreeNode:
    """Hierarchical view of a session's tasks.

    Levels: run → play → group → task → host. ``group`` is the
    role-or-source bucket (see ``_group_key``); when a task has no
    natural grouping the bucket key is ``"_root"`` and renders as a
    flat list under the play.
    """

    kind: Literal["run", "play", "group", "task", "host"]
    label: str
    stats: StatusCounts = field(default_factory=StatusCounts)
    per_host: Mapping[str, StatusCounts] = field(default_factory=dict)
    children: tuple["TaskTreeNode", ...] = ()
    path: str | None = None
    duration: timedelta | None = None
    raw_event: dict | None = None
    task_id: str | None = None  # so the detail pane can fetch the underlying event


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
        return replace(
            directive,
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


def build_task_tree(session: dict) -> TaskTreeNode:
    """Build the hierarchical task tree for one session.

    Ansible's posix.jsonl emits ``v2_playbook_on_play_start`` only when
    the play opens; subsequent task/runner events do NOT carry the
    ``play`` key. We track the current play as a sliding window during
    iteration and attribute tasks/results to whatever play was last
    active. Same for task_start timestamps used for duration.
    """
    events = session.get("events", [])

    # Single linear pass: track current play / task contexts.
    play_order: list[tuple[str, str]] = []
    play_seen: set[str] = set()
    task_starts: dict[str, dict] = {}
    task_records: dict[str, dict] = {}
    task_order: list[str] = []

    current_pid: str = ""
    current_play_name: str = ""

    for event in events:
        et = event.get("_event", "")

        if et == "v2_playbook_on_play_start":
            play = event.get("play") or {}
            pid = str(play.get("id", ""))
            pname = str(play.get("name", "unnamed play"))
            if pid and pid not in play_seen:
                play_seen.add(pid)
                play_order.append((pid, pname))
            current_pid = pid
            current_play_name = pname
            continue

        if et == "v2_playbook_on_task_start":
            task_data = event.get("task")
            tid = str(task_data.get("id", "")) if isinstance(task_data, dict) else ""
            if tid:
                task_starts[tid] = event
            continue

        runner_et = _runner_event_type(event)
        if not runner_et:
            continue

        task = event.get("task")
        if not isinstance(task, dict):
            continue
        tid = str(task.get("id", ""))
        if not tid:
            continue
        # Prefer the current sliding-window play; fall back to anything
        # the event itself carries (older fixtures + future ansible
        # versions that might attach play to runner events).
        pid = current_pid
        if not pid:
            evt_play = event.get("play") or {}
            pid = str(evt_play.get("id", ""))
        if tid not in task_records:
            task_order.append(tid)
        rec = task_records.setdefault(
            tid,
            {
                "label": str(task.get("name") or "unnamed task"),
                "path": task.get("path"),
                "group": _group_key(task),
                "play_id": pid,
                "events": [],
            },
        )
        hosts = event.get("hosts") or {}
        for host, result in hosts.items():
            changed = bool(result.get("changed", False)) if isinstance(result, dict) else False
            rec["events"].append((runner_et, str(host), changed, event))

    # If no play_start events were captured but tasks exist, synthesise a
    # placeholder play so the tree still renders.
    if not play_order and task_records:
        play_order.append(("", current_play_name or "(no play header)"))

    task_start_ts: dict[str, datetime] = {}
    for tid, ts_event in task_starts.items():
        ts = _parse_iso(ts_event.get("_timestamp"))
        if ts is not None:
            task_start_ts[tid] = ts

    def _last_ts_for(tid: str) -> datetime | None:
        latest: datetime | None = None
        for _, _, _, e in task_records.get(tid, {}).get("events", []):
            ts = _parse_iso(e.get("_timestamp"))
            if ts is not None and (latest is None or ts > latest):
                latest = ts
        return latest

    # Build per-play, per-group structure preserving task insertion order.
    play_groups: dict[str, dict[str, list[TaskTreeNode]]] = {pid: {} for pid, _ in play_order}
    play_group_order: dict[str, list[str]] = {pid: [] for pid, _ in play_order}

    for tid in task_order:
        rec = task_records[tid]
        pid = rec["play_id"]
        if pid not in play_groups:
            # Task with no matching play_start — attribute to a synthetic
            # play so it still renders. Label intentionally indicates the
            # missing-header condition rather than "unknown" so users can
            # distinguish "ansible didn't emit play_start" from "we don't
            # know which play this belongs to".
            play_order.append((pid or "_orphans", "(orphan tasks)"))
            play_groups[pid or "_orphans"] = {}
            play_group_order[pid or "_orphans"] = []
            pid = pid or "_orphans"
        grp = rec["group"]
        # Aggregate stats across hosts.
        mut_task_counts = _MutCounts()
        mut_per_host: dict[str, _MutCounts] = {}
        for et, host, changed, _ in rec["events"]:
            mut_task_counts.add_event(et, changed=changed)
            current = mut_per_host.get(host)
            if current is None:
                current = mut_per_host[host] = _MutCounts()
            current.add_event(et, changed=changed)
        task_counts = mut_task_counts.freeze()
        per_host_counts = _freeze_map(mut_per_host)
        host_nodes: list[TaskTreeNode] = []
        for host, counts in per_host_counts.items():
            last_event: dict | None = None
            for et, h, _, e in rec["events"]:
                if h == host:
                    last_event = e
            host_nodes.append(
                TaskTreeNode(
                    kind="host",
                    label=host,
                    stats=counts,
                    raw_event=last_event,
                    task_id=tid,
                )
            )
        duration: timedelta | None = None
        start = task_start_ts.get(tid)
        last = _last_ts_for(tid)
        if start is not None and last is not None:
            duration = last - start
        task_node = TaskTreeNode(
            kind="task",
            label=rec["label"],
            stats=task_counts,
            per_host=per_host_counts,
            children=tuple(host_nodes),
            path=rec["path"],
            duration=duration,
            raw_event=rec["events"][-1][3] if rec["events"] else None,
            task_id=tid,
        )
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
        label=session.get("playbook", ""),
        stats=mut_run_stats.freeze(),
        per_host=_freeze_map(mut_run_per_host),
        children=tuple(play_nodes),
    )


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
    failed_items: tuple[LoopItem, ...]
    ok_items: tuple[LoopItem, ...]
    module_stdout: str | None
    module_stderr: str | None
    warnings: tuple[str, ...]
    raw_event: dict | None


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
        msg=msg if isinstance(msg, str) else None,
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


def _connection_ids_by_task_host(events: list[dict]) -> dict[tuple[str, str], str]:
    """Return the connection id for each (task_id, host) pair."""
    connections: dict[tuple[str, str], str] = {}
    for event in events:
        if event.get("_event") != "aom_connection_acquired":
            continue
        conn_id = event.get("connection_id")
        task_id = event.get("task_id") or event.get("task_uuid")
        host = event.get("host")
        if (
            not isinstance(conn_id, str)
            or not isinstance(task_id, str)
            or not isinstance(host, str)
        ):
            continue
        connections.setdefault((task_id, host), conn_id)
    return connections


def _connection_task_ids(events: list[dict]) -> dict[str, str]:
    """Return ``connection_id -> task_id`` mappings from connection events."""
    task_ids: dict[str, str] = {}
    for event in events:
        if event.get("_event") != "aom_connection_acquired":
            continue
        conn_id = event.get("connection_id")
        task_id = event.get("task_id") or event.get("task_uuid")
        if isinstance(conn_id, str) and isinstance(task_id, str):
            task_ids.setdefault(conn_id, task_id)
    return task_ids


def build_verbose_lines(
    session: dict,
    *,
    level: Literal["run", "play", "task"],
    play_name: str | None = None,
    task_id: str | None = None,
    host: str | None = None,
    play_task_ids: Mapping[str, set[str]] | None = None,
) -> tuple[str, ...]:
    """Build the verbose-panel body for one session and focus scope.

    Scope rules are explicit and deterministic:

    - ``run``: only ``aom_stderr_line`` events whose source is
      ``run_level``.
    - ``play``: run-level lines plus task-level lines whose connection
      maps to a task inside the selected play window.
    - ``task``: run-level lines plus task-level lines for the focused
      ``(task_id, host)`` connection.

    Ambiguous attribution is surfaced with a leading ``?``.

    ``play_task_ids`` is the ``play_name -> task_ids`` membership map from
    :func:`task_ids_by_play`. Pass it when a task tree already exists;
    when omitted it is derived here (rebuilding the tree, O(events)).
    """
    events = list(session.get("events", []))
    if not events:
        return ()

    if play_task_ids is None:
        play_task_ids = task_ids_by_play(build_task_tree(session))
    connection_task_ids = _connection_task_ids(events)
    connection_ids = _connection_ids_by_task_host(events)

    selected_connection_id: str | None = None
    if level == "task" and task_id and host:
        selected_connection_id = connection_ids.get((task_id, host))

    selected_play_task_ids = play_task_ids.get(play_name or "", set())

    lines: list[str] = []
    for event in events:
        if event.get("_event") != "aom_stderr_line":
            continue

        source = event.get("source")
        connection_id = event.get("connection_id")

        include = False
        if source == "run_level":
            include = True
        elif level == "play" and isinstance(connection_id, str):
            task_for_connection = connection_task_ids.get(connection_id)
            include = bool(task_for_connection and task_for_connection in selected_play_task_ids)
        elif level == "task" and isinstance(connection_id, str):
            include = connection_id == selected_connection_id

        if not include:
            continue

        line = str(event.get("line", ""))
        if event.get("attribution_confidence") == "ambiguous":
            line = f"? {line}"
        lines.append(line)

    return tuple(lines)
