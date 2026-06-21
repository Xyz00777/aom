"""Data models for AOM.

This module defines the dual-track architecture:
- Definition classes (immutable, from --list-tasks)
- State classes (mutable, from JSONL events)

See SPECIFICATION.md Section 6.1 for model definitions.
"""

import logging
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, cast

logger = logging.getLogger(__name__)

_JINJA_RE = re.compile(r"\{\{.*?\}\}")


def strip_role_prefix(name: str) -> str:
    """Strip the ``"role : "`` prefix that ansible adds to task names at
    runtime. Preflight definitions already have this stripped (by
    ``parse_list_tasks_output``), so ``TaskDefinition.name`` never contains
    it. ``TaskRunState.name`` does. Callers that match runtime names to
    preflight names should use this to normalise the lookup key."""
    if " : " in name:
        _, stripped = name.split(" : ", 1)
        return stripped.strip()
    return name


class Status(Enum):
    """Task/host execution status."""

    PENDING = "pending"
    RUNNING = "running"
    OK = "ok"
    CHANGED = "changed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNREACHABLE = "unreachable"
    COMPLETED = "completed"


class WarningType(Enum):
    """Warning classification type."""

    WARNING = "warning"
    DEPRECATION = "deprecation"


@dataclass
class WarningEntry:
    """A classified warning or deprecation from the PTY stream."""

    type: WarningType
    message: str
    timestamp: datetime | None = None
    source: str = ""


@dataclass
class TaskDefinition:
    """Static task info from --list-tasks (Definition class)."""

    name: str
    role: str | None
    tags: list[str]
    play_id: str
    play_order: int
    task_order: int
    is_dynamic: bool = False
    uuid: str | None = None
    path: str | None = None
    children: list["TaskDefinition"] = field(default_factory=list)


@dataclass
class RoleGroupDefinition:
    """Grouped role tasks when 5+ consecutive tasks share same role."""

    role: str
    tasks: list[TaskDefinition]

    @property
    def name(self) -> str:
        return f"Role: {self.role} ({len(self.tasks)} tasks)"


def _iter_task_def_tree(task_def: TaskDefinition) -> Iterator[TaskDefinition]:
    """Yield a TaskDefinition and all nested TaskDefinition.children in order."""
    yield task_def
    for child in task_def.children:
        yield from _iter_task_def_tree(child)


def iter_preflight_task_defs(
    entries: Sequence[TaskDefinition | RoleGroupDefinition], inherited_role: str | None = None
) -> Iterator[tuple[TaskDefinition, str | None]]:
    """Yield preflight task definitions in display order with effective role context.

    Walks ``RoleGroupDefinition.tasks`` and nested ``TaskDefinition.children`` recursively,
    preserving the pre-order tree traversal used by indexing and rendering.
    """
    for entry in entries:
        if isinstance(entry, RoleGroupDefinition):
            yield from iter_preflight_task_defs(entry.tasks, inherited_role=entry.role)
            continue

        role = entry.role if entry.role is not None else inherited_role
        yield entry, role
        if entry.children:
            yield from iter_preflight_task_defs(entry.children, inherited_role=role)


@dataclass
class PlayDefinition:
    """Static play info from --list-tasks and --list-hosts (Definition class)."""

    id: str
    name: str
    hosts: str
    resolved_hosts: list[str] = field(default_factory=list)
    tasks: list[TaskDefinition | RoleGroupDefinition] = field(default_factory=list)


@dataclass
class HostRunState:
    """Runtime state for a task execution on a host (State class)."""

    hostname: str
    status: Status
    changed: bool = False
    message: str = ""
    start_time: datetime | None = None
    end_time: datetime | None = None
    # Number of loop items this host has completed so far, tallied live
    # from ``v2_runner_item_on_*`` events. Drives the tree row's
    # ``(N items)`` progress hint while the loop runs. Reset to a fresh
    # HostRunState (count 0) when the aggregate terminal event lands.
    loop_items_done: int = 0


