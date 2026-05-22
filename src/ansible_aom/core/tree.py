"""Pure projection of RunState into renderable tree + host-row data.

This module contains *no* I/O, no ANSI, no terminal awareness. It is
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
    strip_role_prefix,
)

TreeKind = Literal["playbook", "play", "role", "task", "host"]

_TEMPLATE_RE = __import__("re").compile(r"\{\{.*?\}\}")


def _template_skeleton(name: str) -> str:
    """Strip ``{{ ... }}`` from a task name, yielding the static parts.

    ``--list-tasks`` preserves Jinja2 templates verbatim
    (e.g. ``"Get ID for {{ user }}"``). The JSONL callback sends
    the resolved value (``"Get ID for angie-sidecar"``).
    ``_template_skeleton`` returns ``"Get ID for"`` — the parts
    that are guaranteed identical between preflight and runtime.
    Multiple whitespace runs are collapsed so that ``"user  exists"``
    (from stripping ``{{ username }}``) becomes ``"user exists"``."""
    return __import__("re").sub(r"\s+", " ", _TEMPLATE_RE.sub("", name)).strip()


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
    _known_roles: set[str] | None = field(default=None, init=False, repr=False)

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

        lines = self._tree_lines_unbounded(now)
        if len(lines) <= budget:
            return lines

        # --- Stage (a): truncate from the end --------------------------------
        lines = lines[:budget]
        if len(lines) <= budget:
            return lines

        # --- Stage (b): drop host leaves --------------------------------------
        lines = [ln for ln in lines if ln.kind != "host"]
        if len(lines) <= budget:
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
                        label=(f"role: {role_name}  ({n_tasks} {task_word} running on {n_hosts} {host_word})"),
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

        # Iterate preflight plays in declared order so upcoming plays
        # land in the visual position the user will encounter them.
        # Runtime plays drive their own task projection; preflight-only
        # plays render their entire task list as pending. Any runtime
        # play whose name isn't in preflight (defensive: unusual but
        # possible) gets appended at the end.
        runtime_by_name: dict[str, PlayRunState] = {}
        for runtime_play in self._state.plays.values():
            runtime_by_name.setdefault(runtime_play.name, runtime_play)
        seen_runtime_names: set[str] = set()

        ordered_plays: list[tuple[PlayRunState | None, "PlayDefinition | None"]] = []
        for play_def in self._state.definitions:
            runtime = runtime_by_name.get(play_def.name)
            if runtime is not None:
                seen_runtime_names.add(play_def.name)
            ordered_plays.append((runtime, play_def))
        for runtime_play in self._state.plays.values():
            if runtime_play.name in seen_runtime_names:
                continue
            ordered_plays.append((runtime_play, None))

        for runtime, play_def in ordered_plays:
            if runtime is not None:
                self._emit_runtime_play(lines, runtime, now)
            elif play_def is not None:
                self._emit_pending_play(lines, play_def)
        return lines

    def _emit_pending_play(self, lines: list[TreeLine], play_def: "PlayDefinition") -> None:
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
        current_role: str | None = None
        for entry in play_def.tasks:
            if isinstance(entry, RoleGroupDefinition):
                role: str | None = entry.role
                task_defs = entry.tasks
            else:
                role = entry.role
                task_defs = [entry]
            if role != current_role:
                current_role = role
                if role is not None:
                    # For bare TaskDefinition entries with a role, count
                    # all same-role entries across the play (not just the
                    # current entry, which would always be 1).
                    n = len(task_defs) if isinstance(entry, RoleGroupDefinition) else sum(
                        1 for e in play_def.tasks
                        if not isinstance(e, RoleGroupDefinition) and e.role == role
                    )
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
            task_depth = 3 if role is not None else 2
            for tdef in task_defs:
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

    def _emit_runtime_play(self, lines: list[TreeLine], play: PlayRunState, now: datetime) -> None:
        """Render a play that's already in flight (or was)."""
        play_items = self._play_running_and_pending(play)
        if not play_items:
            return

        # Stable partition: running items first, then pending.
        # This ensures the active task and its host leaves are near the
        # top of the tree, so truncation-from-end cuts pending content
        # rather than the currently running task.
        running_items = [(k, n, r, rt) for k, n, r, rt in play_items if k == "running"]
        pending_items = [(k, n, r, rt) for k, n, r, rt in play_items if k != "running"]
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
        if play_def is not None:
            for entry in play_def.tasks:
                if isinstance(entry, RoleGroupDefinition):
                    n = len(entry.tasks)
                    role_total_tasks[entry.role] = role_total_tasks.get(entry.role, 0) + n
                elif entry.role is not None:
                    role_total_tasks[entry.role] = role_total_tasks.get(entry.role, 0) + 1
                else:
                    role_total_tasks[None] = role_total_tasks.get(None, 0) + 1
        # Also count runtime tasks per role that weren't in preflight.
        # include_role tasks appear at runtime but --list-tasks doesn't
        # expand them, so they're missing from play_def.
        emitted_preflight_names: set[str] = set()
        if play_def is not None:
            for entry in play_def.tasks:
                if isinstance(entry, RoleGroupDefinition):
                    for td in entry.tasks:
                        emitted_preflight_names.add(td.name)
                else:
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
            task_role = self._task_role(task.name)
            if task_role is not None:
                role_total_tasks[task_role] = role_total_tasks.get(task_role, 0) + 1
        for item_kind, name, role, runtime in play_items:
            if role != current_role:
                current_role = role
                role_open = role is not None
                if role_open:
                    n = role_total_tasks.get(role, 0)
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
            task_depth = 3 if role_open else 2

            if item_kind == "running" and runtime is not None:
                lines.append(self._task_line(runtime, depth=task_depth))
                for hostname, hs in runtime.hosts.items():
                    elapsed = (
                        (now - hs.start_time).total_seconds() if hs.start_time is not None else 0.0
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
            runtime_by_name[task.name] = task
            stripped = strip_role_prefix(task.name)
            if stripped != task.name:
                runtime_by_name[stripped] = task
        for p in self._state.plays.values():
            if p.play_id == play.play_id:
                continue
            for task in p.tasks.values():
                runtime_by_name.setdefault(task.name, task)
                stripped = strip_role_prefix(task.name)
                if stripped != task.name:
                    runtime_by_name.setdefault(stripped, task)

        play_def = self._play_def_for(play)

        items: list[tuple[str, str, str | None, TaskRunState | None]] = []
        emitted_names: set[str] = set()

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

        if play_def is not None:
            matched_runtime_tasks: set[str] = set()
            for entry in play_def.tasks:
                if isinstance(entry, RoleGroupDefinition):
                    role: str | None = entry.role
                    task_defs = entry.tasks
                else:
                    role = entry.role
                    task_defs = [entry]
                for tdef in task_defs:
                    runtime = runtime_by_name.get(tdef.name)
                    if runtime is None and "{{" in tdef.name:
                        # Preflight name has unresolved Jinja2 template —
                        # try to find a runtime task whose resolved name
                        # matches the template skeleton.
                        for rt_name, rt in runtime_by_name.items():
                            if rt_name in matched_runtime_tasks:
                                continue
                            if _is_template_match(tdef.name, rt_name):
                                runtime = rt
                                matched_runtime_tasks.add(rt_name)
                                break
                        if runtime is not None:
                            # Also try with role prefix stripped
                            for rt_name, rt in runtime_by_name.items():
                                if rt_name in matched_runtime_tasks:
                                    continue
                                stripped_rt = strip_role_prefix(rt_name)
                                if (
                                    stripped_rt != rt_name
                                    and _is_template_match(tdef.name, stripped_rt)
                                ):
                                    runtime = rt
                                    matched_runtime_tasks.add(rt_name)
                                    break
                    kind = _classify(runtime)
                    emitted_names.add(tdef.name)
                    if runtime is not None:
                        # Emit under the runtime (resolved) name so host
                        # leaves and status are correct.
                        emitted_names.add(runtime.name)
                        stripped = strip_role_prefix(runtime.name)
                        if stripped != runtime.name:
                            emitted_names.add(stripped)
                    if kind == "completed":
                        continue
                    items.append((kind, tdef.name, role, runtime))

        # Runtime-only tasks (dynamic include_tasks, or no preflight at all).
        for task in play.tasks.values():
            if task.name in emitted_names or strip_role_prefix(task.name) in emitted_names:
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

        Preflight ``--list-tasks`` records role membership both via
        ``RoleGroupDefinition`` (grouped, 5+ consecutive same-role) and
        ``TaskDefinition.role`` (ungrouped, <5 tasks). First match wins.
        Memoised on first call.

        Runtime task names may carry the ``"role : "`` prefix
        (e.g. ``"podman : Install Podman"``); the stripped form is
        also tried so that lookups succeed against the preflight index
        which stores bare task names.
        """
        if self._role_index is None:
            idx: dict[str, str] = {}
            known_roles: set[str] = set()
            for play_def in self._state.definitions:
                for entry in play_def.tasks:
                    if isinstance(entry, RoleGroupDefinition):
                        for task_def in entry.tasks:
                            idx.setdefault(task_def.name, entry.role)
                        known_roles.add(entry.role)
                    elif entry.role is not None:
                        idx.setdefault(entry.name, entry.role)
                        known_roles.add(entry.role)
            # Also collect roles from runtime task names (include_role /
            # dynamic tasks not in preflight). These have "role : task" prefix.
            for play in self._state.plays.values():
                for task in play.tasks.values():
                    if " : " in task.name:
                        runtime_role = task.name.split(" : ", 1)[0].strip()
                        if runtime_role:
                            known_roles.add(runtime_role)
            self._role_index = idx
            self._known_roles = known_roles
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
            # Only accept if the role was seen elsewhere in the play (avoids
            # false positives from task names that happen to contain " : ").
            role_from_prefix = task_name.split(" : ", 1)[0].strip()
            if role_from_prefix and self._known_roles is not None and role_from_prefix in self._known_roles:
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
