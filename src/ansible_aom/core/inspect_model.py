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
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_run_summary(session: dict) -> RunSummary:
    """Derive a ``RunSummary`` from a session dict (output of ``load_session``)."""
    session_id = session.get("session_id", "")
    status = session.get("status") or ("running" if not session.get("end_time") else "unknown")
    start_time = _parse_iso(session.get("start_time"))
    end_time = _parse_iso(session.get("end_time"))
    duration_seconds = session.get("duration_seconds")
    duration = timedelta(seconds=duration_seconds) if duration_seconds is not None else None

    host_counts: dict[str, StatusCounts] = {}
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
        task_id = (event.get("task") or {}).get("id", "")
        for host, result in hosts.items():
            changed = bool(result.get("changed", False)) if isinstance(result, dict) else False
            current = host_counts.get(host, StatusCounts())
            host_counts[host] = current.add_event(event_type, changed=changed)
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
        host_counts=host_counts,
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
            tid = str((event.get("task") or {}).get("id", ""))
            if tid:
                task_starts[tid] = event
            continue

        runner_et = _runner_event_type(event)
        if not runner_et:
            continue

        task = event.get("task") or {}
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
        task_counts = StatusCounts()
        per_host_counts: dict[str, StatusCounts] = {}
        for et, host, changed, _ in rec["events"]:
            task_counts = task_counts.add_event(et, changed=changed)
            per_host_counts[host] = per_host_counts.get(host, StatusCounts()).add_event(
                et, changed=changed
            )
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
        play_stats = StatusCounts()
        play_per_host: dict[str, StatusCounts] = {}
        for gkey in order:
            tasks = groups[gkey]
            grp_stats = StatusCounts()
            grp_per_host: dict[str, StatusCounts] = {}
            for t in tasks:
                grp_stats = grp_stats.merge(t.stats)
                for host, counts in t.per_host.items():
                    grp_per_host[host] = grp_per_host.get(host, StatusCounts()).merge(counts)
            play_stats = play_stats.merge(grp_stats)
            for host, counts in grp_per_host.items():
                play_per_host[host] = play_per_host.get(host, StatusCounts()).merge(counts)
            if gkey == "_root":
                group_nodes.extend(tasks)
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
                stats=play_stats,
                per_host=play_per_host,
                children=tuple(group_nodes),
            )
        )

    run_stats = StatusCounts()
    run_per_host: dict[str, StatusCounts] = {}
    for p in play_nodes:
        run_stats = run_stats.merge(p.stats)
        for host, counts in p.per_host.items():
            run_per_host[host] = run_per_host.get(host, StatusCounts()).merge(counts)

    return TaskTreeNode(
        kind="run",
        label=session.get("playbook", ""),
        stats=run_stats,
        per_host=run_per_host,
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
    """Right-pane data for a focused (task, host) pair."""

    task_name: str
    file_line: str | None
    host: str | None
    duration: timedelta | None
    status: str  # "ok" | "changed" | "failed" | "skipped" | "unreachable"
    msg: str | None
    failed_items: tuple[LoopItem, ...]
    ok_items: tuple[LoopItem, ...]
    module_stdout: str | None
    module_stderr: str | None
    session_stderr_tail: tuple[str, ...]
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
    *,
    stderr_tail_lines: int = 20,
) -> DetailBlock:
    """Build the right-pane DetailBlock for a focused (task, host) pair.

    ``host_node`` may be None to aggregate over all hosts that ran the
    task. In aggregate mode the first failed host's event is used, falling
    back to any event.
    """
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

    failed_items: list[LoopItem] = []
    ok_items: list[LoopItem] = []
    for raw in host_data.get("results") or []:
        if not isinstance(raw, dict):
            continue
        item = _make_loop_item(raw)
        (failed_items if item.failed else ok_items).append(item)

    stderr_lines = session.get("stderr") or []
    tail = tuple(stderr_lines[-stderr_tail_lines:])

    return DetailBlock(
        task_name=task_node.label,
        file_line=task_node.path,
        host=host_label,
        duration=task_node.duration,
        status=status,
        msg=msg if isinstance(msg, str) else None,
        failed_items=tuple(failed_items),
        ok_items=tuple(ok_items),
        module_stdout=host_data.get("stdout"),
        module_stderr=host_data.get("stderr") or host_data.get("module_stderr"),
        session_stderr_tail=tail,
        raw_event=raw_event,
    )