@dataclass
class TaskRunState:
    """Runtime state for a task execution (State class)."""

    task_id: str
    name: str
    status: Status = Status.PENDING
    hosts: dict[str, HostRunState] = field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None
    path: str | None = None


@dataclass
class PlayRunState:
    """Runtime state for a play execution (State class)."""

    play_id: str
    name: str
    status: Status = Status.PENDING
    tasks: dict[str, TaskRunState] = field(default_factory=dict)
    detected_strategy: str | None = None
    window_start: str | None = None
    window_ordinal: int = 0


def _parse_timestamp(event: dict[str, Any]) -> datetime:
    """Parse timestamp from event, defaulting to current time."""
    ts_str = event.get("_timestamp")
    if not ts_str:
        return datetime.now(timezone.utc)
    try:
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.fromisoformat(ts_str)
    except ValueError, TypeError:
        return datetime.now(timezone.utc)


def _parse_play_window_start(play_data: dict[str, Any]) -> str | None:
    """Extract the window discriminator from ``play.duration.start`` if present."""
    duration = play_data.get("duration")
    if not isinstance(duration, dict):
        return None
    window_start = duration.get("start")
    return window_start if isinstance(window_start, str) else None


def _iter_leaf_task_defs(plays: list["PlayDefinition"]) -> "list[TaskDefinition]":
    """Flatten preflight definitions into the leaf TaskDefinitions visible by name.

    ``RoleGroupDefinition`` is unwrapped so its inner tasks are reachable; nested
    ``TaskDefinition.children`` are also traversed so recursive include/import
    expansions are visible to the grafting logic.
    """
    leaves: list[TaskDefinition] = []
    for play in plays:
        for entry in play.tasks:
            if isinstance(entry, RoleGroupDefinition):
                for task_def in entry.tasks:
                    leaves.extend(_iter_task_def_tree(task_def))
            else:
                leaves.extend(_iter_task_def_tree(entry))
    return leaves


def count_leaf_tasks(plays: list["PlayDefinition"]) -> int:
    """Total number of leaf TaskDefinitions across all preflight plays.

    Shared by infrastructure callers that need a task count without
    materialising the list (the runner persisting ``preflight_task_count``
    to ``meta.json``, the compact renderer's status-bar denominator, …).
    Lives in ``core/`` so layering rules (no infra-to-infra imports) are
    satisfied with one definition.
    """
    return len(_iter_leaf_task_defs(plays))


@dataclass
class IncludeCacheEntry:
    """Cached parsing result for an ``include_tasks`` file.

    ``--list-tasks`` does not expand ``include_tasks`` (only
    ``import_tasks``), so dynamic includes are discovered at runtime via
    the ``task.path`` field in JSONL events. This cache avoids re-parsing
    the same file each time it is included.
    """

    path: str
    task_names: list[str]
    role: str | None
    parsed_at: datetime

    @property
    def task_count(self) -> int:
        """Pre-computed count for O(1) access in counter hot paths."""
        return len(self.task_names)


@dataclass
class RoleCacheEntry:
    """Cached task list for a role discovered at runtime.

    When a role is applied dynamically (e.g. via ``include_role``), its
    tasks are not known from preflight ``--list-tasks``. This entry
    records the tasks observed at runtime so they can be re-used if the
    same role is included again.
    """

    role_name: str
    task_names: list[str]

    @property
    def task_count(self) -> int:
        """Pre-computed count for O(1) access in counter hot paths."""
        return len(self.task_names)


