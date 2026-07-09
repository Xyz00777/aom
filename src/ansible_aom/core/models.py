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
from datetime import datetime
from enum import Enum
from typing import Any

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


def runtime_role_from_task_name(task_name: str) -> str | None:
    """Infer an ``include_role``-style runtime role from a task name.

    Accepts simple ``role : task`` prefixes where the role token has no
    whitespace. Intentionally rejects literal task names like
    ``Install foo : bar`` (whitespace inside the prefix disqualifies them).
    Returns ``None`` when the name has no ``" : "`` separator at all or
    the prefix is empty / contains whitespace.
    """
    if " : " not in task_name:
        return None
    prefix = task_name.split(" : ", 1)[0].strip()
    if not prefix or any(ch.isspace() for ch in prefix):
        return None
    return prefix


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
    # The parent role name when this task is nested inside another role
    # (e.g. an ``include_role`` inside a role's ``tasks/main.yml``).
    # ``None`` for top-level play tasks and for tasks whose enclosing role
    # is the play itself. Carried on the definition so the preflight
    # iterator can propagate a full role path. T5 sets this on dynamically
    # grafted tasks.
    parent_role: str | None = None


@dataclass
class RoleGroupDefinition:
    """Grouped role tasks when 5+ consecutive tasks share same role.

    ``parent`` carries the enclosing role's name for nested roles (e.g.
    ``angie_ssl_terminator`` nested under ``podman``) or ``None`` for
    top-level role groups under a play. Populated by ``group_roles`` via
    its ``parent_role`` argument; carried here so downstream walkers
    (``iter_preflight_task_defs``, ``TreeProjection``) can reconstruct
    the full role path without re-parsing the structure.
    """

    role: str
    tasks: list["TaskDefinition | RoleGroupDefinition"]
    parent: str | None = None

    @property
    def name(self) -> str:
        return f"Role: {self.role} ({len(self.tasks)} tasks)"


def _iter_task_def_tree(task_def: TaskDefinition) -> Iterator[TaskDefinition]:
    """Yield a TaskDefinition and all nested TaskDefinition.children in order."""
    yield task_def
    for child in task_def.children:
        yield from _iter_task_def_tree(child)


def iter_preflight_task_defs(
    entries: Sequence[TaskDefinition | RoleGroupDefinition],
    inherited_role_path: tuple[str, ...] = (),
) -> Iterator[tuple[TaskDefinition, tuple[str, ...]]]:
    """Yield preflight task definitions in display order with effective role path.

    The second element of each yielded tuple is the *full* role path from
    outermost to innermost — e.g. ``("podman", "angie_ssl_terminator")``
    for a task inside ``angie_ssl_terminator`` which itself was included
    from ``podman``. An empty tuple means "no role active" (the task sits
    directly under a play).

    Walks ``RoleGroupDefinition.tasks`` (including any nested
    ``RoleGroupDefinition`` for role-in-role) and nested
    ``TaskDefinition.children`` recursively, preserving the pre-order
    tree traversal used by indexing and rendering.
    """
    for entry in entries:
        if isinstance(entry, RoleGroupDefinition):
            child_path = inherited_role_path + (entry.role,)
            yield from iter_preflight_task_defs(entry.tasks, inherited_role_path=child_path)
            continue

        if entry.role is not None:
            role_path: tuple[str, ...] = inherited_role_path + (entry.role,)
        else:
            role_path = inherited_role_path
        yield entry, role_path
        if entry.children:
            yield from iter_preflight_task_defs(entry.children, inherited_role_path=role_path)


def role_path_str(role_path: tuple[str, ...]) -> str:
    """Return ``'podman > angie_ssl_terminator'`` for display. ``''`` for empty."""
    return " > ".join(role_path)


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
    # The parent role name for nested roles (e.g. ``angie_ssl_terminator``
    # included from ``podman``). ``None`` for top-level play tasks.
    # T5 sets this when the runtime ``"role : "`` prefix differs from
    # the preflight role assignment, so the projection can render a
    # sub-branch under the right role.
    parent_role: str | None = None


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

    ``parent_role`` carries the name of the *enclosing* role when this
    role is nested inside another role's ``tasks/main.yml`` (e.g.
    ``angie_ssl_terminator`` discovered inside ``podman``'s tasks). It
    is ``None`` for top-level roles included directly from a play. T4
    populates it during role discovery; T5 reads it to set
    ``TaskRunState.parent_role`` and ``TaskDefinition.parent_role``.
    """

    role_name: str
    task_names: list[str]
    parent_role: str | None = None

    @property
    def task_count(self) -> int:
        """Pre-computed count for O(1) access in counter hot paths."""
        return len(self.task_names)


# Legacy re-exports for ``from ansible_aom.core.models import RunState``
# (and the leaf-task helpers) so existing callers keep working during the
# migration to :mod:`ansible_aom.core.run_state`. Resolved lazily through
# ``__getattr__`` to avoid a circular import: importing this module would
# otherwise re-trigger the partially-loaded run_state module while it is
# still pulling the dataclasses above out of this module.
_LEGACY_RUN_STATE_EXPORTS = frozenset({"RunState", "_iter_leaf_task_defs", "count_leaf_tasks"})


def __getattr__(name: str) -> Any:  # pragma: no cover - exercised via import tests
    if name in _LEGACY_RUN_STATE_EXPORTS:
        from ansible_aom.core import run_state

        value = getattr(run_state, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _LEGACY_RUN_STATE_EXPORTS)
