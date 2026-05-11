"""Data models for AOM.

This module defines the dual-track architecture:
- Definition classes (immutable, from --list-tasks)
- State classes (mutable, from JSONL events)

See SPECIFICATION.md Section 6.1 for model definitions.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


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


@dataclass
class TaskRunState:
    """Runtime state for a task execution (State class)."""

    task_id: str
    name: str
    status: Status = Status.PENDING
    hosts: dict[str, HostRunState] = field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None


@dataclass
class PlayRunState:
    """Runtime state for a play execution (State class)."""

    play_id: str
    name: str
    status: Status = Status.PENDING
    tasks: dict[str, TaskRunState] = field(default_factory=dict)
    detected_strategy: str | None = None


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


def _iter_leaf_task_defs(plays: list["PlayDefinition"]) -> "list[TaskDefinition]":
    """Flatten preflight definitions into the leaf TaskDefinitions visible by name.

    ``RoleGroupDefinition`` is unwrapped so its inner tasks are reachable; the
    grafting logic needs to look up an event task name against every static
    leaf, regardless of whether role grouping wrapped it for display.
    """
    leaves: list[TaskDefinition] = []
    for play in plays:
        for entry in play.tasks:
            if isinstance(entry, RoleGroupDefinition):
                leaves.extend(entry.tasks)
            else:
                leaves.append(entry)
    return leaves


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
            "v2_playbook_on_stats": self._handle_v2_playbook_on_stats,
        }

        handler = handler_map.get(event_type)
        if handler:
            handler(event, ts)
        else:
            logger.debug(f"Unknown event type: {event_type}")

    def _handle_v2_playbook_on_start(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_playbook_on_start event."""
        if self.start_time is None:
            self.start_time = ts
            self.status = Status.RUNNING

    def _handle_v2_playbook_on_play_start(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_playbook_on_play_start event."""
        play_data = event.get("play", {})
        play_id = play_data.get("id", "")
        play_name = play_data.get("name", "")

        self._current_play_id = play_id

        if self.start_time is None:
            self.start_time = ts
            self.status = Status.RUNNING

        if play_id in self.plays:
            self.plays[play_id].name = play_name
        else:
            self.plays[play_id] = PlayRunState(
                play_id=play_id,
                name=play_name,
                status=Status.RUNNING,
            )

    def _resolve_play_id(self, event: dict[str, Any]) -> str:
        """Resolve play_id from event or _current_play_id.

        ansible-core >=2.20 omits the 'play' field from runner/task events,
        so we fall back to the play_id tracked from the most recent
        v2_playbook_on_play_start event.
        """
        play_data = event.get("play")
        if play_data and isinstance(play_data, dict):
            return play_data.get("id", "")
        return self._current_play_id or ""

    def _graft_or_match_task(self, task_id: str, task_name: str) -> None:
        """Update the dynamic-expansion cursor for an arriving task.

        Matches the task name against preflight TaskDefinitions. A hit
        updates the parent cursor — the next unknown task gets grafted as
        its child. A miss creates a dynamic TaskDefinition under the current
        parent (the most recently matched preflight task) and marks the
        UUID so re-arriving events don't duplicate the graft.

        Called from both ``v2_playbook_on_task_start`` (linear strategy)
        and ``v2_runner_on_start`` (free strategy) so dynamic include_tasks
        children land regardless of strategy.
        """
        if not self.definitions or not task_name or task_id in self._grafted_uuids:
            return

        for leaf in _iter_leaf_task_defs(self.definitions):
            if leaf.name == task_name:
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
            )
        )
        if task_id:
            self._grafted_uuids.add(task_id)

    def _handle_v2_playbook_on_task_start(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_playbook_on_task_start event."""
        task_data = event.get("task", {})
        play_id = self._resolve_play_id(event)
        task_id = task_data.get("id", "")
        task_name = task_data.get("name", "")

        self._graft_or_match_task(task_id, task_name)

        if play_id not in self.plays:
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
                status=Status.PENDING,
            )

    def _handle_v2_playbook_on_handler_task_start(
        self, event: dict[str, Any], ts: datetime
    ) -> None:
        """Handle v2_playbook_on_handler_task_start event (same as task_start)."""
        self._handle_v2_playbook_on_task_start(event, ts)

    def _handle_v2_runner_on_start(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_runner_on_start event."""
        task_data = event.get("task", {})
        _hostname = event.get("host", "")
        task_id = task_data.get("id", "")
        task_name = task_data.get("name", "")
        play_id = self._resolve_play_id(event)

        self._graft_or_match_task(task_id, task_name)

        if play_id not in self.plays:
            self.plays[play_id] = PlayRunState(
                play_id=play_id,
                name="",
                status=Status.RUNNING,
            )
            self.plays[play_id].detected_strategy = "free"
        elif self.plays[play_id].detected_strategy is None:
            self.plays[play_id].detected_strategy = "free"

        play = self.plays[play_id]

        if task_id not in play.tasks:
            play.tasks[task_id] = TaskRunState(
                task_id=task_id,
                name=task_name,
                status=Status.RUNNING,
                start_time=ts,
            )
        else:
            play.tasks[task_id].status = Status.RUNNING
            play.tasks[task_id].start_time = ts

    def _handle_v2_runner_on_ok(self, event: dict[str, Any], ts: datetime) -> None:
        """Handle v2_runner_on_ok event."""
        task_data = event.get("task", {})
        hosts_data = event.get("hosts", {})
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
        task_data = event.get("task", {})
        hosts_data = event.get("hosts", {})
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
        task_data = event.get("task", {})
        hosts_data = event.get("hosts", {})
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
        task_data = event.get("task", {})
        hosts_data = event.get("hosts", {})
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
        """Handle v2_playbook_on_stats event."""
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
