"""Pure projection of RunState into renderable tree + host-row data.

This module contains *no* I/O, no ANSI, no terminal awareness. It is
the data layer the compact (and future TUI) renderers consume. See
docs/superpowers/specs/2026-05-19-free-strategy-tree-view-design.md.

Architectural rule: core/ never imports from compact/ or tui/. Renderers
import from here; never the reverse.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
    TaskRunState,
    iter_preflight_task_defs,
    strip_role_prefix,
)

TreeKind = Literal["playbook", "play", "role", "task", "host"]

_TEMPLATE_RE = re.compile(r"\{\{.*?\}\}")
_ROW_LEASE_TTL = timedelta(seconds=4)
_ROW_LEASE_LIMIT = 128


def _template_skeleton(name: str) -> str:
    """Strip ``{{ ... }}`` from a task name, yielding the static parts.

    ``--list-tasks`` preserves Jinja2 templates verbatim
    (e.g. ``"Get ID for {{ user }}"``). The JSONL callback sends
    the resolved value (``"Get ID for angie-sidecar"``).
    ``_template_skeleton`` returns ``"Get ID for"`` — the parts
    that are guaranteed identical between preflight and runtime.
    Multiple whitespace runs are collapsed so that ``"user  exists"``
    (from stripping ``{{ username }}``) becomes ``"user exists"``."""
    return _TEMPLATE_RE.sub("", name).strip()


def _is_template_match(preflight_name: str, runtime_name: str) -> bool:
    """Return True if ``runtime_name`` could be a resolved version of
    ``preflight_name`` (which may contain ``{{ ... }}`` templates).

    The match is structural: strip ``{{ ... }}`` from the preflight
    name to get the "skeleton" (static text), then check that every
    non-empty word of the skeleton appears as a subsequence in the
    runtime name. This handles templates at the start, middle, or end
    of the name, and works even when the resolved value inserts text
    between skeleton fragments."""
    if "{{" not in preflight_name:
        return False
    skeleton = _template_skeleton(preflight_name)
    if not skeleton:
        return True
    # All skeleton words must appear in order (subsequence) in the
    # runtime name. This is robust against resolved variables that
    # insert text between skeleton fragments.
    skeleton_words = skeleton.split()
    runtime_words = runtime_name.split()
    si = 0
    for rw in runtime_words:
        if si < len(skeleton_words) and rw == skeleton_words[si]:
            si += 1
    return si == len(skeleton_words)


def _play_target_hostnames(play: "PlayRunState", play_def: "PlayDefinition | None") -> set[str]:
    """Collect hostnames targeted by this play (read-only).

    Uses ``play_def.resolved_hosts`` when available (preflight targets).
    Falls back to collecting hostnames from the play's runtime tasks.
    Returns empty set only when no host data is available.
    """
    if play_def is not None and play_def.resolved_hosts:
        return set(play_def.resolved_hosts)
    hostnames: set[str] = set()
    for t in play.tasks.values():
        for hostname in t.hosts:
            hostnames.add(hostname)
    return hostnames


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


@dataclass
class _RowLease:
    """Internal continuity record for a visible row.

    Leases are intentionally short-lived: they keep the projection's
    sticky selection and row continuity metadata alive across quiet gaps,
    but expire on their own so completed rows do not accumulate forever.
    """

    last_seen_at: datetime
    expires_at: datetime


def _effective_status(hs: HostRunState) -> Status:
    """Promote OK+changed → CHANGED for count-classification purposes.

    `HostRunState.status == OK` combined with `changed == True` is
    counted as CHANGED everywhere the projection tallies host outcomes
    (see `host_rows` and `_task_line`). Centralising the rule keeps the
    two call sites from drifting apart.
    """
    return Status.CHANGED if hs.status == Status.OK and hs.changed else hs.status


def _host_leaf_label(hostname: str, hs: HostRunState, total: int | None = None) -> str:
    """Host-leaf label, with a loop-progress hint when live.

    A looped task tallies completed items per host (``loop_items_done``)
    from ``v2_runner_item_on_*`` events. While the loop runs we surface
    that count so the row isn't frozen at the task name for the whole loop.

    ansible never reports a loop's total up front, so the form depends on
    whether a matching prior run supplied one (``total``): ``N/total`` when
    known, else a bare ``(N items)``. Non-looped hosts (count 0) render the
    bare hostname.
    """
    if hs.loop_items_done <= 0:
        return hostname
    if total is not None and total > 0:
        return f"{hostname}  {hs.loop_items_done}/{total}"
    return f"{hostname}  ({hs.loop_items_done} items)"


def _runtime_role_from_task_name(task_name: str) -> str | None:
    """Infer an include_role-style runtime role from a task name.

    Accepts simple ``role : task`` prefixes where the role token has no
    whitespace. This intentionally rejects literal task names like
    ``Install foo : bar``.
    """
    if " : " not in task_name:
        return None
    prefix = task_name.split(" : ", 1)[0].strip()
    if not prefix or any(ch.isspace() for ch in prefix):
        return None
    return prefix


def _is_meta_task(task_name: str) -> bool:
    """Return True for explicit ``meta: ...`` tasks.

    This is a narrow projection-only heuristic: only meta tasks skip
    synthetic host-leaf fallback when their runtime host map is empty.
    """
    return strip_role_prefix(task_name).startswith("meta:")


@dataclass
class TreeProjection:
    """Pure projection of RunState. Build via `from_run_state`."""

    _state: RunState
    _role_index: dict[str, str] | None = field(default=None, init=False, repr=False)
    _known_roles: set[str] | None = field(default=None, init=False, repr=False)
    _runtime_role_counts: dict[str, int] | None = field(default=None, init=False, repr=False)
    _known_tree_revision: int | None = field(default=None, init=False, repr=False)
    _row_leases: dict[tuple[str, str], _RowLease] = field(
        default_factory=dict, init=False, repr=False
    )
    # Sticky fallback: the play_id of the most recent play with running
    # tasks. Persists between render calls so the tree stays stable during
    # transient gaps (e.g. between linear-strategy tasks).
    _last_running_play_id: str | None = field(default=None, init=False, repr=False)
    # Internal lease/sticky discriminator for serial/run_once windowed plays.
    _last_running_play_runtime_id: str | None = field(default=None, init=False, repr=False)

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

    def _refresh_tree_cache(self) -> None:
        """Refresh caches that depend on mutable ``RunState`` shape.

        ``RunState`` mutates in place, so durable projections need a
        lightweight change detector instead of being recreated on every
        event. ``_tree_revision`` advances when definitions change or a
        dynamic task is grafted.
        """
        revision = getattr(self._state, "_tree_revision", 0)
        if self._known_tree_revision == revision:
            return
        self._known_tree_revision = revision
        self._role_index = None
        self._known_roles = None
        self._runtime_role_counts = None

    @staticmethod
    def _task_definition_identity(task_def: "TaskDefinition") -> str:
        if task_def.uuid:
            return task_def.uuid
        if task_def.path:
            return task_def.path
        return f"{task_def.play_id}:{task_def.task_order}:{task_def.name}"

    @staticmethod
    def _task_runtime_identity(play: PlayRunState, task: TaskRunState) -> str:
        play_identity = TreeProjection._play_runtime_identity(play)
        task_identity = task.task_id or task.name
        return f"{play_identity}:{task_identity}"

    @staticmethod
    def _play_runtime_identity(play: PlayRunState) -> str:
        base = play.play_id or play.name
        window = play.window_start if play.window_start is not None else f"#{play.window_ordinal}"
        return f"{base}:{window}" if window else base

    @staticmethod
    def _play_sticky_identity(play: PlayRunState) -> str:
        return play.play_id or play.name

    def _remember_running_play(self, play: PlayRunState) -> None:
        self._last_running_play_id = self._play_sticky_identity(play)
        self._last_running_play_runtime_id = self._play_runtime_identity(play)

    def _touch_row_lease(self, kind: str, identity: str, now: datetime) -> None:
        if not identity:
            return
        lease = self._row_leases.get((kind, identity))
        expires_at = now + _ROW_LEASE_TTL
        if lease is None:
            self._row_leases[(kind, identity)] = _RowLease(last_seen_at=now, expires_at=expires_at)
        else:
            lease.last_seen_at = now
            lease.expires_at = expires_at

    def _touch_play_leases(
        self, runtime: PlayRunState | None, play_def: "PlayDefinition | None", now: datetime
    ) -> None:
        if runtime is not None:
            self._touch_row_lease("play", self._play_runtime_identity(runtime), now)
        elif play_def is not None and play_def.id:
            self._touch_row_lease("play", play_def.id, now)

    def _touch_task_lease(
        self,
        play: PlayRunState | None,
        runtime: TaskRunState | None,
        task_def: "TaskDefinition | None",
        now: datetime,
    ) -> None:
        if runtime is not None:
            if play is not None:
                self._touch_row_lease("task", self._task_runtime_identity(play, runtime), now)
            else:
                self._touch_row_lease("task", runtime.task_id or runtime.name, now)
            return
        if task_def is not None:
            self._touch_row_lease("task", self._task_definition_identity(task_def), now)

    def _touch_host_lease(self, hostname: str, now: datetime) -> None:
        self._touch_row_lease("host", hostname, now)

    def _touch_role_lease(self, role: str | None, now: datetime) -> None:
        if role is not None:
            self._touch_row_lease("role", role, now)

    def _prune_row_leases(self, now: datetime) -> None:
        expired = [key for key, lease in self._row_leases.items() if lease.expires_at <= now]
        for key in expired:
            del self._row_leases[key]

        if len(self._row_leases) <= _ROW_LEASE_LIMIT:
            return

        overflow = len(self._row_leases) - _ROW_LEASE_LIMIT
        for key, _ in sorted(
            self._row_leases.items(),
            key=lambda item: (item[1].last_seen_at, item[1].expires_at, item[0]),
        )[:overflow]:
            del self._row_leases[key]

    def _leased_play_id(
        self,
        ordered_plays: list[tuple[PlayRunState | None, "PlayDefinition | None"]],
        now: datetime,
    ) -> str | None:
        best: tuple[datetime, int, str] | None = None
        for index, (runtime, _play_def) in enumerate(ordered_plays):
            if runtime is None or not runtime.tasks:
                continue
            play_id = self._play_runtime_identity(runtime)
            lease = self._row_leases.get(("play", play_id))
            if lease is None or lease.expires_at <= now:
                continue
            candidate = (lease.last_seen_at, index, play_id)
            if best is None or candidate > best:
                best = candidate
        return best[2] if best is not None else None

    def _play_lease_alive(self, play_id: str, now: datetime) -> bool:
        lease = self._row_leases.get(("play", play_id))
        return lease is not None and lease.expires_at > now

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

        self._refresh_tree_cache()
        self._prune_row_leases(now)

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
            self._touch_host_lease(hostname, now)
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
          (a) truncate from the end (cut upcoming plays/tasks first)
          (b) drop host leaves under tasks (if still over budget)
          (c) collapse roles to "role: X  (N tasks running on K hosts)"

        The unbounded tree is ordered active-play-first, so truncating
        from the end preserves the deepest, most informative portion of
        the tree (the running play's role → task → host subtree) while
        upcoming plays get cut first. This is the key difference from
        "structural lines first" approaches, which consume the entire
        budget on play headers and leave no room for tasks or hosts.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        self._refresh_tree_cache()
        self._prune_row_leases(now)

        lines = self._tree_lines_unbounded(now)
        if len(lines) <= budget:
            self._prune_row_leases(now)
            return lines

        # --- Stage (a): truncate from the end --------------------------------
        lines = lines[:budget]
        if len(lines) <= budget:
            self._prune_row_leases(now)
            return lines

        # --- Stage (b): drop host leaves --------------------------------------
        lines = [ln for ln in lines if ln.kind != "host"]
        if len(lines) <= budget:
            self._prune_row_leases(now)
            return lines

        # --- Stage (c): collapse roles to summary lines -----------------------
        # Aggregate per-role running task count and unique running-host count
        # from current RunState.
        tasks_per_role: dict[str | None, int] = defaultdict(int)
        hosts_per_role: dict[str | None, set[str]] = defaultdict(set)
        for play in self._state.plays.values():
            for task in play.tasks.values():
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
                role_name = ln.identity or ln.label.removeprefix("role: ")
                n_tasks = tasks_per_role.get(role_name, 0)
                n_hosts = len(hosts_per_role.get(role_name, set()))
                task_word = "task" if n_tasks == 1 else "tasks"
                host_word = "host" if n_hosts == 1 else "hosts"
                collapsed.append(
                    TreeLine(
                        depth=ln.depth,
                        kind="role",
                        label=(
                            f"role: {role_name}"
                            f"  ({n_tasks} {task_word} running on {n_hosts} {host_word})"
                        ),
                        glyph=None,
                        status=None,
                        elapsed_s=None,
                        identity=role_name,
                    )
                )
                i += 1
                while i < len(lines) and lines[i].kind in ("task", "host"):
                    i += 1
            else:
                collapsed.append(ln)
                i += 1

        # Final hard-cap (safety net)
        if len(collapsed) > budget:
            collapsed = collapsed[:budget]

        self._prune_row_leases(now)

        return collapsed

    def _tree_lines_unbounded(self, now: datetime) -> list[TreeLine]:
        """Project full tree (no pruning). See ``tree_lines`` for entry point.

        Layout rule: each play shows tasks that are currently RUNNING and
        every task still to come (pending). Completed tasks are dropped —
        they already appear in the streaming log above the panel, so the
        tree's job is just "what's happening now and what's next".

        Upcoming plays (preflight entries with no runtime counterpart yet)
        are also emitted, in preflight order, so the user can see what
        comes after the in-flight play.
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
        self._touch_row_lease("playbook", self._state.playbook, now)

        # Iterate preflight plays in declared order so upcoming plays
        # land in the visual position the user will encounter them.
        # Runtime plays drive their own task projection; preflight-only
        # plays render their entire task list as pending. Any runtime
        # play whose name isn't in preflight (defensive: unusual but
        # possible) gets appended at the end.
        runtime_by_id: dict[str, PlayRunState] = {}
        runtime_by_name: dict[str, list[PlayRunState]] = defaultdict(list)
        for runtime_play in self._state.plays.values():
            if runtime_play.play_id:
                runtime_by_id.setdefault(runtime_play.play_id, runtime_play)
            runtime_by_name[runtime_play.name].append(runtime_play)
        seen_runtime_ids: set[str] = set()
        seen_runtime_objects: set[int] = set()

        ordered_plays: list[tuple[PlayRunState | None, "PlayDefinition | None"]] = []
        for preflight_play_def in self._state.definitions:
            runtime = None
            if preflight_play_def.id:
                runtime = runtime_by_id.get(preflight_play_def.id)
                if runtime is not None:
                    seen_runtime_ids.add(preflight_play_def.id)
            if runtime is None:
                for candidate in runtime_by_name.get(preflight_play_def.name, []):
                    if id(candidate) in seen_runtime_objects:
                        continue
                    runtime = candidate
                    break
            if runtime is not None:
                seen_runtime_objects.add(id(runtime))
            ordered_plays.append((runtime, preflight_play_def))
        for runtime_play in self._state.plays.values():
            if runtime_play.play_id and runtime_play.play_id in seen_runtime_ids:
                continue
            if id(runtime_play) in seen_runtime_objects:
                continue
            ordered_plays.append((runtime_play, None))

        # First pass: find the latest play with running items.
        fresh_found: PlayRunState | None = None
        for runtime, _ in ordered_plays:
            if runtime is not None:
                items = self._play_running_and_pending(runtime, include_cross_play=False)
                if any(k == "running" for k, _, _, _ in items):
                    fresh_found = runtime  # don't break — find latest

        if fresh_found is not None:
            self._remember_running_play(fresh_found)
            active_play_id: str | None = self._last_running_play_runtime_id
        elif self._last_running_play_runtime_id is not None and self._play_lease_alive(
            self._last_running_play_runtime_id, now
        ):
            active_play_id = self._last_running_play_runtime_id  # sticky from previous frame
        else:
            leased_play_id = self._leased_play_id(ordered_plays, now)
            if leased_play_id is not None:
                self._last_running_play_runtime_id = leased_play_id
                for runtime, _ in ordered_plays:
                    if (
                        runtime is not None
                        and self._play_runtime_identity(runtime) == leased_play_id
                    ):
                        self._remember_running_play(runtime)
                        break
                active_play_id = leased_play_id
            else:
                if self._last_running_play_runtime_id is None:
                    # Cold start: no running items anywhere and no sticky
                    # anchor yet. Pick the last runtime play with tasks so
                    # the tree doesn't go blank on the very first gap frame.
                    for runtime, _ in reversed(ordered_plays):
                        if runtime is not None and runtime.tasks:
                            self._remember_running_play(runtime)
                            active_play_id = self._last_running_play_runtime_id
                            break
                    else:
                        active_play_id = None
                else:
                    # The lease expired and no fresh running play replaced
                    # it. Keep the most recent active play pinned so quiet
                    # gaps do not widen back out to every completed play;
                    # row leases still age out independently.
                    active_play_id = self._last_running_play_runtime_id

        for runtime, play_def in ordered_plays:
            if runtime is not None:
                if active_play_id is not None:
                    if self._play_runtime_identity(runtime) != active_play_id:
                        items = self._play_running_and_pending(runtime, include_cross_play=False)
                        if not any(k == "running" for k, _, _, _ in items) and runtime.tasks:
                            continue  # completed play (had tasks, now all done)
                self._emit_runtime_play(lines, runtime, now)
            elif play_def is not None:
                self._emit_pending_play(lines, play_def, now)
        return lines

    def _emit_pending_play(
        self, lines: list[TreeLine], play_def: "PlayDefinition", now: datetime
    ) -> None:
        """Render an upcoming-only play: header + every preflight task as pending."""
        lines.append(
            TreeLine(
                depth=1,
                kind="play",
                label=f"play: {play_def.name}",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            )
        )
        self._touch_row_lease("play", play_def.id or play_def.name, now)
        role_counts: dict[str | None, int] = {}
        for entry, role in iter_preflight_task_defs(play_def.tasks):
            role_counts[role] = role_counts.get(role, 0) + 1
        current_role: str | None = None
        for tdef, role in iter_preflight_task_defs(play_def.tasks):
            if role != current_role:
                current_role = role
                if role is not None:
                    n = role_counts.get(role, 0)
                    task_count = f" ({n} task{'s' if n != 1 else ''})" if n > 0 else ""
                    lines.append(
                        TreeLine(
                            depth=2,
                            kind="role",
                            label=f"role: {role}{task_count}",
                            glyph=None,
                            status=None,
                            elapsed_s=None,
                            identity=role,
                        )
                    )
                    self._touch_role_lease(role, now)
            task_depth = 3 if role is not None else 2

            lines.append(
                TreeLine(
                    depth=task_depth,
                    kind="task",
                    label=tdef.name,
                    glyph=None,
                    status=Status.PENDING,
                    elapsed_s=None,
                )
            )
            self._touch_task_lease(None, None, tdef, now)

    def _emit_runtime_play(self, lines: list[TreeLine], play: PlayRunState, now: datetime) -> None:
        """Render a play that's already in flight (or was)."""
        play_items = self._play_running_and_pending(play)
        if not play_items:
            return

        running_items = [(k, n, r, rt) for k, n, r, rt in play_items if k == "running"]
        pending_items = [(k, n, r, rt) for k, n, r, rt in play_items if k != "running"]

        if not running_items and not pending_items:
            return

        play_items = running_items + pending_items

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
        # Count total tasks per role from definitions (not from play_items,
        # which drops completed tasks and would undercount).
        role_total_tasks: dict[str | None, int] = {}
        play_def = self._play_def_for(play)
        self._touch_play_leases(play, play_def, now)
        if play_def is not None:
            for entry, role in iter_preflight_task_defs(play_def.tasks):
                role_total_tasks[role] = role_total_tasks.get(role, 0) + 1
        # Also count runtime tasks per role that weren't in preflight.
        # include_role tasks appear at runtime but --list-tasks doesn't
        # expand them, so they're missing from play_def.
        emitted_preflight_names: set[str] = set()
        if play_def is not None:
            for entry, _ in iter_preflight_task_defs(play_def.tasks):
                emitted_preflight_names.add(entry.name)

        for task in play.tasks.values():
            stripped = strip_role_prefix(task.name)
            if task.name in emitted_preflight_names or stripped in emitted_preflight_names:
                continue
            # Check template match too
            is_template_matched = False
            for pn in emitted_preflight_names:
                if "{{" in pn and _is_template_match(pn, task.name):
                    is_template_matched = True
                    break
                if "{{" in pn and _is_template_match(pn, stripped):
                    is_template_matched = True
                    break
            if is_template_matched:
                continue
            task_role = _runtime_role_from_task_name(task.name)
            if task_role is not None:
                role_total_tasks[task_role] = role_total_tasks.get(task_role, 0) + 1
        for item_kind, name, role, runtime in play_items:
            effective_role = (
                role
                if role is not None
                else (_runtime_role_from_task_name(runtime.name) if runtime is not None else None)
            )

            if effective_role != current_role:
                current_role = effective_role
                role_open = effective_role is not None
                if role_open:
                    n = role_total_tasks.get(effective_role, 0)
                    if n == 0:
                        n = sum(
                            1
                            for task in play.tasks.values()
                            if _runtime_role_from_task_name(task.name) == effective_role
                        )
                    task_count = f" ({n} task{'s' if n != 1 else ''})" if n > 0 else ""
                    lines.append(
                        TreeLine(
                            depth=2,
                            kind="role",
                            label=f"role: {effective_role}{task_count}",
                            glyph=None,
                            status=None,
                            elapsed_s=None,
                            identity=effective_role,
                        )
                    )
                    self._touch_role_lease(effective_role, now)
            task_depth = 3 if role_open else 2

            if item_kind == "running" and runtime is not None:
                lines.append(self._task_line(runtime, depth=task_depth))
                self._touch_task_lease(play, runtime, None, now)
                if _is_meta_task(runtime.name):
                    # Meta tasks are projection-only control flow. Keep the
                    # task row visible, but never project host leaves.
                    pass
                elif runtime.hosts:
                    loop_totals = self._state.loop_totals.get(runtime.path or "", {})
                    for hostname, hs in runtime.hosts.items():
                        elapsed = (
                            (now - hs.start_time).total_seconds()
                            if hs.start_time is not None
                            else 0.0
                        )
                        lines.append(
                            TreeLine(
                                depth=task_depth + 1,
                                kind="host",
                                label=_host_leaf_label(hostname, hs, loop_totals.get(hostname)),
                                glyph=None,
                                status=hs.status,
                                elapsed_s=elapsed,
                            )
                        )
                        self._touch_host_lease(hostname, now)
                elif not _is_meta_task(runtime.name):
                    elapsed = (
                        (now - runtime.start_time).total_seconds() if runtime.start_time else 0.0
                    )
                    for hostname in sorted(_play_target_hostnames(play, play_def)):
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
                        self._touch_host_lease(hostname, now)
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
                self._touch_row_lease("task", name, now)

    def _play_running_and_pending(
        self, play: "PlayRunState", include_cross_play: bool = True
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
        runtime_by_name: dict[str, list[TaskRunState]] = defaultdict(list)
        runtime_by_path: dict[str, list[TaskRunState]] = defaultdict(list)
        for task in play.tasks.values():
            runtime_by_name[task.name].append(task)
            if task.path is not None:
                runtime_by_path[task.path].append(task)
            stripped = strip_role_prefix(task.name)
            if stripped != task.name:
                runtime_by_name[stripped].append(task)

        # Generic cross-play borrowing is intentionally disabled here.
        # Rows are built only from the current play's runtime tasks; any
        # explicit ownership model needs to be represented upstream.

        play_def = self._play_def_for(play)

        items: list[tuple[str, str, str | None, TaskRunState | None]] = []
        emitted_names: set[str] = set()
        emitted_task_ids: set[str] = set()

        def _task_identity(task: TaskRunState) -> str:
            return task.task_id or task.name

        def _classify(runtime: TaskRunState | None) -> str:
            """Return ``"running"`` / ``"pending"`` / ``"completed"``.

            ``"completed"`` is filtered out before items reach the caller,
            but the helper still returns it so the drop site can branch
            on a single classification result.

            A task with RUNNING status but no hosts yet (e.g. between
            ``v2_playbook_on_task_start`` and the first
            ``v2_runner_on_start``) is classified as ``"running"`` so the
            tree shows the correct ◐ icon and makes room for host leaves
            that will appear once runner events arrive.
            """
            if runtime is None:
                return "pending"
            if runtime.status == Status.COMPLETED:
                return "completed"
            if not runtime.hosts:
                return "running" if runtime.status == Status.RUNNING else "pending"
            if any(hs.status == Status.RUNNING for hs in runtime.hosts.values()):
                return "running"
            return "completed"

        def _pick_runtime(
            task_name: str,
            matched_runtime_task_ids: set[str],
            preferred_hosts: set[str] | None = None,
            task_path: str | None = None,
        ) -> TaskRunState | None:
            def _pick_best(candidates: list[TaskRunState]) -> TaskRunState | None:
                best: TaskRunState | None = None
                best_score = -1

                for candidate in candidates:
                    candidate_id = _task_identity(candidate)
                    if candidate_id in matched_runtime_task_ids:
                        continue

                    score = 0
                    if preferred_hosts:
                        score = len(preferred_hosts.intersection(candidate.hosts))

                    # Prefer the candidate that best matches the current
                    # branch's hosts; when scores tie, keep the earlier
                    # runtime arrival order.
                    if best is None or score > best_score:
                        best = candidate
                        best_score = score

                if best is not None:
                    matched_runtime_task_ids.add(_task_identity(best))
                return best

            # Exact task paths outrank name/host heuristics so same-named
            # delegated and non-delegated rows stay distinct.
            if task_path is not None:
                best = _pick_best(runtime_by_path.get(task_path, []))
                if best is not None:
                    return best

            candidates: list[TaskRunState] = []
            seen_candidate_ids: set[str] = set()

            def _append_candidates(candidate_name: str) -> None:
                for candidate in runtime_by_name.get(candidate_name, []):
                    candidate_id = _task_identity(candidate)
                    if candidate_id in seen_candidate_ids:
                        continue
                    seen_candidate_ids.add(candidate_id)
                    candidates.append(candidate)

            _append_candidates(task_name)
            if "{{" in task_name:
                for candidate_name, candidate_tasks in runtime_by_name.items():
                    stripped_candidate_name = strip_role_prefix(candidate_name)
                    if not _is_template_match(task_name, candidate_name) and not _is_template_match(
                        task_name, stripped_candidate_name
                    ):
                        continue
                    for candidate in candidate_tasks:
                        candidate_id = _task_identity(candidate)
                        if candidate_id in seen_candidate_ids:
                            continue
                        seen_candidate_ids.add(candidate_id)
                        candidates.append(candidate)

            return _pick_best(candidates)

        def _emit_preflight_entries(
            entries: Iterable[TaskDefinition | RoleGroupDefinition],
            inherited_role: str | None,
            preferred_hosts: set[str] | None,
            matched_runtime_task_ids: set[str],
        ) -> None:
            for entry in entries:
                if isinstance(entry, RoleGroupDefinition):
                    _emit_preflight_entries(
                        entry.tasks, entry.role, preferred_hosts, matched_runtime_task_ids
                    )
                    continue

                role = entry.role if entry.role is not None else inherited_role
                runtime = _pick_runtime(
                    entry.name, matched_runtime_task_ids, preferred_hosts, entry.path
                )
                if runtime is None and "{{" in entry.name:
                    # Preflight name has unresolved Jinja2 template — try
                    # to find a runtime task whose resolved name matches
                    # the template skeleton.
                    for candidate_name in runtime_by_name:
                        stripped_candidate_name = strip_role_prefix(candidate_name)
                        if not _is_template_match(
                            entry.name, candidate_name
                        ) and not _is_template_match(entry.name, stripped_candidate_name):
                            continue
                        runtime = _pick_runtime(
                            candidate_name, matched_runtime_task_ids, preferred_hosts
                        )
                        if runtime is not None:
                            break

                kind = _classify(runtime)
                emitted_names.add(entry.name)
                next_preferred_hosts = preferred_hosts
                if runtime is not None:
                    # Emit under the runtime (resolved) name so host
                    # leaves and status are correct.
                    emitted_names.add(runtime.name)
                    emitted_task_ids.add(_task_identity(runtime))
                    stripped = strip_role_prefix(runtime.name)
                    if stripped != runtime.name:
                        emitted_names.add(stripped)
                    if runtime.hosts:
                        next_preferred_hosts = set(runtime.hosts)
                if kind != "completed":
                    items.append((kind, entry.name, role, runtime))

                if entry.children:
                    _emit_preflight_entries(
                        entry.children, role, next_preferred_hosts, matched_runtime_task_ids
                    )

        if play_def is not None:
            matched_runtime_task_ids: set[str] = set()
            _emit_preflight_entries(play_def.tasks, None, None, matched_runtime_task_ids)

        # Runtime-only tasks (dynamic include_tasks, or no preflight at all).
        for task in play.tasks.values():
            task_identity = _task_identity(task)
            if task_identity in emitted_task_ids:
                continue
            kind = _classify(task)
            if kind == "completed":
                continue
            items.append((kind, task.name, _runtime_role_from_task_name(task.name), task))
            emitted_names.add(task.name)
            emitted_task_ids.add(task_identity)
            stripped = strip_role_prefix(task.name)
            if stripped != task.name:
                emitted_names.add(stripped)

        return items

    def _play_def_for(self, play: "PlayRunState") -> "PlayDefinition | None":
        """Return the matching preflight PlayDefinition, or None.

        Prefer stable play execution identity (play_id) when available.
        Fall back to display-name matching only for legacy/partial event
        streams that lack a stable id.
        """
        by_id = self._state._play_def_by_id
        if by_id is not None and play.play_id:
            match = by_id.get(play.play_id)
            if match is not None:
                return match
        by_name = self._state._play_def_by_name
        if by_name is None:
            return None
        return by_name.get(play.name)

    def _task_role(self, task_name: str) -> str | None:
        """Return the role name a task belongs to, or None.

        Preflight ``--list-tasks`` records role membership both via
        ``RoleGroupDefinition`` (grouped, 5+ consecutive same-role) and
        ``TaskDefinition.role`` (ungrouped, <5 tasks). First match wins.
        Memoised on first call.

        Runtime task names may carry the ``"role : "`` prefix
        (e.g. ``"podman : Install Podman"``); the stripped form is
        also tried so that lookups succeed against the preflight index
        which stores bare task names.
        """
        self._refresh_tree_cache()
        if self._role_index is None:
            idx: dict[str, str] = {}
            known_roles: set[str] = set()
            for play_def in self._state.definitions:
                for task_def, role in iter_preflight_task_defs(play_def.tasks):
                    if role is not None:
                        idx.setdefault(task_def.name, role)
                        known_roles.add(role)
            runtime_role_counts: dict[str, int] = defaultdict(int)
            for play in self._state.plays.values():
                for task in play.tasks.values():
                    if " : " in task.name:
                        runtime_role = task.name.split(" : ", 1)[0].strip()
                        if runtime_role:
                            runtime_role_counts[runtime_role] += 1
            self._role_index = idx
            self._known_roles = known_roles
            self._runtime_role_counts = runtime_role_counts
        result = self._role_index.get(task_name)
        if result is None:
            result = self._role_index.get(strip_role_prefix(task_name))
        if result is None:
            # Try template-variable match: runtime name "Get ID for
            # angie-sidecar" vs index key "Get ID for {{ username }}".
            for preflight_name, role_name in self._role_index.items():
                if _is_template_match(preflight_name, task_name):
                    return role_name
        if result is None and " : " in task_name:
            # Runtime "role : task" prefix with no preflight entry —
            # extract role name directly from the prefix (include_role).
            # Only accept if the role was seen in preflight or repeated
            # across runtime tasks (avoids false positives from task names
            # that happen to contain " : ").
            role_from_prefix = task_name.split(" : ", 1)[0].strip()
            if not role_from_prefix or any(ch.isspace() for ch in role_from_prefix):
                return result
            if self._known_roles is not None and role_from_prefix in self._known_roles:
                return role_from_prefix
            if (
                self._runtime_role_counts is not None
                and self._runtime_role_counts.get(role_from_prefix, 0) > 1
            ):
                return role_from_prefix
        return result

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
