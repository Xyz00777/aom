"""Pure projection of RunState into renderable tree + host-row data.

This module contains *no* I/O, no ANSI, no terminal awareness — it is
the data layer the compact (and future TUI) renderers consume. See
docs/superpowers/specs/2026-05-19-free-strategy-tree-view-design.md.

Architectural rule: core/ never imports from compact/ or tui/. Renderers
import from here; never the reverse.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskRunState,
)

TreeKind = Literal["playbook", "play", "role", "task", "host"]


@dataclass(frozen=True)
class TreeLine:
    """One rendered line in the tree.

    The renderer turns this into "{indent}{branch_glyph}{label}" with
    status-coloured glyph; this class itself carries no rendering
    concerns.

    `identity` carries a non-presentation handle for the line — currently
    used only for `kind="role"` lines, so the pruner and the renderer
    don't have to parse the role name back out of `label`. None for all
    other line kinds.
    """

    depth: int
    kind: TreeKind
    label: str
    glyph: str | None
    status: Status | None
    elapsed_s: float | None
    identity: str | None = None


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


def _effective_status(hs: HostRunState) -> Status:
    """Promote OK+changed → CHANGED for count-classification purposes.

    `HostRunState.status == OK` combined with `changed == True` is
    counted as CHANGED everywhere the projection tallies host outcomes
    (see `host_rows` and `_task_line`). Centralising the rule keeps the
    two call sites from drifting apart.
    """
    return Status.CHANGED if hs.status == Status.OK and hs.changed else hs.status


@dataclass
class TreeProjection:
    """Pure projection of RunState. Build via `from_run_state`."""

    _state: RunState
    _role_index: dict[str, str] | None = field(default=None, init=False, repr=False)

    @classmethod
    def from_run_state(cls, state: RunState) -> "TreeProjection":
        return cls(_state=state)

    # --- Visibility predicates --------------------------------------------

    def is_tree_visible(self) -> bool:
        """True iff the playbook is currently in flight.

        "In flight" = at least one task has been announced AND
        `v2_playbook_on_stats` hasn't fired yet (`state.end_time` set).

        The tree is sticky between tasks: even when no host is
        currently RUNNING (transient gap between tasks under linear
        strategy, especially for fast tasks), the tree stays visible
        and falls back to showing the most recently active task. This
        avoids flicker on sub-second tasks. See `tree_lines` for the
        fallback render.
        """
        if self._state.end_time is not None:
            return False
        for play in self._state.plays.values():
            if play.tasks:
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
                    effective = _effective_status(hs)

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
        """Project + prune to fit `budget` lines.

        Pruning order:
          (a) drop host leaves under tasks
          (b) drop excess task lines within a role, keep first one
          (c) collapse a role to "role: X  (N tasks running on K hosts)"

        Invariant: every active role retains at least one visible line.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        lines = self._tree_lines_unbounded(now)
        if len(lines) <= budget:
            return lines

        # --- Stage (a): drop host leaves -----------------------------------
        lines = [ln for ln in lines if ln.kind != "host"]
        if len(lines) <= budget:
            return lines

        # --- Stage (b): keep <=1 task per role bucket ----------------------
        # Stage (b): keep ≤1 task line per role bucket. A role bucket starts
        # at a role/play/playbook line.
        #
        # Tasks in the implicit "no role" bucket (depth=2, directly under
        # `play` with no preceding `role` line) are also capped at one. The
        # spec invariants only protect *active roles* — play-level tasks have
        # no invariant — so capping them when over budget is allowed and gives
        # the pruner more room. Plan-spec deviation accepted by review.
        kept: list[TreeLine] = []
        tasks_in_current_bucket = 0
        for ln in lines:
            if ln.kind in ("playbook", "play", "role"):
                kept.append(ln)
                tasks_in_current_bucket = 0
            elif ln.kind == "task":
                if tasks_in_current_bucket == 0:
                    kept.append(ln)
                tasks_in_current_bucket += 1
            else:
                kept.append(ln)
        lines = kept
        if len(lines) <= budget:
            return lines

        # --- Stage (c): collapse roles to summary lines --------------------
        # Aggregate per-role running task count and unique running-host count
        # from current RunState. Tasks with role=None aggregate under the
        # None bucket but won't render as "role: ..." — they survive stage
        # (b) already; if the suite is still over-budget here, the layout is
        # too constrained to satisfy and the result will simply be shorter
        # than the strict bound (acceptable degradation, never worse than
        # playbook + play + 1 line per active role).
        tasks_per_role: dict[str | None, int] = defaultdict(int)
        hosts_per_role: dict[str | None, set[str]] = defaultdict(set)
        for play in self._state.plays.values():
            for task in play.tasks.values():
                # Same "running iff any host is RUNNING" rule as the walker.
                running_hosts = {
                    hostname for hostname, hs in task.hosts.items() if hs.status == Status.RUNNING
                }
                if not running_hosts:
                    continue
                role = self._task_role(task.name)
                tasks_per_role[role] += 1
                hosts_per_role[role].update(running_hosts)

        collapsed: list[TreeLine] = []
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.kind == "role":
                # Use the structured role identity, not the rendered label —
                # avoids coupling pruning to label format.
                role_name = ln.identity or ln.label.removeprefix("role: ")
                n_tasks = tasks_per_role.get(role_name, 0)
                n_hosts = len(hosts_per_role.get(role_name, set()))
                collapsed.append(
                    TreeLine(
                        depth=ln.depth,
                        kind="role",
                        label=(f"role: {role_name}  ({n_tasks} tasks running on {n_hosts} hosts)"),
                        glyph=None,
                        status=None,
                        elapsed_s=None,
                        identity=role_name,
                    )
                )
                # Skip any immediately following task lines under this role.
                i += 1
                # Also consume any orphaned host lines so this code is correct
                # regardless of whether stage (a) already pruned them.
                while i < len(lines) and lines[i].kind in ("task", "host"):
                    i += 1
            else:
                collapsed.append(ln)
                i += 1
        return collapsed

    def _tree_lines_unbounded(self, now: datetime) -> list[TreeLine]:
        """Project full tree (no pruning). See ``tree_lines`` for entry point.

        Layout rule: each play shows tasks that are currently RUNNING and
        every task still to come (pending). Completed tasks are dropped —
        they already appear in the streaming log above the panel, so the
        tree's job is just "what's happening now and what's next".
        """
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
            play_items = self._play_running_and_pending(play)
            if not play_items:
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

            current_role: str | None = None
            role_open = False
            for item_kind, name, role, runtime in play_items:
                if role != current_role:
                    current_role = role
                    role_open = role is not None
                    if role_open:
                        lines.append(
                            TreeLine(
                                depth=2,
                                kind="role",
                                label=f"role: {role}",
                                glyph=None,
                                status=None,
                                elapsed_s=None,
                                identity=role,
                            )
                        )
                task_depth = 3 if role_open else 2

                if item_kind == "running" and runtime is not None:
                    lines.append(self._task_line(runtime, depth=task_depth))
                    for hostname, hs in runtime.hosts.items():
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
                                status=hs.status,
                                elapsed_s=elapsed,
                            )
                        )
                else:  # pending
                    lines.append(
                        TreeLine(
                            depth=task_depth,
                            kind="task",
                            label=name,
                            glyph=None,
                            status=Status.PENDING,
                            elapsed_s=None,
                        )
                    )

        return lines

    def _play_running_and_pending(
        self, play: "PlayRunState"
    ) -> list[tuple[str, str, str | None, TaskRunState | None]]:
        """Enumerate (kind, name, role, runtime) for a play's running and
        pending tasks, in execution order.

        ``kind`` is ``"running"`` (task has at least one RUNNING host) or
        ``"pending"`` (task hasn't started, or runtime has no hosts yet).
        Completed tasks — runtime has hosts and no host is RUNNING — are
        dropped from the result.

        Order: preflight order first (when ``definitions`` is available),
        with any runtime-only tasks (dynamic ``include_tasks``) appended
        in runtime-arrival order.
        """
        runtime_by_name: dict[str, TaskRunState] = {}
        for task in play.tasks.values():
            runtime_by_name.setdefault(task.name, task)

        play_def = self._play_def_for(play)

        items: list[tuple[str, str, str | None, TaskRunState | None]] = []
        emitted_names: set[str] = set()

        def _classify(runtime: TaskRunState | None) -> str:
            """Return ``"running"`` / ``"pending"`` / ``"completed"``.

            ``"completed"`` is filtered out before items reach the caller,
            but the helper still returns it so the drop site can branch
            on a single classification result.
            """
            if runtime is None or not runtime.hosts:
                return "pending"
            if any(hs.status == Status.RUNNING for hs in runtime.hosts.values()):
                return "running"
            return "completed"

        if play_def is not None:
            for entry in play_def.tasks:
                if isinstance(entry, RoleGroupDefinition):
                    role: str | None = entry.role
                    task_defs = entry.tasks
                else:
                    role = None
                    task_defs = [entry]
                for tdef in task_defs:
                    runtime = runtime_by_name.get(tdef.name)
                    kind = _classify(runtime)
                    emitted_names.add(tdef.name)
                    if kind == "completed":
                        continue
                    items.append((kind, tdef.name, role, runtime))

        # Runtime-only tasks (dynamic include_tasks, or no preflight at all).
        for task in play.tasks.values():
            if task.name in emitted_names:
                continue
            kind = _classify(task)
            if kind == "completed":
                continue
            items.append((kind, task.name, self._task_role(task.name), task))

        return items

    def _play_def_for(self, play: "PlayRunState") -> "PlayDefinition | None":
        """Return the matching preflight PlayDefinition, or None.

        Preflight defs key by play number; runtime plays key by UUID, so
        the only viable join is by name. ``RunState`` already maintains
        ``_play_def_by_name`` for the runner — reuse it here.
        """
        index = self._state._play_def_by_name
        if index is None:
            return None
        return index.get(play.name)

    def _task_role(self, task_name: str) -> str | None:
        """Return the role name a task belongs to, or None.

        Preflight `--list-tasks` records role membership via
        RoleGroupDefinition; first match wins. Memoised on first call.
        """
        if self._role_index is None:
            idx: dict[str, str] = {}
            for play_def in self._state.definitions:
                for entry in play_def.tasks:
                    if isinstance(entry, RoleGroupDefinition):
                        for task_def in entry.tasks:
                            idx.setdefault(task_def.name, entry.role)
            # Direct assignment is fine because TreeProjection is a regular
            # @dataclass (not frozen).
            self._role_index = idx
        return self._role_index.get(task_name)

    @staticmethod
    def _task_line(task: TaskRunState, depth: int) -> TreeLine:
        # Count tally for the parenthesised summary on the task line.
        # Order matters for the label: ok, changed, running, failed,
        # unreachable, skipped — same order as the spec example.
        ok = changed = running = failed = unreachable = skipped = 0
        for hs in task.hosts.values():
            if hs.status == Status.RUNNING:
                running += 1
                continue
            effective = _effective_status(hs)
            if effective == Status.OK:
                ok += 1
            elif effective == Status.CHANGED:
                changed += 1
            elif effective == Status.FAILED:
                failed += 1
            elif effective == Status.UNREACHABLE:
                unreachable += 1
            elif effective == Status.SKIPPED:
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
