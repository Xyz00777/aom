"""Pure projection of RunState into renderable tree + host-row data.

This module contains *no* I/O, no ANSI, no terminal awareness — it is
the data layer the compact (and future TUI) renderers consume. See
docs/superpowers/specs/2026-05-19-free-strategy-tree-view-design.md.

Architectural rule: core/ never imports from compact/ or tui/. Renderers
import from here; never the reverse.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from ansible_aom.core.models import RoleGroupDefinition, RunState, Status, TaskRunState

TreeKind = Literal["playbook", "play", "role", "task", "host"]


@dataclass(frozen=True)
class TreeLine:
    """One rendered line in the tree.

    The renderer turns this into "{indent}{branch_glyph}{label}" with
    status-coloured glyph; this class itself carries no rendering
    concerns.
    """

    depth: int
    kind: TreeKind
    label: str
    glyph: str | None
    status: Status | None
    elapsed_s: float | None


@dataclass(frozen=True)
class HostRow:
    """One row in the per-host summary table.

    `counts` only carries non-zero entries. `worst_status` drives the
    hostname colour selection per the spec; `current_task` is None when
    the host is idle (between tasks) or after the run finishes.
    """

    hostname: str
    counts: dict[Status, int]
    worst_status: Status | None
    current_task: str | None
    current_elapsed_s: float | None


@dataclass
class TreeProjection:
    """Pure projection of RunState. Build via `from_run_state`."""

    _state: RunState

    @classmethod
    def from_run_state(cls, state: RunState) -> "TreeProjection":
        return cls(_state=state)

    # --- Visibility predicates --------------------------------------------

    def is_tree_visible(self) -> bool:
        """True iff at least one task has status=RUNNING right now."""
        for play in self._state.plays.values():
            for task in play.tasks.values():
                if task.status == Status.RUNNING:
                    return True
        return False

    def is_host_summary_visible(self) -> bool:
        """True iff the run targets more than one host.

        Prefers preflight `resolved_hosts` (so a multi-host run shows the
        table from frame zero); falls back to "hosts seen in events" when
        no preflight definitions are available.
        """
        preflight_hosts: set[str] = set()
        for play_def in self._state.definitions:
            preflight_hosts.update(play_def.resolved_hosts)
        if len(preflight_hosts) > 1:
            return True

        seen: set[str] = set()
        for play in self._state.plays.values():
            for task in play.tasks.values():
                seen.update(task.hosts.keys())
        return len(seen) > 1

    # --- Projections (filled in later tasks) ------------------------------

    # Priority order for worst-status selection (highest precedence first).
    # FAILED is worst because a single failure on a host is the most
    # actionable signal; UNREACHABLE comes next; CHANGED indicates state
    # actually mutated; OK is the baseline.
    _WORST_STATUS_PRIORITY: tuple[Status, ...] = (
        Status.FAILED,
        Status.UNREACHABLE,
        Status.CHANGED,
        Status.OK,
        Status.SKIPPED,
        Status.PENDING,
    )

    def host_rows(self, now: datetime | None = None) -> list[HostRow]:
        if now is None:
            now = datetime.now(timezone.utc)

        # Per-host accumulators.
        counts: dict[str, dict[Status, int]] = {}
        current: dict[str, tuple[str, float] | None] = {}

        # Preserve first-seen ordering — mirrors event order, which mirrors
        # ansible's host order under linear and roughly the start order
        # under free.
        order: list[str] = []

        for play in self._state.plays.values():
            for task in play.tasks.values():
                for hostname, hs in task.hosts.items():
                    if hostname not in counts:
                        counts[hostname] = {}
                        current[hostname] = None
                        order.append(hostname)

                    # changed=True takes precedence over status=OK for
                    # count classification — spec section "host row".
                    effective = (
                        Status.CHANGED if hs.status == Status.OK and hs.changed else hs.status
                    )

                    if hs.status == Status.RUNNING:
                        elapsed = (
                            (now - hs.start_time).total_seconds()
                            if hs.start_time is not None
                            else 0.0
                        )
                        current[hostname] = (task.name, elapsed)
                    elif effective in (
                        Status.OK,
                        Status.CHANGED,
                        Status.FAILED,
                        Status.UNREACHABLE,
                        Status.SKIPPED,
                    ):
                        counts[hostname][effective] = counts[hostname].get(effective, 0) + 1

        rows: list[HostRow] = []
        for hostname in order:
            host_counts = counts[hostname]
            worst = self._worst_status_of(host_counts.keys())
            cur = current[hostname]
            rows.append(
                HostRow(
                    hostname=hostname,
                    counts=dict(host_counts),
                    worst_status=worst,
                    current_task=cur[0] if cur else None,
                    current_elapsed_s=cur[1] if cur else None,
                )
            )
        return rows

    @classmethod
    def _worst_status_of(cls, statuses: Iterable[Status]) -> Status | None:
        seen = set(statuses)
        for s in cls._WORST_STATUS_PRIORITY:
            if s in seen:
                return s
        return None

    def tree_lines(self, budget: int, now: datetime | None = None) -> list[TreeLine]:
        if now is None:
            now = datetime.now(timezone.utc)

        if not self.is_tree_visible():
            return []

        lines: list[TreeLine] = [
            TreeLine(
                depth=0,
                kind="playbook",
                label=self._state.playbook,
                glyph=None,
                status=None,
                elapsed_s=None,
            )
        ]

        for play in self._state.plays.values():
            running_tasks = [t for t in play.tasks.values() if t.status == Status.RUNNING]
            if not running_tasks:
                continue
            lines.append(
                TreeLine(
                    depth=1,
                    kind="play",
                    label=f"play: {play.name}",
                    glyph=None,
                    status=play.status,
                    elapsed_s=None,
                )
            )
            # Group running tasks by their role (or None for play-level tasks).
            # Ordering preserves first-encounter order — under linear that's
            # ansible source order; under free that's per-task start order.
            tasks_by_role: dict[str | None, list[TaskRunState]] = {}
            order: list[str | None] = []
            for task in running_tasks:
                role = self._task_role(task.name)
                if role not in tasks_by_role:
                    tasks_by_role[role] = []
                    order.append(role)
                tasks_by_role[role].append(task)

            for role in order:
                task_depth = 2
                if role is not None:
                    lines.append(
                        TreeLine(
                            depth=2,
                            kind="role",
                            label=f"role: {role}",
                            glyph=None,
                            status=None,
                            elapsed_s=None,
                        )
                    )
                    task_depth = 3
                for task in tasks_by_role[role]:
                    lines.append(self._task_line(task, depth=task_depth))
                    for hostname, hs in task.hosts.items():
                        if hs.status != Status.RUNNING:
                            continue
                        elapsed = (
                            (now - hs.start_time).total_seconds()
                            if hs.start_time is not None
                            else 0.0
                        )
                        lines.append(
                            TreeLine(
                                depth=task_depth + 1,
                                kind="host",
                                label=hostname,
                                glyph=None,
                                status=Status.RUNNING,
                                elapsed_s=elapsed,
                            )
                        )

        return lines

    def _task_role(self, task_name: str) -> str | None:
        """Return the role name a task belongs to, or None.

        Preflight `--list-tasks` records role membership via
        RoleGroupDefinition; we look up by task name. The first match
        wins — duplicate task names across roles is a user-side
        ambiguity we don't try to resolve here.
        """
        for play_def in self._state.definitions:
            for entry in play_def.tasks:
                if isinstance(entry, RoleGroupDefinition):
                    for task_def in entry.tasks:
                        if task_def.name == task_name:
                            return entry.role
        return None

    @staticmethod
    def _task_line(task: TaskRunState, depth: int) -> TreeLine:
        # Count tally for the parenthesised summary on the task line.
        # Order matters for the label: ok, changed, running, failed,
        # unreachable, skipped — same order as the spec example.
        ok = changed = running = failed = unreachable = skipped = 0
        for hs in task.hosts.values():
            if hs.status == Status.RUNNING:
                running += 1
            elif hs.status == Status.OK:
                if hs.changed:
                    changed += 1
                else:
                    ok += 1
            elif hs.status == Status.CHANGED:
                changed += 1
            elif hs.status == Status.FAILED:
                failed += 1
            elif hs.status == Status.UNREACHABLE:
                unreachable += 1
            elif hs.status == Status.SKIPPED:
                skipped += 1
        parts: list[str] = []
        for label, n in (
            ("ok", ok),
            ("changed", changed),
            ("running", running),
            ("failed", failed),
            ("unreachable", unreachable),
            ("skipped", skipped),
        ):
            if n > 0:
                parts.append(f"{n} {label}")
        suffix = f"  ({', '.join(parts)})" if parts else ""
        return TreeLine(
            depth=depth,
            kind="task",
            label=f"{task.name}{suffix}",
            glyph=None,
            status=Status.RUNNING,
            elapsed_s=None,
        )