@dataclass
class RunState:
    """Complete execution state (State class)."""

    playbook: str
    plays: dict[str, PlayRunState] = field(default_factory=dict)
    definitions: list[PlayDefinition] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: Status = Status.PENDING
    _current_play_id: str | None = field(default=None, init=False, repr=False)
    _last_matched_task_def: "TaskDefinition | None" = field(default=None, init=False, repr=False)
    _grafted_uuids: set[str] = field(default_factory=set, init=False, repr=False)
    # R5: count unknown _event values so the renderer can surface a
    # one-line "(N unknown events: foo×3)" hint at completion. Events
    # with no _event field at all are degenerate (not "future-version
    # drift") and aren't counted here.
    unknown_events: dict[str, int] = field(default_factory=dict)
    # Loop item totals from a matching prior run: ``{task.path: {host:
    # item_count}}``. Injected via the renderer's ``set_prior_run`` so the
    # tree can show ``N/total`` while a loop runs. Empty when there is no
    # prior run (live count falls back to a bare ``(N items)``). This is
    # reference data, not execution state — it is never mutated by events.
    loop_totals: dict[str, dict[str, int]] = field(default_factory=dict)
    # HS-5/HS-6: name → definition lookup dicts, built once when
    # ``definitions`` is assigned. They replace the per-event linear
    # scans in ``_graft_or_match_task`` and ``_resolve_play_hosts``.
    # Marked as Optional and rebuilt via __setattr__ so reassignment of
    # ``definitions`` (e.g. across replay invocations) refreshes both.
    _task_def_index: dict[str, "TaskDefinition"] | None = field(
        default=None, init=False, repr=False
    )
    _task_def_by_path: dict[str, "TaskDefinition"] | None = field(
        default=None, init=False, repr=False
    )
    _play_def_by_id: dict[str, PlayDefinition] | None = field(default=None, init=False, repr=False)
    _play_def_by_name: dict[str, PlayDefinition] | None = field(
        default=None, init=False, repr=False
    )
    _include_cache: dict[str, "IncludeCacheEntry"] = field(
        default_factory=dict, init=False, repr=False
    )
    _role_cache: dict[str, "RoleCacheEntry"] = field(default_factory=dict, init=False, repr=False)
    _play_window_counts: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _tree_revision: int = field(default=0, init=False, repr=False)

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        # Rebuild the lookup dicts whenever ``definitions`` is (re)assigned.
        # Cheap: O(P_def + T_def), happens once per run after preflight.
        if name == "definitions":
            self._rebuild_definition_indexes()
            self._bump_tree_revision()

    def _bump_tree_revision(self) -> None:
        """Advance the private tree-shape revision counter.

        TreeProjection instances use this to refresh any caches derived
        from ``definitions`` without being recreated on every event.
        """
        super().__setattr__("_tree_revision", getattr(self, "_tree_revision", 0) + 1)

    def _rebuild_definition_indexes(self) -> None:
        """(Re)populate the definition lookup indexes.

        Called whenever ``definitions`` is reassigned. Empty definitions
        produce empty dicts (not ``None``) so the lookup paths never need
        a None-check.
        """
        task_index: dict[str, TaskDefinition] = {}
        task_index_by_path: dict[str, TaskDefinition] = {}
        for leaf in _iter_leaf_task_defs(self.definitions):
            # First-write wins — matches the prior linear scan's behaviour
            # of returning the first match for duplicate names.
            task_index.setdefault(leaf.name, leaf)
            if leaf.path is not None:
                task_index_by_path.setdefault(leaf.path, leaf)
        super().__setattr__("_task_def_index", task_index)
        super().__setattr__("_task_def_by_path", task_index_by_path)

        play_index_by_id: dict[str, PlayDefinition] = {}
        play_index_by_name: dict[str, PlayDefinition] = {}
        for play_def in self.definitions:
            if play_def.id:
                play_index_by_id.setdefault(play_def.id, play_def)
            play_index_by_name.setdefault(play_def.name.strip(), play_def)
        super().__setattr__("_play_def_by_id", play_index_by_id)
        super().__setattr__("_play_def_by_name", play_index_by_name)

    def handle_event(self, event: dict[str, Any]) -> None:
        """Process a JSONL event and update state."""
        event_type = event.get("_event", "")
        ts = _parse_timestamp(event)

        handler_map = {
            "v2_playbook_on_start": self._handle_v2_playbook_on_start,
            "v2_playbook_on_play_start": self._handle_v2_playbook_on_play_start,
            "v2_playbook_on_task_start": self._handle_v2_playbook_on_task_start,
            "v2_playbook_on_handler_task_start": self._handle_v2_playbook_on_handler_task_start,
            "v2_runner_on_start": self._handle_v2_runner_on_start,
            "v2_runner_on_ok": self._handle_v2_runner_on_ok,
            "v2_runner_on_failed": self._handle_v2_runner_on_failed,
            "v2_runner_on_skipped": self._handle_v2_runner_on_skipped,
            "v2_runner_on_unreachable": self._handle_v2_runner_on_unreachable,
            "v2_runner_item_on_ok": self._handle_v2_runner_item_on,
            "v2_runner_item_on_failed": self._handle_v2_runner_item_on,
            "v2_runner_item_on_skipped": self._handle_v2_runner_item_on,
            "v2_playbook_on_stats": self._handle_v2_playbook_on_stats,
        }

        handler = handler_map.get(event_type)
        if handler:
            handler(event, ts)
        elif event_type:
            self.unknown_events[event_type] = self.unknown_events.get(event_type, 0) + 1
            logger.debug(f"Unknown event type: {event_type}")

    def _handle_v2_playbook_on_start(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_playbook_on_start event."""
        if self.start_time is None:
            self.start_time = ts
            self.status = Status.RUNNING

    def _finalize_play(self, play: "PlayRunState", ts: datetime) -> None:
        """Force-complete a play whose work is definitively done.

        Any host still marked RUNNING is transitioned to OK (with an
        ``end_time``); any RUNNING task becomes COMPLETED. Used when a
        boundary proves the play is over but a terminal event never
        arrived — notably ``ansible.builtin.pause``, which emits no
        ``v2_runner_on_ok``, so without this its host lingers as
        ``(1 running)`` in the tree for the rest of the run. Hosts that
        already hold a terminal status (OK/CHANGED/FAILED/…) are left
        untouched.
        """
        for task in play.tasks.values():
            for hostname in list(task.hosts):
                hs = task.hosts[hostname]
                if hs.status == Status.RUNNING:
                    task.hosts[hostname] = HostRunState(
                        hostname=hostname,
                        status=Status.OK,
                        changed=False,
                        start_time=hs.start_time,
                        end_time=ts,
                    )
            if task.status == Status.RUNNING:
                task.status = Status.COMPLETED

    def _handle_v2_playbook_on_play_start(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_playbook_on_play_start event."""
        play_data = event.get("play", {})
        play_id = play_data.get("id", "")
        play_name = play_data.get("name", "").strip()
        play_window_start = _parse_play_window_start(play_data)
        play_window_ordinal = self._play_window_counts.get(play_id, 0)

        # A new play starting is definitive proof that every prior play is
        # done — ansible runs plays sequentially. Finalise prior plays now
        # so a pause (or any action with no terminal event) that was the
        # last task of its play doesn't stay RUNNING in the tree. Skip the
        # same play_id (serial batches re-emit play_start for one play and
        # the entry is replaced below anyway).
        for prior_id, prior in self.plays.items():
            if prior_id == play_id:
                continue
            self._finalize_play(prior, ts)
            if prior.status == Status.RUNNING:
                prior.status = Status.COMPLETED

        self._current_play_id = play_id
        self._play_window_counts[play_id] = play_window_ordinal + 1

        if self.start_time is None:
            self.start_time = ts
            self.status = Status.RUNNING

        if play_id in self.plays:
            existing = self.plays[play_id]
            existing.name = play_name
            existing.status = Status.RUNNING
            existing.window_start = play_window_start
            existing.window_ordinal = play_window_ordinal
            self._finalize_play(existing, ts)
            for task in existing.tasks.values():
                if task.status == Status.COMPLETED:
                    task.hosts.clear()
        else:
            self.plays[play_id] = PlayRunState(
                play_id=play_id,
                name=play_name,
                status=Status.RUNNING,
                window_start=play_window_start,
                window_ordinal=play_window_ordinal,
            )

    def _resolve_play_id(self, event: dict[str, Any]) -> str:
        """Resolve play_id from event or _current_play_id.

        ansible-core >=2.20 omits the 'play' field from runner/task events,
        so we fall back to the play_id tracked from the most recent
        v2_playbook_on_play_start event.
        """
        play_data = event.get("play")
        if play_data and isinstance(play_data, dict):
            return cast(str, play_data.get("id", ""))
        return self._current_play_id or ""

    def _graft_or_match_task(
        self, task_id: str, task_name: str, task_path: str | None = None
    ) -> None:
        """Update the dynamic-expansion cursor for an arriving task.

        Matches the runtime task path against preflight TaskDefinitions
        first, then falls back to the task name. A hit updates the parent
        cursor — the next unknown task gets grafted as its child. A miss
        creates a dynamic TaskDefinition under the current parent (the most
        recently matched preflight task) and marks the UUID so re-arriving
        events don't duplicate the graft.

        Called from both ``v2_playbook_on_task_start`` (linear strategy)
        and ``v2_runner_on_start`` (free strategy) so dynamic include_tasks
        children land regardless of strategy.
        """
        if not self.definitions or not task_name or task_id in self._grafted_uuids:
            return

        # HS-5: path/name → leaf lookup via the precomputed indexes (built
        # when ``definitions`` was assigned). Falls back to scanning only if
        # the indexes are somehow stale, which __setattr__ rules out.
        path_index = self._task_def_by_path
        if task_path and path_index is not None:
            leaf = path_index.get(task_path)
            if leaf is not None:
                self._last_matched_task_def = leaf
                return

        index = self._task_def_index
        if index is not None:
            leaf = index.get(task_name)
            if leaf is None:
                leaf = index.get(strip_role_prefix(task_name))
            if leaf is None:
                # Try template-variable match: runtime "Get ID for
                # angie-sidecar" vs preflight "Get ID for {{ user }}".
                for preflight_name, tdef in index.items():
                    if "{{" not in preflight_name:
                        continue
                    skeleton = re.sub(r"\s+", " ", _JINJA_RE.sub("", preflight_name)).strip()
                    if not skeleton:
                        leaf = tdef
                        break
                    # Subsequence match: every skeleton word must appear
                    # in order in the runtime name.
                    skeleton_words = skeleton.split()
                    runtime_words = task_name.split()
                    si = 0
                    for rw in runtime_words:
                        if si < len(skeleton_words) and rw == skeleton_words[si]:
                            si += 1
                    if si == len(skeleton_words):
                        leaf = tdef
                        break
            if leaf is not None:
                self._last_matched_task_def = leaf
                return

        parent = self._last_matched_task_def
        if parent is None:
            # No preflight task has matched yet — leave the unknown task as
            # an orphan rather than grafting it onto an arbitrary node.
            return

        parent.children.append(
            TaskDefinition(
                name=task_name,
                role=parent.role,
                tags=[],
                play_id=parent.play_id,
                play_order=parent.play_order,
                task_order=-1,
                is_dynamic=True,
                path=task_path,
            )
        )
        if task_id:
            self._grafted_uuids.add(task_id)
        self._bump_tree_revision()

    def _handle_v2_playbook_on_task_start(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_playbook_on_task_start event."""
        task_data = self._task_dict(event)
        play_id = self._resolve_play_id(event)
        task_id = task_data.get("id", "")
        task_name = task_data.get("name", "")
        task_path = task_data.get("path")
        play_missing = play_id not in self.plays

        self._graft_or_match_task(task_id, task_name, task_path)

        if play_missing:
            self.plays[play_id] = PlayRunState(
                play_id=play_id,
                name="",
                status=Status.RUNNING,
            )

        play = self.plays[play_id]

        if play.detected_strategy is None:
            play.detected_strategy = "linear"

        if task_id not in play.tasks:
            play.tasks[task_id] = TaskRunState(
                task_id=task_id,
                name=task_name,
                status=Status.RUNNING,
                start_time=ts,
                path=task_path,
            )
        else:
            play.tasks[task_id].status = Status.RUNNING
            play.tasks[task_id].start_time = ts
            if task_path is not None:
                play.tasks[task_id].path = task_path

        # Under linear strategy `ansible.posix.jsonl` does not emit
        # v2_runner_on_start (guarded by `if self._is_lockstep: return`),
        # so per-host RUNNING state has no other signal. Synthesise it
        # from the matching play's preflight resolved_hosts. Terminal
        # handlers (runner_on_ok/failed/skipped/unreachable) will
        # overwrite each host entry as the events arrive.
        resolved_hosts = self._resolve_play_hosts(play)
        for hostname in resolved_hosts:
            if hostname not in play.tasks[task_id].hosts:
                play.tasks[task_id].hosts[hostname] = HostRunState(
                    hostname=hostname,
                    status=Status.RUNNING,
                    start_time=ts,
                )

        # Under linear strategy, tasks execute sequentially. When a new
        # task starts, any previous RUNNING task that is clearly done —
        # mark it COMPLETED so the tree can clear it.
        if play.detected_strategy == "linear":
            for p in self.plays.values():
                for other_task in p.tasks.values():
                    if other_task.task_id == task_id and p.play_id == play.play_id:
                        continue
                    if other_task.status != Status.RUNNING:
                        continue
                    if not other_task.hosts:
                        other_task.status = Status.COMPLETED
                        continue
                    if all(hs.status != Status.RUNNING for hs in other_task.hosts.values()):
                        other_task.status = Status.COMPLETED
                    elif p.play_id == play.play_id or play_missing:
                        for hostname in list(other_task.hosts):
                            hs = other_task.hosts[hostname]
                            if hs.status == Status.RUNNING:
                                other_task.hosts[hostname] = HostRunState(
                                    hostname=hostname,
                                    status=Status.OK,
                                    changed=False,
                                    start_time=hs.start_time,
                                    end_time=ts,
                                )
                        other_task.status = Status.COMPLETED
                    else:
                        continue

    def _resolve_play_hosts(self, play: "PlayRunState") -> list[str]:
        """Look up preflight resolved_hosts for a runtime play.

        Preflight assigns ``PlayDefinition.id = str(play_number)`` while
        runtime events carry an opaque UUID, so the IDs don't match.
        We match by name instead. Returns an empty list when no
        definition matches (no preflight data, or play name mismatch) —
        callers should treat that as "no per-host signal available".

        HS-6: name → PlayDefinition via precomputed index, built when
        ``definitions`` is assigned. Avoids the O(P_def) scan that ran
        on every task-start event.
        """
        index = self._play_def_by_name
        if index is not None:
            play_def = index.get(play.name)
            if play_def is not None:
                return list(play_def.resolved_hosts)
            # Fallback: stripped-name match catches whitespace differences
            # between --list-tasks output and JSONL event play names.
            stripped = play.name.strip()
            if stripped != play.name:
                play_def = index.get(stripped)
                if play_def is not None:
                    return list(play_def.resolved_hosts)
        return []

    def _handle_v2_playbook_on_handler_task_start(
        self, event: dict[str, Any], ts: datetime
    ) -> None:
        """Handle v2_playbook_on_handler_task_start event (same as task_start)."""
        self._handle_v2_playbook_on_task_start(event, ts)

    def _handle_v2_runner_on_start(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_runner_on_start event."""
        task_data = self._task_dict(event)
        hostname = event.get("host", "")
        task_id = task_data.get("id", "")
        task_name = task_data.get("name", "")
        task_path = task_data.get("path")
        play_id = self._resolve_play_id(event)

        self._graft_or_match_task(task_id, task_name, task_path)

        if play_id not in self.plays:
            self.plays[play_id] = PlayRunState(
                play_id=play_id,
                name="",
                status=Status.RUNNING,
            )
            self.plays[play_id].detected_strategy = "free"
        elif self.plays[play_id].detected_strategy is None:
            self.plays[play_id].detected_strategy = "free"
        elif self.plays[play_id].detected_strategy == "linear":
            # A v2_runner_on_start event means the playbook is NOT
            # running with lockstep enabled (the JSONL callback
            # guards runner_on_start behind `if self._is_lockstep:
            # return`). Flip to free — the earlier linear detection
            # by task_start was premature.
            self.plays[play_id].detected_strategy = "free"

        play = self.plays[play_id]

        if task_id not in play.tasks:
            play.tasks[task_id] = TaskRunState(
                task_id=task_id,
                name=task_name,
                status=Status.RUNNING,
                start_time=ts,
                path=task_path,
            )
        else:
            play.tasks[task_id].status = Status.RUNNING
            play.tasks[task_id].start_time = ts
            if task_path is not None:
                play.tasks[task_id].path = task_path

        # Record the host as RUNNING so the renderer can show which hosts
        # are currently executing a task (especially under strategy: free,
        # where the only signal that host X has started task Y is this
        # event). A subsequent v2_runner_on_ok/failed/skipped/unreachable
        # event will overwrite this entry with the terminal status.
        if hostname and hostname not in play.tasks[task_id].hosts:
            play.tasks[task_id].hosts[hostname] = HostRunState(
                hostname=hostname,
                status=Status.RUNNING,
                start_time=ts,
            )

    def _handle_v2_runner_item_on(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle a per-item loop event (``v2_runner_item_on_*``).

        These are additive, live-progress signals emitted by the bundled
        ``aom_jsonl`` callback once per loop iteration. They must NOT affect
        host/task status counts — the aggregate ``v2_runner_on_*`` event
        still lands at loop end and is the source of truth for final state.
        Registering them here (rather than letting them fall through to
        ``unknown_events``) keeps the run-quality report clean.

        The only state mutation is a per-host ``loop_items_done`` tally
        used by the tree row. The host is marked RUNNING if not already
        present — under the linear strategy there is no ``v2_runner_on_start``
        and these item events are the first per-host signal of the loop.
        """
        task_data = self._task_dict(event)
        task_id = task_data.get("id", "")
        play_id = self._resolve_play_id(event)
        play = self.plays.get(play_id)
        if play is None:
            return
        task = play.tasks.get(task_id)
        if task is None:
            return
        for hostname in self._hosts_dict(event):
            if not hostname:
                continue
            host = task.hosts.get(hostname)
            if host is None:
                host = HostRunState(hostname=hostname, status=Status.RUNNING, start_time=ts)
                task.hosts[hostname] = host
            host.loop_items_done += 1

    def _task_dict(self, event: dict[str, Any]) -> dict[str, Any]:
        """Extract the ``task`` field as a dict.

        ansible.posix.jsonl may emit ``task`` as a bare UUID string or
        ``None`` when the mitogen transport drops mid-task.  Return an
        empty dict in those cases so callers can safely call ``.get()``.
        """
        task = event.get("task")
        return task if isinstance(task, dict) else {}

    def _hosts_dict(self, event: dict[str, Any]) -> dict[str, Any]:
        """Extract the ``hosts`` field as a dict.

        mitogen bulk-reconnect events can emit ``hosts`` as a list of
        hostnames instead of the canonical ``{hostname: result}`` dict.
        Return an empty dict so callers can safely call ``.items()`` or
        iterate without materialising bogus host entries.
        """
        hosts = event.get("hosts")
        return hosts if isinstance(hosts, dict) else {}

    def _handle_v2_runner_on_ok(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_runner_on_ok event."""
        task_data = self._task_dict(event)
        hosts_data = self._hosts_dict(event)
        task_id = task_data.get("id", "")
        play_id = self._resolve_play_id(event)

        if play_id not in self.plays:
            return

        play = self.plays[play_id]
        if task_id not in play.tasks:
            return

        task = play.tasks[task_id]

        for hostname, host_result in hosts_data.items():
            changed = host_result.get("changed", False)
            task.hosts[hostname] = HostRunState(
                hostname=hostname,
                status=Status.CHANGED if changed else Status.OK,
                changed=changed,
                end_time=ts,
            )

    def _handle_v2_runner_on_failed(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_runner_on_failed event."""
        task_data = self._task_dict(event)
        hosts_data = self._hosts_dict(event)
        task_id = task_data.get("id", "")
        play_id = self._resolve_play_id(event)

        if play_id not in self.plays:
            return

        play = self.plays[play_id]
        if task_id not in play.tasks:
            return

        task = play.tasks[task_id]

        for hostname, host_result in hosts_data.items():
            ignore_errors = False
            verbose_always = host_result.get("_ansible_verbose_always", {})
            if isinstance(verbose_always, dict):
                ignore_errors = verbose_always.get("ignore_errors", False)

            msg = host_result.get("msg", "")

            if ignore_errors:
                task.hosts[hostname] = HostRunState(
                    hostname=hostname,
                    status=Status.OK,
                    changed=False,
                    message=msg,
                    end_time=ts,
                )
            else:
                task.hosts[hostname] = HostRunState(
                    hostname=hostname,
                    status=Status.FAILED,
                    changed=False,
                    message=msg,
                    end_time=ts,
                )
                self.status = Status.FAILED

    def _handle_v2_runner_on_skipped(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_runner_on_skipped event."""
        task_data = self._task_dict(event)
        hosts_data = self._hosts_dict(event)
        task_id = task_data.get("id", "")
        play_id = self._resolve_play_id(event)

        if play_id not in self.plays:
            return

        play = self.plays[play_id]
        if task_id not in play.tasks:
            return

        task = play.tasks[task_id]

        for hostname in hosts_data:
            task.hosts[hostname] = HostRunState(
                hostname=hostname,
                status=Status.SKIPPED,
                end_time=ts,
            )

    def _handle_v2_runner_on_unreachable(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_runner_on_unreachable event."""
        task_data = self._task_dict(event)
        hosts_data = self._hosts_dict(event)
        task_id = task_data.get("id", "")
        play_id = self._resolve_play_id(event)

        if play_id not in self.plays:
            return

        play = self.plays[play_id]
        if task_id not in play.tasks:
            return

        task = play.tasks[task_id]

        for hostname, host_result in hosts_data.items():
            msg = host_result.get("msg", "")
            task.hosts[hostname] = HostRunState(
                hostname=hostname,
                status=Status.UNREACHABLE,
                message=msg,
                end_time=ts,
            )

        self.status = Status.FAILED

    def _handle_v2_playbook_on_stats(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_playbook_on_stats event.

        Also clean up any hosts still stuck as RUNNING — this happens when
        terminal events (v2_runner_on_ok etc.) are silently dropped because
        play_id or task_id doesn't match. By the time we receive
        v2_playbook_on_stats the playbook is finished, so no host should
        still be RUNNING."""
        self.end_time = ts

        stats = event.get("stats", {})
        has_failures = False
        has_unreachable = False

        for host_stats in stats.values():
            if not isinstance(host_stats, dict):
                continue
            if host_stats.get("failures", 0) > 0:
                has_failures = True
            if host_stats.get("unreachable", 0) > 0:
                has_unreachable = True

        if has_failures or has_unreachable:
            self.status = Status.FAILED
        else:
            self.status = Status.COMPLETED

        # Clean up stale RUNNING hosts: the playbook is done, so any host
        # still marked RUNNING has a missing terminal event.
        for play in self.plays.values():
            self._finalize_play(play, ts)
