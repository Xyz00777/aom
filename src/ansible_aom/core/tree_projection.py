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
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Literal

from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RoleGroupDefinition,
    Status,
    TaskDefinition,
    TaskRunState,
    _is_template_match,
    iter_preflight_task_defs,
    runtime_role_from_task_name,
    strip_role_prefix,
)
from ansible_aom.core.run_state import RunState

TreeKind = Literal["playbook", "play", "role", "task", "host", "more"]

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


def _collapse_role_path(role_path: tuple[str, ...]) -> tuple[str, ...]:
    """Collapse consecutive duplicate role names in a path.

    ``iter_preflight_task_defs`` produces ``(A, A)`` for a task whose
    ``role`` field matches the enclosing ``RoleGroupDefinition``'s
    role. The projection wants one ``role:`` header per unique
    nesting level, not one per element — so ``(A, A)`` collapses to
    ``(A,)`` here. Non-consecutive duplicates (``(A, B, A)``) are
    preserved because they represent a legitimate re-entry into a
    role after a sibling role.
    """
    if len(role_path) < 2:
        return role_path
    collapsed: list[str] = [role_path[0]]
    for role in role_path[1:]:
        if role != collapsed[-1]:
            collapsed.append(role)
    return tuple(collapsed)


def _collapse_role_path_aggressive(role_path: tuple[str, ...]) -> tuple[str, ...]:
    """Drop any element that duplicates an earlier element of the path.

    Stricter than ``_collapse_role_path``: ``(A, B, A)`` becomes
    ``(A, B)``, not just ``(A, B, A)``. Used as the final pass in
    ``_extend_role_path`` to defend against non-consecutive duplicates
    introduced when concatenating a preflight path with a runtime
    name chain (e.g. ``("podman", "angie_ssl_terminator")`` + ``("podman",)``
    → ``("podman", "angie_ssl_terminator", "podman")``, which would
    render a duplicate ``role: podman`` header). Any element whose
    value already appears earlier in the path is skipped, so the
    projection emits one ``role:`` header per unique nesting level
    regardless of how the chain was assembled.
    """
    if len(role_path) < 2:
        return role_path
    collapsed: list[str] = [role_path[0]]
    seen: set[str] = {role_path[0]}
    for role in role_path[1:]:
        if role in seen:
            continue
        collapsed.append(role)
        seen.add(role)
    return tuple(collapsed)


def _name_role_chain(name: str) -> tuple[str, ...]:
    """Extract the role chain encoded in a task name's ``" : "`` segments.

    ansible emits runtime task names like ``"podman : Install Podman"``
    for tasks inside a role. A name with multiple segments encodes a
    *chain* of roles: each segment before the last is a role (outermost
    to innermost), and the last segment is the actual task description.
    ``"Install nginx"`` returns ``()`` (no chain); ``"podman : Install
    Podman"`` returns ``("podman",)``; ``"D : leaf : actually do the
    thing"`` returns ``("D", "leaf")``.

    Segments containing whitespace are rejected (matches
    ``runtime_role_from_task_name``'s gate against literal task names
    like ``"Install foo : bar"`` which happen to contain the
    separator). The chain terminates at the first whitespace-bearing
    segment.
    """
    if " : " not in name:
        return ()
    chain: list[str] = []
    for segment in name.split(" : ")[:-1]:
        if not segment or any(ch.isspace() for ch in segment):
            break
        chain.append(segment)
    return tuple(chain)


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


def _cluster_items_by_role_path(
    items: list[tuple[str, str, tuple[str, ...], TaskRunState | None]],
) -> list[tuple[str, str, tuple[str, ...], TaskRunState | None]]:
    """Group items so tasks sharing the same role branch stay contiguous,
    preventing multi-host concurrency from repeatedly opening and closing
    role headers.
    """
    if not items:
        return items

    by_path: dict[tuple[str, ...], list[tuple[str, str, tuple[str, ...], TaskRunState | None]]] = (
        defaultdict(list)
    )
    path_order: list[tuple[str, ...]] = []
    for item in items:
        rpath = item[2]
        if rpath not in by_path:
            path_order.append(rpath)
        by_path[rpath].append(item)

    clustered: list[tuple[str, str, tuple[str, ...], TaskRunState | None]] = []
    emitted_paths: set[tuple[str, ...]] = set()

    def _emit_path_and_descendants(target_path: tuple[str, ...]) -> None:
        if target_path in emitted_paths:
            return
        emitted_paths.add(target_path)

        # Check if any descendant has running items
        descendants = [
            p
            for p in path_order
            if p not in emitted_paths
            and len(p) > len(target_path)
            and p[: len(target_path)] == target_path
        ]
        running_descendants = [
            p for p in descendants if any(it[0] == "running" for it in by_path[p])
        ]
        pending_descendants = [p for p in descendants if p not in running_descendants]

        # 1. Emit running descendants first so active work is visible at the top
        for p in running_descendants:
            _emit_path_and_descendants(p)

        # 2. Emit target path items
        if target_path in by_path:
            clustered.extend(by_path[target_path])

        # 3. Emit remaining pending descendants
        for p in pending_descendants:
            _emit_path_and_descendants(p)

    for p in path_order:
        if p not in emitted_paths:
            root = (p[0],) if p else ()
            if root not in emitted_paths and root in by_path:
                _emit_path_and_descendants(root)
            else:
                _emit_path_and_descendants(p)

    return clustered


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

    `has_tail_after` is True when a "more tasks" footer follows this
    line at the same or deeper depth. The renderer uses it to demote
    this line's branch glyph from `└─` to `├─` and keep the parent spine
    running so the cut is visually traceable from the top of the window
    down to the footer. False everywhere else (the common case).
    """

    depth: int
    kind: TreeKind
    label: str
    glyph: str | None
    status: Status | None
    elapsed_s: float | None
    identity: str | None = None
    has_tail_after: bool = False


@dataclass(frozen=True)
class HostRow:
    """One row in the per-host summary table.

    `counts` only carries non-zero entries. `worst_status` drives the
    hostname colour selection per the spec; `current_task` is None when
    the host is idle (between tasks) or after the run finishes.

    `failed_task` / `failed_status` carry the name and status of the most
    recent terminal failure on this host (FAILED or UNREACHABLE). They
    are set only when the host is not currently RUNNING — a running task
    always takes display precedence over a past failure.
    """

    hostname: str
    counts: dict[Status, int]
    worst_status: Status | None
    current_task: str | None
    current_elapsed_s: float | None
    failed_task: str | None = None
    failed_status: Status | None = None


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
    if hs.poll_hint:
        return f"{hostname}  ({hs.poll_hint})"
    if hs.loop_items_done <= 0:
        return hostname
    if total is not None and total > 0:
        return f"{hostname}  {hs.loop_items_done}/{total}"
    return f"{hostname}  ({hs.loop_items_done} items)"


def _leaf_visible(hs: HostRunState) -> bool:
    """Host-leaf visibility under a running task.

    RUNNING leaves are the tree's payload; FAILED/UNREACHABLE leaves
    stay visible because a failure is the actionable signal (mirrors
    the failed-task keep-visible rule in ``_classify``). OK/CHANGED/
    SKIPPED hosts drop off — their result lines already streamed to
    the log above the panel and the task-line summary counts them.
    """
    return hs.status in (Status.RUNNING, Status.FAILED, Status.UNREACHABLE)


def _leaf_elapsed_s(hs: HostRunState, now: datetime) -> float:
    """Per-host elapsed seconds for a host leaf.

    Running hosts tick against ``now``; terminal hosts freeze at
    ``end_time - start_time`` (how long the host actually took).
    """
    if hs.status == Status.RUNNING:
        return (now - hs.start_time).total_seconds() if hs.start_time is not None else 0.0
    if hs.start_time is not None and hs.end_time is not None:
        return (hs.end_time - hs.start_time).total_seconds()
    return 0.0


def _pending_host_count(
    play: "PlayRunState", play_def: "PlayDefinition | None", runtime: TaskRunState
) -> int:
    """Play-target hosts that have not started ``runtime`` yet.

    Under ``throttle``/``serial``/free strategy a task's host map only
    grows as per-host start events arrive; the difference against the
    play's target set is the "not yet started" tail. Hosts that went
    FAILED/UNREACHABLE earlier in the play are excluded — ansible
    removes them from the play, so they will never start this task.
    Returns 0 when no target information is available.
    """
    targets = _play_target_hostnames(play, play_def)
    if not targets:
        return 0
    dead = {
        hostname
        for task in play.tasks.values()
        for hostname, hs in task.hosts.items()
        if hs.status in (Status.FAILED, Status.UNREACHABLE)
    }
    return len(targets - set(runtime.hosts) - dead)


def _play_def_for_state(run_state: "RunState", play: "PlayRunState") -> "PlayDefinition | None":
    """Resolve a runtime play to its preflight PlayDefinition.

    Mirrors ``TreeProjection._play_def_for`` minus the tree-construction
    mapping (which isn't available outside a projection): id first, then
    name. Returns None when no definitions were supplied.
    """
    by_id = run_state._play_def_by_id
    if by_id is not None and play.play_id:
        match = by_id.get(play.play_id)
        if match is not None:
            return match
    by_name = run_state._play_def_by_name
    if by_name is not None:
        return by_name.get(play.name)
    return None


def play_dead_hosts(play: "PlayRunState") -> set[str]:
    """Hosts that went FAILED/UNREACHABLE anywhere in ``play``.

    Ansible drops these hosts from the play, so they never reach later
    tasks. O(tasks × hosts) — callers on hot paths should memoise (see
    the ``dead_by_play`` parameter of ``task_complete_on_all_targets``).
    """
    return {
        hostname
        for t in play.tasks.values()
        for hostname, hs in t.hosts.items()
        if hs.status in (Status.FAILED, Status.UNREACHABLE)
    }


def task_complete_on_all_targets(
    run_state: "RunState",
    task_uuid: str,
    *,
    dead_by_play: dict[str, set[str]] | None = None,
    fan_out_groups: dict[tuple[str, str, str], set[str]] | None = None,
) -> bool:
    """True when every live target host has finished ``task_uuid``.

    "Live targets" = the task's play target host set (preflight
    ``resolved_hosts`` when available, else the runtime union) minus
    hosts that went FAILED/UNREACHABLE anywhere in the play (ansible
    drops them, so they never reach later tasks). The task is complete
    only when every live target has a terminal (non-RUNNING) entry in it.

    This is deliberately stricter than "all *started* hosts terminal":
    under a free/host-pinned strategy the started set fills gradually
    (fork limit) and a host can start a task minutes after its peers
    finished it, so the started set undercounts. Anchoring on the target
    set is what makes the per-task summary reflect the whole play instead
    of whichever cohort happened to have reported first.

    Some free-strategy implementations assign a separate UUID to each
    host for a dynamically included task. ``fan_out_groups`` maps the
    shared ``(play_id, task name, task path)`` identity to those UUIDs.
    For groups with multiple members, completion instead covers the union
    of hosts observed across every member: every live host in that union
    must have a terminal entry in at least one member. Missing and
    singleton groups retain the target-set behavior above unchanged.

    ``dead_by_play`` is an optional memo dict (play_id → dead-host set)
    filled lazily. The dead-host scan is O(play tasks × hosts); without a
    memo, a caller checking many tasks per event re-pays it per call —
    the quadratic sweep behind the free-strategy display freeze. The
    CALLER owns invalidation: entries must be dropped whenever a host
    dies (failed/unreachable), a play (re)starts, or a formerly-dead
    host's result is overwritten (retry recovery).

    Returns False when the task is unknown, or when neither target
    information nor a multi-member fan-out host union is available yet.
    Callers treat "can't tell" as "not complete" and fall back to the
    run-end forced flush.
    """
    for play in run_state.plays.values():
        task = play.tasks.get(task_uuid)
        if task is None:
            continue
        play_def = _play_def_for_state(run_state, play)
        targets = _play_target_hostnames(play, play_def)
        fan_out_members: set[str] | None = None
        if fan_out_groups is not None and task.path:
            members = fan_out_groups.get((play.play_id, task.name, task.path))
            if members is not None and len(members) > 1:
                fan_out_members = members
        if not targets and fan_out_members is None:
            return False
        # A host that died *before* reaching this task never runs it and
        # must not block completion. One that died *in* this task has a
        # terminal entry here — it finished (by failing) and is counted
        # normally by the loop below.
        if dead_by_play is not None:
            dead = dead_by_play.get(play.play_id)
            if dead is None:
                dead = play_dead_hosts(play)
                dead_by_play[play.play_id] = dead
        else:
            dead = play_dead_hosts(play)

        if fan_out_members is not None:
            group_hosts: set[str] = set()
            terminal_hosts: set[str] = set()
            for member_uuid in fan_out_members:
                member = play.tasks.get(member_uuid)
                if member is None:
                    continue
                group_hosts.update(member.hosts)
                terminal_hosts.update(
                    hostname
                    for hostname, host_state in member.hosts.items()
                    if host_state.status != Status.RUNNING
                )
            live_group_hosts = group_hosts - dead
            return bool(group_hosts) and live_group_hosts <= terminal_hosts

        # Build map of task order index in this play to check if hosts have advanced past task_uuid
        task_order = {tid: idx for idx, tid in enumerate(play.tasks)}
        current_idx = task_order.get(task_uuid, -1)

        for hostname in targets:
            hs = task.hosts.get(hostname)
            if hs is not None:
                if hs.status == Status.RUNNING and not (
                    hs.synthesised and play.detected_strategy == "free"
                ):
                    return False  # still running this task
            elif hostname not in dead:
                # If hostname has already started or completed any task strictly
                # after task_uuid in this play, it has passed task_uuid and won't run it.
                has_passed = False
                if current_idx >= 0:
                    for later_tid in list(play.tasks.keys())[current_idx + 1 :]:
                        if hostname in play.tasks[later_tid].hosts:
                            has_passed = True
                            break
                if not has_passed:
                    return False  # hasn't reached this task yet, and still alive
        return True

    return False


def _is_meta_task(task_name: str) -> bool:
    """Return True for explicit ``meta: ...`` tasks.

    This is a narrow projection-only heuristic: only meta tasks skip
    synthetic host-leaf fallback when their runtime host map is empty.
    """
    return strip_role_prefix(task_name).startswith("meta:")


def _more_footer(depth: int, count: int) -> TreeLine:
    """Build a "… and N more tasks" footer TreeLine.

    The footer uses ``kind="more"`` (T1's new literal) so the renderer
    can recognise it and suppress its branch glyph (T4 will add the
    special case). The depth carries the visual position the footer
    sits at — ``0`` for the outer footer (full-tree summary) and the
    deepest visible task's depth for the inner footer (active-role
    summary). ``status=Status.PENDING`` matches the existing single-cut
    footer so the colour stays consistent. ``count`` is the number of
    hidden task lines represented by
    this footer.
    """
    return TreeLine(
        depth=depth,
        kind="more",
        label=f"… and {count} more tasks",
        glyph=None,
        status=Status.PENDING,
        elapsed_s=None,
    )


def _count_domain_entities(lines: list[TreeLine]) -> int:
    """Count hidden task lines for the "X more tasks" footer."""
    return sum(1 for ln in lines if ln.kind == "task")


def _truncate_two_level(unbounded: list[TreeLine], budget: int) -> list[TreeLine]:
    """Two-cut truncation. See ``.sisyphus/plans/two-level-truncation.md`` T2.

    The algorithm finds the first play-line at or after ``budget - 1``
    and treats that as the "outer cut" — everything before is the
    "head" and kept verbatim, everything from there on is the "outer
    tail" and collapsed into the outer footer. Within the budget left
    for the inner section, the cut can land inside a role's task list;
    in that case an inner footer at the role's task depth is emitted
    with the count of hidden task-domain entities. If the outer cut
    falls cleanly between plays (no role was partially visible), only
    the outer footer is emitted.

    Marks ``has_tail_after=True`` on the last line of ``head`` and the
    last visible line before the inner footer so the renderer can
    demote their glyphs from ``└─`` to ``├─`` and keep the parent spine
    running. The outer footer carries ``kind="more"`` at ``depth=0``;
    the inner footer (when emitted) carries ``kind="more"`` at the
    deepest visible task's depth.

    Falls back to the pre-T2 single-footer behavior (one ``kind="more"``
    footer at depth 0) when no play boundary exists within the budget
    window or when ``head`` alone overflows the budget — the contract
    "the user always sees an 'and N more tasks' indicator" must hold.
    """
    if len(unbounded) <= budget:
        return list(unbounded)

    # Step 1: find the outer cut — the first play-line at or after
    # ``budget - 1``. Walking backward from ``budget - 1`` keeps the
    # "truncate from the end" invariant (cuts the tail, not the head).
    budget_idx = budget - 1
    head_end = budget_idx
    while head_end > 0 and unbounded[head_end].kind != "play":
        head_end -= 1

    if head_end == 0:
        # No play boundary within the window — degenerate. Fall back
        # to single-footer behavior so we never break the contract.
        keep = budget - 1
        dropped = unbounded[keep:]
        dropped_count = _count_domain_entities(dropped)
        return list(unbounded[:keep]) + [_more_footer(depth=0, count=dropped_count)]

    head = list(unbounded[:head_end])
    outer_tail = unbounded[head_end:]
    # Reserve two lines for the footers: one inner footer at the active
    # role's depth, one outer footer at depth 0. The inner section's
    # visible lines (the active role + first few tasks) live between
    # them. With the pre-T2 single-footer contract, the cut-inside-role
    # branch produces exactly ``budget`` lines so existing
    # ``len(lines) <= budget`` tests keep passing.
    inner_budget = budget - len(head) - 2
    if inner_budget < 0:
        # head alone is over budget — degenerate. Fall back to
        # single-footer behavior.
        keep = budget - 1
        dropped = unbounded[keep:]
        dropped_count = _count_domain_entities(dropped)
        return list(unbounded[:keep]) + [_more_footer(depth=0, count=dropped_count)]

    inner_dropped_lines = outer_tail[inner_budget:]
    inner_dropped = _count_domain_entities(inner_dropped_lines)

    if inner_budget == 0 or inner_dropped == 0:
        # No inner cut — either the outer_tail fit completely
        # (inner_dropped == 0) or the budget was fully consumed by the
        # head so there's no room for an inner section (inner_budget
        # == 0). In both cases the cut landed cleanly between plays;
        # skip the inner footer and emit a single outer footer only.
        keep = budget - 1
        result = list(unbounded[:keep])
        if result:
            result[-1] = replace(result[-1], has_tail_after=True)
        dropped = unbounded[keep:]
        result.append(_more_footer(depth=0, count=_count_domain_entities(dropped)))
        return result

    # Cut inside the active role: emit the inner section + inner footer.
    # Mark EVERY line in the inner section with ``has_tail_after=True`` so
    # the renderer demotes every ancestor's branch glyph from ``└─`` to
    # ``├─`` and keeps the parent spine running. The user-approved sketch
    # requires the spur on the play, role, task, and host ancestors of the
    # inner footer — not just the line immediately above it. Marking only
    # the last line produces the wrong visual: only the host leaf gets
    # ``├─`` while the play/role/task ancestors stay as ``└─`` and the
    # spine is broken. The depth-of-cut semantic (which line carries the
    # inner footer) is preserved by reading ``last_visible.depth`` after
    # the comprehension replaces every line.
    inner_section = [replace(ln, has_tail_after=True) for ln in outer_tail[:inner_budget]]
    last_visible = inner_section[-1]
    inner_section.append(_more_footer(depth=last_visible.depth, count=inner_dropped))

    if head:
        head[-1] = replace(head[-1], has_tail_after=True)
    result = head + inner_section
    dropped = outer_tail[inner_budget:]
    result.append(_more_footer(depth=0, count=_count_domain_entities(dropped)))
    return result


@dataclass
class TreeProjection:
    """Pure projection of RunState. Build via `from_run_state`."""

    _state: RunState
    _role_index: dict[str, tuple[str, ...]] | None = field(default=None, init=False, repr=False)
    _known_roles: set[str] | None = field(default=None, init=False, repr=False)
    _runtime_role_counts: dict[str, int] | None = field(default=None, init=False, repr=False)
    _known_tree_revision: int | None = field(default=None, init=False, repr=False)
    # Preflight-derived caches. Everything here is a pure function of the
    # (immutable-after-set_definitions) definitions, so it is computed once
    # and reused across renders. All are invalidated wholesale in
    # ``_refresh_tree_cache`` when the tree revision advances (definitions
    # reassigned or a dynamic task grafted). Keyed by ``id(play_def)`` — play
    # definition objects are stable for the life of a revision.
    #
    # ``_pending_play_lines``: the full TreeLine list a fully-pending play
    # projects (``_emit_pending_play``). ``_runtime_play_preflight_roles``:
    # the ``(innermost-role → preflight task count, preflight name set)`` pair
    # ``_emit_runtime_play`` derives from a play's definition. Keyed by the
    # visible-play-name filter, ``_role_total_preflight``: the preflight
    # portion of ``_build_role_total_tasks``. ``_total_unique_tasks``: the
    # whole-run leaf-task count the outer footer uses.
    _pending_play_lines: dict[int, list["TreeLine"]] = field(
        default_factory=dict, init=False, repr=False
    )
    _runtime_play_preflight_roles: dict[
        int, tuple[dict[str | None, int], set[str], set[tuple[str, ...]]]
    ] = field(default_factory=dict, init=False, repr=False)
    _role_total_preflight: dict[frozenset[str] | None, tuple[dict[str, int], set[str]]] = field(
        default_factory=dict, init=False, repr=False
    )
    _total_unique_tasks: int | None = field(default=None, init=False, repr=False)
    # Per-render memo for ``_play_running_and_pending`` — reset at the top of
    # each ``_tree_lines_unbounded`` call. The active play's items are needed
    # by both the "find the latest running play" pre-pass and the emission
    # loop; without this memo the O(preflight × runtime-match) walk runs twice
    # per render. Keyed by ``id(play)``.
    _prp_render_memo: dict[int, list[tuple[str, str, tuple[str, ...], "TaskRunState | None"]]] = (
        field(default_factory=dict, init=False, repr=False)
    )
    _row_leases: dict[tuple[str, str], _RowLease] = field(
        default_factory=dict, init=False, repr=False
    )
    # Sticky fallback: the play_id of the most recent play with running
    # tasks. Persists between render calls so the tree stays stable during
    # transient gaps (e.g. between linear-strategy tasks).
    _last_running_play_id: str | None = field(default=None, init=False, repr=False)
    # Internal lease/sticky discriminator for serial/run_once windowed plays.
    _last_running_play_runtime_id: str | None = field(default=None, init=False, repr=False)
    # Mapping from runtime play_id to the PlayDefinition matched during
    # tree construction. Fixes Issue #11: when two plays share the same
    # display name (e.g. "Deploy" executed twice), the name-based index
    # in RunState._play_def_by_name only holds one entry. This mapping
    # is built in _tree_lines_unbounded from the ordered_plays matching
    # logic and used by _play_def_for to avoid the name-collision trap.
    _runtime_play_to_def: dict[str, PlayDefinition | None] = field(
        default_factory=dict, init=False, repr=False
    )

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
        self._pending_play_lines.clear()
        self._runtime_play_preflight_roles.clear()
        self._role_total_preflight.clear()
        self._total_unique_tasks = None

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
        # Track the most recent terminal failure per host so the
        # "on" column can name the failing task instead of "(idle)".
        failed: dict[str, tuple[str, Status]] = {}

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
                        if effective in (Status.FAILED, Status.UNREACHABLE):
                            failed[hostname] = (task.name, effective)

        rows: list[HostRow] = []
        for hostname in order:
            host_counts = counts[hostname]
            worst = self._worst_status_of(host_counts.keys())
            cur = current[hostname]
            fail = failed.get(hostname)
            rows.append(
                HostRow(
                    hostname=hostname,
                    counts=dict(host_counts),
                    worst_status=worst,
                    current_task=cur[0] if cur else None,
                    current_elapsed_s=cur[1] if cur else None,
                    failed_task=fail[0] if fail else None,
                    failed_status=fail[1] if fail else None,
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

    def _relabel_role_lines(self, lines: list[TreeLine]) -> list[TreeLine]:
        """Rewrite role TreeLine labels to carry a stable ``(N tasks)`` count.

        T3 post-truncation pass: every ``kind="role"`` line's label is
        replaced so the count always reflects the role's total task
        count (preflight + runtime) — never a "remaining" suffix.

        - ``role: X (N tasks)`` — when the role has any tasks at all.
          ``N`` is the total task count for this role across the
          currently-visible plays.
        - ``role: X`` — when the role has zero tasks (no count emitted).
        - ``role: X (1 task)`` — singular form when N=1 (matches the
          existing convention from ``_emit_pending_play`` and
          ``_emit_runtime_play``).

        Earlier revisions of this method emitted ``(M remaining)`` where
        ``M = total - visible``; that formulation counted completed
        tasks (which are dropped from the kept lines) and made the
        suffix count grow as the run progressed. The
        ``… and N more tasks`` inner/outer footers already carry the
        hidden-work signal in the truncated case, so role labels no
        longer need to mirror them.

        The TreeLine's other fields are untouched. The renderer doesn't
        pattern-match the suffix — it just renders the label string —
        so changing the shape here is safe for compact and TUI. The pass
        is idempotent in the within-budget case (visible == total) so
        the output matches today's emission when no truncation happens.

        The post-truncation pass structure is kept intact (and
        ``_build_role_total_tasks`` / ``_count_visible_tasks_per_role``
        remain) so the inner-footer recompute in
        ``_recompute_inner_footer_count`` can keep using them.

        See ``.sisyphus/plans/two-level-truncation.md`` T3.
        """
        play_names = self._visible_play_names(lines)
        role_total_tasks = self._build_role_total_tasks(play_names=play_names)
        # ``role_visible_tasks`` is no longer used to compute the suffix
        # (the suffix is gone), but it's still cheap to compute here and
        # keeps the post-truncation pass structure intact for any future
        # emission change. _recompute_inner_footer_count relies on these
        # helpers, so they are not deletable.
        _role_visible_tasks = self._count_visible_tasks_per_role(lines)

        result: list[TreeLine] = []
        for ln in lines:
            if ln.kind != "role" or ln.identity is None:
                result.append(ln)
                continue
            r = ln.identity
            total = role_total_tasks.get(r, 0)

            if total == 0:
                # Empty role: no count at all. Matches the pre-T3
                # emission (``if n > 0 else ""``).
                new_label = f"role: {r}"
            else:
                plural = "task" if total == 1 else "tasks"
                new_label = f"role: {r} ({total} {plural})"

            result.append(replace(ln, label=new_label))
        return result

    def _visible_play_names(self, lines: list[TreeLine]) -> set[str]:
        """Extract the names of all plays currently visible in ``lines``.

        Walks the projected tree and collects the set of play names
        that the user can see. Used by the relabel and inner-footer
        passes to scope ``_build_role_total_tasks`` to the visible
        subset of plays — a role that appears in N different play
        definitions should report its task count for the single play
        the user is looking at, not the sum across all N. The label
        prefix ``"play: "`` is stripped before adding to the set.
        """
        play_names: set[str] = set()
        for ln in lines:
            if ln.kind == "play" and ln.label.startswith("play: "):
                play_names.add(ln.label[len("play: ") :])
        return play_names

    @staticmethod
    def _play_def_matches_visible(play_def_name: str, visible_names: set[str]) -> bool:
        """Return True if a preflight definition name corresponds to a
        visible play name.

        Ansible's ``--list-tasks`` and the JSONL ``play_start`` event
        can carry slightly different forms of the same play name (the
        test fixture uses the truncated event name ``"Setup rootless
        Podman"`` for a preflight definition named ``"Setup rootless
        Podman for Scrutiny web server"``). A definition is considered
        to match a visible name when either string-equals, stripped-
        equals, or one is a prefix of the other — strict equality alone
        would silently drop the preflight contribution for any play
        where the two sources disagree, deflating role totals below
        the preflight ground truth.
        """
        if not visible_names:
            return True
        stripped = play_def_name.strip()
        for v in visible_names:
            vs = v.strip()
            if play_def_name == v or stripped == vs:
                return True
            if play_def_name.startswith(v) or stripped.startswith(vs):
                return True
            if v.startswith(play_def_name) or vs.startswith(stripped):
                return True
        return False

    def _role_total_preflight_for(
        self, play_names: set[str] | None
    ) -> tuple[dict[str, int], set[str]]:
        """Preflight portion of ``_build_role_total_tasks``: ``(role → subtree
        task count, preflight name set)`` for the plays matching ``play_names``.

        Pure function of the definitions and the visibility filter, memoised
        per filter and invalidated on revision. See ``_build_role_total_tasks``
        for the counting rules (subtree crediting; parent stubs skipped).
        """
        key = frozenset(play_names) if play_names is not None else None
        cached = self._role_total_preflight.get(key)
        if cached is not None:
            return cached
        role_total_tasks: dict[str, int] = {}
        emitted_preflight_names: set[str] = set()
        for play_def in self._state.definitions:
            if not self._play_def_matches_visible(play_def.name, play_names or set()):
                continue
            for entry, role_path in iter_preflight_task_defs(play_def.tasks):
                emitted_preflight_names.add(entry.name)
                if entry.children:
                    continue
                collapsed_path = _collapse_role_path_aggressive(role_path)
                if not collapsed_path:
                    continue
                for role in collapsed_path:
                    role_total_tasks[role] = role_total_tasks.get(role, 0) + 1
        result = (role_total_tasks, emitted_preflight_names)
        self._role_total_preflight[key] = result
        return result

    def _build_role_total_tasks(self, play_names: set[str] | None = None) -> dict[str, int]:
        """Build role → total task count from preflight + runtime state.

        Mirrors the per-play counting logic in ``_emit_pending_play``
        and ``_emit_runtime_play``, but aggregated across all plays into
        a single map. Counts are SUBTREE-keyed: every task credits each
        ancestor in its role path (post-aggressive-collapse), not just
        the innermost role. This makes ``role_total_tasks["podman"]``
        include tasks under ``angie_ssl_terminator`` nested inside
        podman — the user's expectation per
        ``.sisyphus/plans/recursive-nesting.md`` open-question line
        143-148. Single-role fixtures keep their existing totals
        because the subtree of a leaf role equals its direct children.

        When ``play_names`` is provided, only tasks belonging to those
        plays are counted. This is used by the relabel and inner-footer
        passes, which operate on a tree that may have been truncated
        to a subset of plays. Without this filter, a role that appears
        in N different play definitions would have its task count
        inflated by the sum of tasks across all of them, producing
        role-label and inner-footer counts that span multiple plays
        instead of the one the user is currently looking at. When
        ``play_names`` is ``None``, every play in
        ``self._state.definitions`` is counted (the default; used by
        callers that need the global map).

        A definition is considered to match a visible play name when
        either string-equals it, stripped-string-equals it, or one is
        a prefix of the other (ansible's preflight ``--list-tasks``
        and the JSONL ``play_start`` event can use slightly different
        forms of the same play name — e.g. truncated vs. full). This
        keeps the preflight+runtime totals aligned with the visible
        tree's per-play scope even when the play name strings differ
        between sources.

        Three passes:

        1. Preflight definitions. For each ``PlayDefinition`` in
           ``self._state.definitions``, iterate ``iter_preflight_task_defs``
           and credit each task to every role in its role path (so a
           task under ``("podman", "angie_ssl_terminator")`` credits
           both ``podman`` and ``angie_ssl_terminator``). Tasks with
           empty role paths are skipped (they live directly under a
           play, no role header). Parent stub entries (those with
           non-empty ``TaskDefinition.children``) are skipped — they
           are ``include_tasks`` containers, not leaves; the credit
           must land on their children instead to avoid double
           counting.

        2. Runtime tasks not in preflight. ``include_role`` and dynamic
           ``include_tasks`` appear at runtime but not in ``--list-tasks``
           output, so they aren't in the preflight count. For each
           runtime ``TaskRunState`` whose name (or stripped name) isn't
           in the preflight name set and doesn't template-match a
           preflight name, credit ``runtime_role_from_task_name`` and
           any chain prefix extracted from ``" : "`` in the task name.

        3. Fallback for runtime-only roles. The emission's
           ``_emit_runtime_play`` falls back to counting runtime tasks
           by ``runtime_role_from_task_name`` for any role that has 0 in
           the preflight+runtime-only map. This catches dynamic-only
           roles whose grafted ``TaskDefinition`` carries
           ``role=None`` in the preflight tree but the runtime task name
           still has the role prefix (e.g. dynamic include_role whose
           child is grafted under a role-less parent). Replicate that
           fallback here so the relabel produces the same counts the
           emission would.
        """
        # Preflight passes: credit each task to every role in its
        # (aggressively collapsed) role path, and build the preflight name set
        # for the runtime filter. Both are pure functions of the definitions
        # and the ``play_names`` visibility filter, so they are memoised (per
        # filter, invalidated on revision) rather than re-walked on every
        # render. ``role_total_tasks`` is copied because the runtime/fallback
        # passes below mutate it; ``emitted_preflight_names`` is only read.
        preflight_totals, emitted_preflight_names = self._role_total_preflight_for(play_names)
        role_total_tasks: dict[str, int] = dict(preflight_totals)

        # Runtime pass: tasks not in preflight. Credit the chain
        # extracted from " : " in the runtime name so the runtime
        # subtree (including outer roles) is reflected too.
        for play in self._state.plays.values():
            if play_names is not None and play.name not in play_names:
                continue
            for task in play.tasks.values():
                stripped = strip_role_prefix(task.name)
                if task.name in emitted_preflight_names or stripped in emitted_preflight_names:
                    continue
                is_template_matched = False
                for pn in emitted_preflight_names:
                    if "{{" in pn and (
                        _is_template_match(pn, task.name) or _is_template_match(pn, stripped)
                    ):
                        is_template_matched = True
                        break
                if is_template_matched:
                    continue
                chain = _name_role_chain(task.name)
                if chain:
                    for role in _collapse_role_path_aggressive(chain):
                        role_total_tasks[role] = role_total_tasks.get(role, 0) + 1

        # Fallback: count runtime tasks per role name for any role that
        # still has 0. Mirrors ``_emit_runtime_play``'s ``if n == 0:``
        # guard at line ~1159. This catches roles that appear at runtime
        # via dynamic include_role whose grafted TaskDefinition has
        # ``role=None`` (so preflight didn't tally them) AND whose task
        # name was grafted into the preflight name set (so the
        # runtime-only pass skipped them). Filtered by ``play_names``
        # to match the preflight/runtime passes above.
        all_runtime_roles: set[str] = set()
        for play in self._state.plays.values():
            if play_names is not None and play.name not in play_names:
                continue
            for task in play.tasks.values():
                r = runtime_role_from_task_name(task.name)
                if r is not None:
                    all_runtime_roles.add(r)
        for role in all_runtime_roles:
            if role_total_tasks.get(role, 0) == 0:
                count = sum(
                    1
                    for play in self._state.plays.values()
                    if play_names is None or play.name in play_names
                    for task in play.tasks.values()
                    if runtime_role_from_task_name(task.name) == role
                )
                if count > 0:
                    role_total_tasks[role] = count

        return role_total_tasks

    def _count_visible_tasks_per_role(self, lines: list[TreeLine]) -> dict[str, int]:
        """Walk the lines list and count ``kind="task"`` lines per role.

        Each task line is counted under EVERY ancestor role in its
        visible role stack (subtree semantics). A ``kind="role"`` line
        pushes ``ln.identity`` onto the stack; a ``kind in ("play",
        "playbook")`` line clears the stack. A ``kind="task"`` line
        credits every role currently in the stack so a task under
        ``role: podman > role: angie_ssl_terminator`` counts under
        both. Tasks with empty role stacks (no role ancestor) are not
        credited to any role — they live directly under a play.

        Host leaves, "more" footers, and structural lines themselves
        don't contribute to task counts.

        Used by ``_relabel_role_lines`` to compute the
        ``role_visible_tasks`` map. The walk is O(n) over the kept
        lines (typically ≪ budget), so it's cheap.
        """
        role_visible_tasks: dict[str, int] = {}
        current_role_stack: list[str] = []
        current_depth_stack: list[int] = []
        for ln in lines:
            if ln.kind == "role" and ln.identity is not None:
                # Pop siblings (same depth) and out-of-scope ancestors
                # (lesser depth) so the stack reflects the correct
                # ancestor chain. Without this, sibling roles at the
                # same depth accumulate and tasks under the second role
                # are incorrectly credited to the first.
                while current_depth_stack and current_depth_stack[-1] >= ln.depth:
                    current_depth_stack.pop()
                    current_role_stack.pop()
                current_role_stack.append(ln.identity)
                current_depth_stack.append(ln.depth)
            elif ln.kind in ("play", "playbook"):
                current_role_stack.clear()
                current_depth_stack.clear()
            elif ln.kind == "task":
                for role in current_role_stack:
                    role_visible_tasks[role] = role_visible_tasks.get(role, 0) + 1
        return role_visible_tasks

    def _count_completed_tasks_per_role(
        self, play_names: set[str] | None = None
    ) -> tuple[dict[str, int], int]:
        """Count completed tasks per role (subtree semantics) and total completed tasks.

        A task is completed if ``task.status == Status.COMPLETED`` or (``task.hosts``
        is non-empty and every host has non-RUNNING status).
        """
        role_completed: dict[str, int] = {}
        total_completed = 0
        for play in self._state.plays.values():
            if play_names is not None and not self._play_def_matches_visible(play.name, play_names):
                continue
            for task in play.tasks.values():
                is_completed = task.status == Status.COMPLETED or (
                    bool(task.hosts)
                    and all(hs.status != Status.RUNNING for hs in task.hosts.values())
                )
                if not is_completed:
                    continue
                total_completed += 1
                role_path = self._task_role(task.name)
                if not role_path:
                    chain = _name_role_chain(task.name)
                    if chain:
                        role_path = _collapse_role_path_aggressive(chain)
                    else:
                        r = runtime_role_from_task_name(task.name)
                        if r is not None:
                            role_path = (r,)
                for role in role_path:
                    role_completed[role] = role_completed.get(role, 0) + 1
        return role_completed, total_completed

    def _recompute_inner_footer_count(self, lines: list[TreeLine]) -> list[TreeLine]:
        """Replace the inner footer(s) with per-role subtree remaining counts.

        ``_truncate_two_level`` emits one inner footer with a count of
        *all* task-domain entities (tasks + roles + plays) in the
        dropped tail — which includes upcoming plays' tasks. The user
        expects the inner footer to report only the tasks remaining in
        each open role's branch, derived from
        ``role_total - role_completed - role_visible``.

        For nested roles (e.g. ``role: podman > role:
        angie_ssl_terminator`` with the cut inside angie), this method
        emits ONE inner footer per open role ancestor — angie reports
        its own subtree remaining, podman reports its subtree remaining
        (which includes angie's tasks transitively). Footers are
        emitted deepest-first so the innermost role's footer is
        closest to its task list, matching the visual mental model.

        The "depth" of each inner footer equals the role's task-list
        depth (= role's line depth + 1) so it hangs in line with where
        this role's tasks would sit. The renderer suppresses branch
        glyphs on ``kind="more"`` lines, so multiple footers at
        different depths render as siblings of the deepest visible
        task without breaking the parent spine.

        Single-role cases preserve the existing single-footer
        behavior: exactly one footer at the deepest visible line
        depth, count = role_total - role_completed - role_visible.

        For roles in the **head** (lines before the inner section or
        before the outer cut when no inner section exists), this
        method also inserts per-role inner footers at the role's
        task-list depth when uncompleted tasks remain hidden under that role.
        Footers are inserted immediately after the role's last visible task
        in the line list, deepest-first (innermost role's footer
        first), matching the multi-level cut-inside-role logic.

        The **outer footer** count is always recomputed to equal
        ``total_unique_tasks_across_all_plays - total_completed_tasks - visible_task_count``.
        This keeps the outer footer's number and the inner footers' numbers
        consistent — they all derive from ``total - completed - visible``.

        No-op when no inner footer exists in the inner section AND
        no role in the head has remaining > 0 (degenerate — fall
        back to whatever count the truncation produced).
        """
        play_names = self._visible_play_names(lines)
        role_total_tasks = self._build_role_total_tasks(play_names=play_names)
        role_visible_tasks = self._count_visible_tasks_per_role(lines)
        role_completed_tasks, _ = self._count_completed_tasks_per_role(play_names=play_names)
        visible_task_count = sum(1 for ln in lines if ln.kind == "task")

        inner_idx: int | None = None
        for i, ln in enumerate(lines):
            if ln.kind == "more" and ln.depth > 0:
                inner_idx = i
                break

        role_chain: list[str] = []
        if inner_idx is not None:
            for j in range(inner_idx - 1, -1, -1):
                cand = lines[j]
                if cand.kind in ("play", "playbook"):
                    break
                if cand.kind == "role" and cand.identity is not None:
                    role_chain.append(cand.identity)
            role_chain.reverse()

        inner_section_roles: set[str] = set(role_chain)

        # Single walk: track each role's last visible task index so
        # head-footer insertion knows where to place each role's
        # footer (immediately after the last visible task under it,
        # including any inner-role tasks in the same subtree).
        role_stack: list[tuple[int, str]] = []
        last_task_in_stack_role: dict[str, int] = {}
        for j, ln in enumerate(lines):
            if ln.kind == "role" and ln.identity is not None:
                # Pop siblings at the same depth so tasks under the new
                # sibling role don't get credited to the previous sibling
                # in ``last_task_in_stack_role`` (Bug A: sibling roles
                # at the same depth must close out the previous sibling's
                # contribution to footer placement).
                while role_stack and role_stack[-1][0] >= ln.depth:
                    role_stack.pop()
                role_stack.append((ln.depth, ln.identity))
            elif ln.kind in ("play", "playbook"):
                role_stack.clear()
            elif ln.kind == "task":
                for _depth, role_name in role_stack:
                    last_task_in_stack_role[role_name] = j

        depth_by_role: dict[str, int] = {
            ln.identity: ln.depth for ln in lines if ln.kind == "role" and ln.identity is not None
        }

        # Process head roles innermost-first so an outer role's
        # footer is placed after the inner role's footer (matching
        # the deepest-first ordering used by the inner-section logic).
        head_role_names = sorted(
            (r for r in role_total_tasks if r not in inner_section_roles),
            key=lambda r: -depth_by_role.get(r, 0),
        )

        # Map from role name to its assigned footer insertion index.
        # The insertion point is the max of: the role line's own
        # index, the role's last visible task index, and any inner
        # role's already-assigned footer position (so the outer role's
        # footer lands BELOW the inner role's footer at the same site).
        head_footer_insert_idx: dict[str, int] = {}
        for role_name in head_role_names:
            total = role_total_tasks[role_name]
            completed = role_completed_tasks.get(role_name, 0)
            remaining = total - completed - role_visible_tasks.get(role_name, 0)
            if remaining <= 0:
                continue
            role_line_idx: int | None = next(
                (j for j, ln in enumerate(lines) if ln.kind == "role" and ln.identity == role_name),
                None,
            )
            if role_line_idx is None:
                continue
            last_task_idx = last_task_in_stack_role.get(role_name)
            insert_after = max(
                role_line_idx,
                last_task_idx if last_task_idx is not None else role_line_idx,
            )
            inner_footer_positions = [
                pos
                for other, pos in head_footer_insert_idx.items()
                if depth_by_role.get(other, 0) > depth_by_role.get(role_name, 0)
                and any(
                    lines[j2].kind == "role" and lines[j2].identity == other
                    for j2 in range(role_line_idx + 1, insert_after + 1)
                )
            ]
            if inner_footer_positions:
                insert_after = max(insert_after, max(inner_footer_positions))
            head_footer_insert_idx[role_name] = insert_after

        head_footers = [
            (
                insert_after,
                _more_footer(
                    depth=depth_by_role[r] + 1,
                    count=role_total_tasks[r]
                    - role_completed_tasks.get(r, 0)
                    - role_visible_tasks.get(r, 0),
                ),
            )
            for r, insert_after in head_footer_insert_idx.items()
        ]
        # Sort by insert position ascending, depth descending within
        # the same position. The depth-descending tiebreaker keeps
        # the innermost role's footer first so the outer role's
        # footer lands right below it.
        head_footers.sort(key=lambda pair: (pair[0], -pair[1].depth))

        result: list[TreeLine] = list(lines)
        offset_at_position: dict[int, int] = {}
        for insert_after, footer in head_footers:
            offset = offset_at_position.get(insert_after, 0)
            result.insert(insert_after + 1 + offset, footer)
            offset_at_position[insert_after] = offset + 1

        if inner_idx is not None:
            replacements: list[TreeLine] = []
            for role in reversed(role_chain):
                total = role_total_tasks.get(role, 0)
                completed = role_completed_tasks.get(role, 0)
                visible = role_visible_tasks.get(role, 0)
                remaining = total - completed - visible
                if remaining <= 0:
                    continue
                role_depth: int | None = None
                for j in range(inner_idx - 1, -1, -1):
                    if lines[j].kind == "role" and lines[j].identity == role:
                        role_depth = lines[j].depth
                        break
                assert role_depth is not None
                replacements.append(_more_footer(depth=role_depth + 1, count=remaining))
            # The inner footer was at ``inner_idx`` in the
            # original ``lines``. Head footers inserted before
            # that position shift it right, so compute the
            # adjusted index rather than searching for the
            # first ``more`` line with ``depth > 0`` (which
            # would incorrectly match a head footer instead of
            # the inner footer).
            shift = 0
            local_offsets: dict[int, int] = {}
            for insert_after, _ in head_footers:
                off = local_offsets.get(insert_after, 0)
                insert_pos = insert_after + 1 + off
                if insert_pos <= inner_idx + shift:
                    shift += 1
                local_offsets[insert_after] = off + 1
            cur_inner_idx = inner_idx + shift
            result = result[:cur_inner_idx] + replacements + result[cur_inner_idx + 1 :]

        outer_idx: int | None = None
        for j, ln in enumerate(result):
            if ln.kind == "more" and ln.depth == 0:
                outer_idx = j
                break
        if outer_idx is not None:
            # ``iter_preflight_task_defs`` yields parent stubs as well as
            # their children. Parent stubs are ``include_tasks`` containers,
            # not leaves — counting them would double-count the leaves in
            # their subtree. Skip them so the outer footer's drop count
            # matches the visible/inner math (same rule as
            # ``_count_tasks`` in ``format.py``).
            # Whole-run leaf-task count is a pure function of the definitions;
            # memoise it (invalidated on revision) instead of re-walking every
            # play's preflight tree on each render.
            if self._total_unique_tasks is None:
                self._total_unique_tasks = sum(
                    sum(
                        1
                        for tdef, _ in iter_preflight_task_defs(play_def.tasks)
                        if not tdef.children
                    )
                    for play_def in self._state.definitions
                )
            _, global_completed_tasks = self._count_completed_tasks_per_role(play_names=None)
            total_bound = max(self._total_unique_tasks, global_completed_tasks + visible_task_count)
            outer_remaining = max(0, total_bound - global_completed_tasks - visible_task_count)
            result[outer_idx] = _more_footer(depth=0, count=outer_remaining)

        return result

    def tree_lines(self, budget: int, now: datetime | None = None) -> list[TreeLine]:
        """Project + prune to fit `budget` lines.

        Truncation is two-cut (see ``_truncate_two_level`` and the
        T2 plan at ``.sisyphus/plans/two-level-truncation.md``):
        when the budget is exceeded, the algorithm finds the first
        play-line at or after the budget boundary and treats that
        as the "outer cut". Everything before is the "head" and
        kept verbatim. Within the remaining budget, a second
        "inner cut" can land inside a role's task list; in that
        case an inner footer at the role's task depth reports the
        dropped tail. The outer footer at depth 0 reports the
        total drop count across the whole tree.

        The unbounded tree is ordered active-play-first, so
        truncating from the end preserves the deepest, most
        informative portion of the tree (the running play's role
        → task → host subtree) while upcoming plays get cut
        first. This is the key difference from "structural lines
        first" approaches, which consume the entire budget on
        play headers and leave no room for tasks or hosts.

        After truncation (or in the within-budget path),
        ``_relabel_role_lines`` rewrites every role line's label to
        carry the stable ``(N tasks)`` count — the role's total task
        count from preflight + runtime definitions. The "hidden work"
        signal lives in the ``… and N more tasks`` inner/outer footers
        emitted by ``_recompute_inner_footer_count``. See T3 of the
        plan.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        self._refresh_tree_cache()
        self._prune_row_leases(now)

        lines = self._tree_lines_unbounded(now)
        if len(lines) <= budget:
            # Idempotent relabel: when nothing was truncated, the role
            # labels already read "(N tasks)" from emission, and the
            # relabel pass reproduces that exactly. Running it here
            # keeps a single code path for both branches so any future
            # emission change in the role label format can't desync.
            relabelled = self._relabel_role_lines(lines)
            self._prune_row_leases(now)
            return relabelled

        truncated = _truncate_two_level(lines, budget)
        recomputed = self._recompute_inner_footer_count(truncated)
        relabelled = self._relabel_role_lines(recomputed)
        self._prune_row_leases(now)
        return relabelled

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

        # Fresh per-render memo so the active play's running/pending items are
        # computed once, not once for the "latest running play" pre-pass and
        # again for emission.
        self._prp_render_memo = {}

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

        # Build the runtime-play → definition mapping so _play_def_for
        # can resolve duplicate-named plays correctly (Issue #11).
        self._runtime_play_to_def = {}
        for runtime, play_def in ordered_plays:
            if runtime is not None and runtime.play_id:
                self._runtime_play_to_def[runtime.play_id] = play_def

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

        active_play_index: int | None = None
        if active_play_id is not None:
            for idx, (rt, _) in enumerate(ordered_plays):
                if rt is not None and self._play_runtime_identity(rt) == active_play_id:
                    active_play_index = idx
                    break

        for idx, (runtime, play_def) in enumerate(ordered_plays):
            if runtime is not None:
                if active_play_id is not None:
                    if self._play_runtime_identity(runtime) != active_play_id:
                        # Force-finalized plays (e.g. linear strategy
                        # advancing to the next play) get hidden even
                        # when no task events arrived — otherwise their
                        # preflight tasks would render as pending long
                        # after the playbook moved past them.
                        if runtime.status == Status.COMPLETED:
                            continue
                        items = self._play_running_and_pending(runtime, include_cross_play=False)
                        # If an active play has already started after this play,
                        # and this prior play has no running tasks, it is completed.
                        if active_play_index is not None and idx < active_play_index:
                            if not any(k == "running" for k, _, _, _ in items):
                                continue
                        # Hide plays whose every task is finished: no
                        # running, no pending, only ``runtime.tasks``
                        # left as completed history. A play with some
                        # completed AND some still-pending tasks must
                        # NOT be skipped — upcoming work is the user's
                        # signal of progress.
                        if not items and runtime.tasks:
                            continue
                self._emit_runtime_play(lines, runtime, now)
            elif play_def is not None:
                # Preflight-only plays that appear before the active play in the
                # playbook definition order were skipped (e.g. via --tags or
                # when: conditions) and will not run. Do not emit them as pending.
                if active_play_index is not None and idx < active_play_index:
                    continue
                self._emit_pending_play(lines, play_def, now)
        return lines

    def _emit_pending_play(
        self, lines: list[TreeLine], play_def: "PlayDefinition", now: datetime
    ) -> None:
        """Render an upcoming-only play: header + every preflight task as pending.

        Walks the preflight tree iteratively. Each task carries a
        ``role_path`` (outermost to innermost) from
        ``iter_preflight_task_defs``. As the path changes between tasks, we
        close the previous roles by emitting headers for only the roles
        in the new path's suffix beyond the common prefix with the prior
        path — i.e. open inner roles, leave outer ones untouched. The
        role header at role-index ``i`` lives at depth ``2 + i``; a task
        at the bottom of a ``len(n)`` role path sits at depth ``2 + n``
        (or depth 2 when the path is empty).

        A fully-pending play's projection is a pure function of its
        (immutable-per-revision) ``PlayDefinition``: every line is PENDING
        with ``elapsed_s=None``, so nothing here depends on ``now`` or runtime
        state. The emitted line list is therefore memoised per ``id(play_def)``
        (invalidated on revision change) and reused across renders — the walk
        over a large upcoming play used to run on every frame. The row-lease
        side effects are intentionally dropped on the cached path: pending
        play / task / role leases are never read to make an output decision
        (only ``("play", <runtime-identity>)`` leases are, and those are
        refreshed each render by ``_emit_runtime_play``), so skipping them
        cannot change what is rendered.
        """
        cached = self._pending_play_lines.get(id(play_def))
        if cached is not None:
            lines.extend(cached)
            return

        emitted: list[TreeLine] = [
            TreeLine(
                depth=1,
                kind="play",
                label=f"play: {play_def.name}",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            )
        ]
        # Pre-pass: count tasks per *innermost* role so the role header
        # summary reflects the total under that role regardless of
        # nesting depth. ``_collapse_role_path_aggressive`` collapses
        # the ``(X, X)`` path produced when ``TaskDefinition.role``
        # matches the enclosing ``RoleGroupDefinition.role`` (the
        # preflight side of the duplicate-role-header bug), and also
        # drops any non-consecutive duplicates the per-step collapse
        # cannot catch.
        role_counts: dict[str | None, int] = {}
        for _entry, role_path in iter_preflight_task_defs(play_def.tasks):
            collapsed_path = _collapse_role_path_aggressive(role_path)
            innermost = collapsed_path[-1] if collapsed_path else None
            role_counts[innermost] = role_counts.get(innermost, 0) + 1

        current_role_path: list[str] = []
        for tdef, role_path in iter_preflight_task_defs(play_def.tasks):
            # ``_collapse_role_path_aggressive`` collapses the
            # ``(X, X)`` path produced when ``TaskDefinition.role``
            # matches the enclosing ``RoleGroupDefinition.role``, so
            # the renderer sees one role path element per unique
            # nesting level instead of two for the duplicate case.
            role_path_list = list(_collapse_role_path_aggressive(role_path))
            if role_path_list != current_role_path:
                common = 0
                for a, b in zip(current_role_path, role_path_list):
                    if a == b:
                        common += 1
                    else:
                        break
                for depth_idx in range(common, len(role_path_list)):
                    role = role_path_list[depth_idx]
                    n = role_counts.get(role, 0)
                    task_count = f" ({n} task{'s' if n != 1 else ''})" if n > 0 else ""
                    role_depth = 2 + depth_idx
                    emitted.append(
                        TreeLine(
                            depth=role_depth,
                            kind="role",
                            label=f"role: {role}{task_count}",
                            glyph=None,
                            status=None,
                            elapsed_s=None,
                            identity=role,
                        )
                    )
                current_role_path = role_path_list
            task_depth = 2 + len(current_role_path) if current_role_path else 2
            emitted.append(
                TreeLine(
                    depth=task_depth,
                    kind="task",
                    label=strip_role_prefix(tdef.name),
                    glyph=None,
                    status=Status.PENDING,
                    elapsed_s=None,
                )
            )

        self._pending_play_lines[id(play_def)] = emitted
        lines.extend(emitted)

    def _runtime_play_preflight_roles_for(
        self, play_def: "PlayDefinition | None"
    ) -> tuple[dict[str | None, int], set[str], set[tuple[str, ...]]]:
        """``(innermost-role → preflight task count, preflight name set, preflight
        known role paths)`` for a play, memoised per ``id(play_def)`` and invalidated on revision.

        All are pure functions of the play definition. The caller copies the
        count dict before mutating it with runtime roles; the name set and path set
        are only read, so they are returned by reference.
        """
        if play_def is None:
            return {}, set(), set()
        cached = self._runtime_play_preflight_roles.get(id(play_def))
        if cached is not None:
            return cached
        role_total_tasks: dict[str | None, int] = {}
        emitted_preflight_names: set[str] = set()
        preflight_known_role_paths: set[tuple[str, ...]] = set()
        for entry, role_path in iter_preflight_task_defs(play_def.tasks):
            collapsed_path = _collapse_role_path_aggressive(role_path)
            innermost = collapsed_path[-1] if collapsed_path else None
            role_total_tasks[innermost] = role_total_tasks.get(innermost, 0) + 1
            emitted_preflight_names.add(entry.name)
            if role_path:
                preflight_known_role_paths.add(collapsed_path)
        result = (role_total_tasks, emitted_preflight_names, preflight_known_role_paths)
        self._runtime_play_preflight_roles[id(play_def)] = result
        return result

    def _emit_runtime_play(self, lines: list[TreeLine], play: PlayRunState, now: datetime) -> None:
        """Render a play that's already in flight (or was)."""
        play_items = self._play_running_and_pending(play)
        if not play_items:
            return

        running_items = [(k, n, rp, rt) for k, n, rp, rt in play_items if k == "running"]
        pending_items = [(k, n, rp, rt) for k, n, rp, rt in play_items if k != "running"]

        if not running_items and not pending_items:
            return

        # Render running tasks and pending tasks clustered by their hierarchical
        # role path so that multi-host concurrency does not interleave tasks
        # and repeatedly open/close role headers.
        play_items = _cluster_items_by_role_path(running_items + pending_items)

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

        # Count total tasks per *innermost* role from definitions (not
        # from play_items, which drops completed tasks and would
        # undercount). The count key is the innermost role name so the
        # parenthesised "(N tasks)" summary stays stable for nested
        # roles. ``_collapse_role_path_aggressive`` collapses the
        # ``(X, X)`` path produced when ``TaskDefinition.role`` matches
        # the enclosing ``RoleGroupDefinition.role`` so the count and
        # the path the main loop iterates stay consistent.
        play_def = self._play_def_for(play)
        self._touch_play_leases(play, play_def, now)
        # The innermost-role task counts and the preflight name set are pure
        # functions of ``play_def`` (invalidated on revision), so they are
        # memoised per ``id(play_def)`` rather than re-walked every render.
        # ``role_total_tasks`` is copied because the runtime pass below mutates
        # it; ``emitted_preflight_names`` is only read, so it is shared.
        preflight_role_totals, emitted_preflight_names, _ = self._runtime_play_preflight_roles_for(
            play_def
        )
        role_total_tasks: dict[str | None, int] = dict(preflight_role_totals)
        # Also count runtime tasks per role that weren't in preflight.
        # include_role tasks appear at runtime but --list-tasks doesn't
        # expand them, so they're missing from play_def.

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
            task_role = runtime_role_from_task_name(task.name)
            if task_role is not None:
                role_total_tasks[task_role] = role_total_tasks.get(task_role, 0) + 1

        current_role_path: list[str] = []
        for item_kind, name, role_path, runtime in play_items:
            role_path_list = list(role_path)
            # No prefix-guard here: ``_play_running_and_pending`` yields
            # exactly one combined item per preflight task (it merges the
            # running task with its preflight definition rather than
            # emitting two items for the same task), so a pending task
            # at a shallower role depth than the current open chain is
            # a genuinely different task — drop it would silently hide
            # legitimate work. The role-chain emitter below correctly
            # handles the depth transition (common prefix = shallow
            # depth, no new role headers emitted, then emit the
            # pending task at its real depth).
            if role_path_list != current_role_path:
                common = 0
                for a, b in zip(current_role_path, role_path_list):
                    if a == b:
                        common += 1
                    else:
                        break
                for depth_idx in range(common, len(role_path_list)):
                    role = role_path_list[depth_idx]
                    n = role_total_tasks.get(role, 0)
                    if n == 0:
                        n = sum(
                            1
                            for task in play.tasks.values()
                            if runtime_role_from_task_name(task.name) == role
                        )
                    task_count = f" ({n} task{'s' if n != 1 else ''})" if n > 0 else ""
                    role_depth = 2 + depth_idx
                    lines.append(
                        TreeLine(
                            depth=role_depth,
                            kind="role",
                            label=f"role: {role}{task_count}",
                            glyph=None,
                            status=None,
                            elapsed_s=None,
                            identity=role,
                        )
                    )
                    self._touch_role_lease(role, now)
                current_role_path = role_path_list
            task_depth = 2 + len(current_role_path) if current_role_path else 2

            if item_kind == "running" and runtime is not None:
                lines.append(
                    self._task_line(
                        runtime,
                        depth=task_depth,
                        pending=_pending_host_count(play, play_def, runtime),
                    )
                )
                self._touch_task_lease(play, runtime, None, now)
                if _is_meta_task(runtime.name):
                    # Meta tasks are projection-only control flow. Keep the
                    # task row visible, but never project host leaves.
                    pass
                elif runtime.hosts:
                    loop_totals = self._state.loop_totals.get(runtime.path or "", {})
                    for hostname, hs in runtime.hosts.items():
                        if not _leaf_visible(hs):
                            continue
                        lines.append(
                            TreeLine(
                                depth=task_depth + 1,
                                kind="host",
                                label=_host_leaf_label(hostname, hs, loop_totals.get(hostname)),
                                glyph=None,
                                status=hs.status,
                                elapsed_s=_leaf_elapsed_s(hs, now),
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
                pending_label = (
                    strip_role_prefix(runtime.name)
                    if runtime is not None
                    else strip_role_prefix(name)
                )
                lines.append(
                    TreeLine(
                        depth=task_depth,
                        kind="task",
                        label=pending_label,
                        glyph=None,
                        status=Status.PENDING,
                        elapsed_s=None,
                    )
                )
                # Use task identity (not display name) for the lease key so
                # same-name concurrent tasks don't share a lease (Issue #12).
                if runtime is not None:
                    self._touch_row_lease("task", self._task_runtime_identity(play, runtime), now)
                else:
                    self._touch_row_lease("task", name, now)

    def _play_running_and_pending(
        self, play: "PlayRunState", include_cross_play: bool = True
    ) -> list[tuple[str, str, tuple[str, ...], TaskRunState | None]]:
        """Enumerate (kind, name, role_path, runtime) for a play's running and
        pending tasks, in execution order.

        ``kind`` is ``"running"`` (task has at least one RUNNING host) or
        ``"pending"`` (task hasn't started, or runtime has no hosts yet).
        Completed tasks — runtime has hosts and no host is RUNNING — are
        dropped from the result.

        ``role_path`` is the full role path from outermost to innermost
        (e.g. ``("podman", "angie_ssl_terminator")``). An empty tuple
        means the task sits directly under a play with no role context.

        The preflight side supplies the *outer* portion of the path via
        the matched ``TaskDefinition``'s ``role_path`` (built by
        ``iter_preflight_task_defs``). The runtime side may extend it:
        ``TaskRunState.parent_role`` (set by the role-cache look-up at
        task-start time) adds the next-outer role when grafted or
        included via a nested role, and
        ``runtime_role_from_task_name`` adds the *innermost* role when
        the runtime ``"role : "`` prefix differs from the preflight
        mapping. The preflight path is always preserved (the runtime
        extension is appended, not used to override it).

        Order: preflight order first (when ``definitions`` is available),
        with any runtime-only tasks (dynamic ``include_tasks``) appended
        in runtime-arrival order.

        ``include_cross_play`` is accepted for call-site compatibility but has
        no effect (cross-play borrowing is intentionally disabled), so the
        per-render memo below can serve both the ``False`` pre-pass call and
        the ``True`` emission call from one computation.
        """
        memo = self._prp_render_memo.get(id(play))
        if memo is not None:
            return memo

        runtime_by_name: dict[str, list[TaskRunState]] = defaultdict(list)
        runtime_by_path: dict[str, list[TaskRunState]] = defaultdict(list)
        for task in play.tasks.values():
            runtime_by_name[task.name].append(task)
            if task.path is not None:
                runtime_by_path[task.path].append(task)
            curr = task.name
            while " : " in curr:
                curr = curr.split(" : ", 1)[1].strip()
                runtime_by_name[curr].append(task)

        # Generic cross-play borrowing is intentionally disabled here.
        # Rows are built only from the current play's runtime tasks; any
        # explicit ownership model needs to be represented upstream.

        play_def = self._play_def_for(play)
        preflight_known_role_paths: set[tuple[str, ...]] = set()
        if play_def is not None:
            _, _, preflight_known_role_paths = self._runtime_play_preflight_roles_for(play_def)

        items: list[tuple[str, str, tuple[str, ...], TaskRunState | None]] = []
        emitted_names: set[str] = set()
        emitted_task_ids: set[str] = set()

        def _extend_role_path(
            preflight_path: tuple[str, ...],
            preflight_name_chain: tuple[str, ...],
            runtime: TaskRunState | None,
            runtime_name_chain: tuple[str, ...],
        ) -> tuple[str, ...]:
            """Combine the preflight role path with the runtime's role info.

            Construction order, outermost to innermost:

            1. The preflight's own role path (from the role group chain
               + ``TaskDefinition.role``).
            2. The preflight's name chain (extracted from the task
               name's ``" : "`` structure). This captures inner roles
               that the preflight's role field didn't surface — e.g. a
               task under ``role: podman`` whose name starts with
               ``"angie_ssl_terminator : "``.
            3. ``runtime.parent_role`` (set by the role-cache look-up),
               prepended when the runtime provides an outer role the
               preflight didn't have.
            4. The runtime's name chain, appended only when it adds
               new role levels beyond what's already in the path —
               i.e. its elements aren't a suffix of the path built so
               far. This handles two cases: when the preflight already
               encoded the same chain (the runtime is a confirmation
               and adds nothing), and when the runtime reveals deeper
               nesting the preflight couldn't know about (e.g. a task
               whose name has more ``" : "`` segments than the
               preflight's own task name).
            """
            extended: tuple[str, ...] = _collapse_role_path(preflight_path + preflight_name_chain)
            if runtime is not None and runtime.parent_role is not None:
                if not extended or extended[0] != runtime.parent_role:
                    extended = _collapse_role_path((runtime.parent_role,) + extended)
            if runtime_name_chain and (
                len(runtime_name_chain) > len(extended)
                or extended[-len(runtime_name_chain) :] != runtime_name_chain
            ):
                extended = _collapse_role_path(extended + runtime_name_chain)
            res = _collapse_role_path_aggressive(extended)
            if preflight_known_role_paths and res and res not in preflight_known_role_paths:
                candidates = [
                    p
                    for p in preflight_known_role_paths
                    if len(p) > len(res) and p[-len(res) :] == res
                ]
                if len(candidates) == 1:
                    return candidates[0]
            return res

        def _task_identity(task: TaskRunState) -> str:
            return task.task_id or task.name

        latest_task = next(reversed(play.tasks.values())) if play.tasks else None
        latest_task_id = _task_identity(latest_task) if latest_task else None
        has_running_tasks = any(
            any(hs.status == Status.RUNNING for hs in t.hosts.values())
            or (not t.hosts and t.status == Status.RUNNING)
            for t in play.tasks.values()
        )

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
            # A task with at least one FAILED or UNREACHABLE host stays visible
            # in the tree while no further task has started or is running,
            # so the user can see the failure summary during the gap (TC-329).
            # Once the next task starts, it drops off.
            if not has_running_tasks and _task_identity(runtime) == latest_task_id:
                if any(
                    _effective_status(hs) in (Status.FAILED, Status.UNREACHABLE)
                    for hs in runtime.hosts.values()
                ):
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
                task_name_stripped = strip_role_prefix(task_name)
                for candidate_name, candidate_tasks in runtime_by_name.items():
                    stripped_candidate_name = strip_role_prefix(candidate_name)
                    if (
                        not _is_template_match(task_name, candidate_name)
                        and not _is_template_match(task_name, stripped_candidate_name)
                        and not _is_template_match(task_name_stripped, candidate_name)
                        and not _is_template_match(task_name_stripped, stripped_candidate_name)
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
            inherited_role_path: tuple[str, ...],
            preferred_hosts: set[str] | None,
            matched_runtime_task_ids: set[str],
        ) -> None:
            for entry in entries:
                if isinstance(entry, RoleGroupDefinition):
                    child_path = inherited_role_path + (entry.role,)
                    _emit_preflight_entries(
                        entry.tasks, child_path, preferred_hosts, matched_runtime_task_ids
                    )
                    continue

                # Build the preflight portion of the role path for this
                # task. ``inherited_role_path`` is the enclosing role
                # group chain; ``entry.role`` is the task's own role
                # (matches the enclosing group for grouped tasks, or a
                # sibling role for ungrouped tasks).
                if entry.role is not None:
                    preflight_path = _collapse_role_path(inherited_role_path + (entry.role,))
                else:
                    preflight_path = inherited_role_path

                runtime = _pick_runtime(
                    entry.name, matched_runtime_task_ids, preferred_hosts, entry.path
                )
                if runtime is None and "{{" in entry.name:
                    # Preflight name has unresolved Jinja2 template — try
                    # to find a runtime task whose resolved name matches
                    # the template skeleton.
                    entry_stripped = strip_role_prefix(entry.name)
                    for candidate_name in runtime_by_name:
                        stripped_candidate_name = strip_role_prefix(candidate_name)
                        if (
                            not _is_template_match(entry.name, candidate_name)
                            and not _is_template_match(entry.name, stripped_candidate_name)
                            and not _is_template_match(entry_stripped, candidate_name)
                            and not _is_template_match(entry_stripped, stripped_candidate_name)
                        ):
                            continue
                        runtime = _pick_runtime(
                            candidate_name, matched_runtime_task_ids, preferred_hosts
                        )
                        if runtime is not None:
                            break
                    if runtime is None:
                        # Empty-skeleton names (entirely ``{{ ... }}``) can
                        # never match any runtime task — no static fragment
                        # exists to anchor a future match. Skip the entry
                        # rather than emitting it as a permanent orphan.
                        fragments = [f for f in _TEMPLATE_RE.split(entry.name) if f]
                        if not fragments:
                            continue

                preflight_name_chain = _name_role_chain(entry.name)
                runtime_name_chain = _name_role_chain(runtime.name) if runtime is not None else ()
                full_role_path = _extend_role_path(
                    preflight_path, preflight_name_chain, runtime, runtime_name_chain
                )
                kind = _classify(runtime)
                emitted_names.add(entry.name)
                next_preferred_hosts = preferred_hosts
                if runtime is not None:
                    # Emit under the runtime (resolved) name so host
                    # leaves and status are correct.
                    emitted_names.add(runtime.name)
                    runtime_identity = _task_identity(runtime)
                    # Skip when this runtime task was already emitted
                    # via a sibling walk above (e.g. ``include_role``
                    # sibling graft in ``_graft_role_pending_siblings``
                    # adds the runtime task itself as a sibling under
                    # the parent stub — both paths reach this point
                    # for the same TaskRunState and would otherwise
                    # emit it twice: once as running, once as pending).
                    if runtime_identity in emitted_task_ids:
                        continue
                    emitted_task_ids.add(runtime_identity)
                    stripped = strip_role_prefix(runtime.name)
                    if stripped != runtime.name:
                        emitted_names.add(stripped)
                    if runtime.hosts:
                        next_preferred_hosts = set(runtime.hosts)
                # Skip preflight entries that name a runtime task we
                # already emitted on an earlier walk. ``_pick_runtime``
                # returns ``None`` here because the runtime identity is
                # already in ``matched_runtime_task_ids`` (it was
                # matched when its sibling entry was processed); the
                # ``runtime is not None`` branch above can't catch
                # this case. Without this guard the same TaskDefinition
                # would render twice: once as running, once as pending.
                elif entry.name in emitted_names and any(
                    tid in emitted_task_ids
                    for tid in (_task_identity(t) for t in runtime_by_name.get(entry.name, []))
                ):
                    continue
                if kind != "completed":
                    items.append((kind, entry.name, full_role_path, runtime))

                if entry.children:
                    _emit_preflight_entries(
                        entry.children,
                        full_role_path,
                        next_preferred_hosts,
                        matched_runtime_task_ids,
                    )

        if play_def is not None:
            matched_runtime_task_ids: set[str] = set()
            _emit_preflight_entries(play_def.tasks, (), None, matched_runtime_task_ids)

        # Runtime-only tasks (dynamic include_tasks, or no preflight at all).
        # When preflight entries were emitted above, treat the runtime
        # task as the natural next task in the chain — i.e. extend the
        # last preflight item's role path with the runtime's name
        # chain. This keeps deep-nested runtime tasks (e.g. a task
        # grafted under an ``include_role`` discovered at runtime that
        # the preflight couldn't see) inside the same nesting context
        # as the surrounding preflight tasks, instead of breaking out
        # into a sibling role block.
        last_emitted_role_path: tuple[str, ...] = ()
        for item in items:
            last_emitted_role_path = item[2]

        for task in play.tasks.values():
            task_identity = _task_identity(task)
            if task_identity in emitted_task_ids:
                continue
            kind = _classify(task)
            if kind == "completed":
                continue
            runtime_name_chain = _name_role_chain(task.name)
            full_role_path = _extend_role_path(last_emitted_role_path, (), task, runtime_name_chain)

            items.append((kind, task.name, full_role_path, task))
            emitted_names.add(task.name)
            emitted_task_ids.add(task_identity)
            stripped = strip_role_prefix(task.name)
            if stripped != task.name:
                emitted_names.add(stripped)

        items = _cluster_items_by_role_path(items)
        self._prp_render_memo[id(play)] = items
        return items

    def _play_def_for(self, play: "PlayRunState") -> "PlayDefinition | None":
        """Return the matching preflight PlayDefinition, or None.

        Resolution order:

        1. The explicit mapping built during tree construction (handles
           duplicate play names correctly — each runtime play is paired
           with exactly one definition).
        2. ID-based lookup (preflight ``PlayDefinition.id`` matches
           runtime ``play_id`` — works when ansible uses the same IDs).
        3. Name-based lookup as last resort (may return the wrong
           definition when two plays share a name).
        """
        if play.play_id:
            matched = self._runtime_play_to_def.get(play.play_id)
            if play.play_id in self._runtime_play_to_def:
                return matched
        by_id = self._state._play_def_by_id
        if by_id is not None and play.play_id:
            match = by_id.get(play.play_id)
            if match is not None:
                return match
        by_name = self._state._play_def_by_name
        if by_name is None:
            return None
        return by_name.get(play.name)

    def _task_role(self, task_name: str) -> tuple[str, ...]:
        """Return the full role path a task belongs to, or ``()``.

        Preflight ``--list-tasks`` records role membership both via
        ``RoleGroupDefinition`` (grouped, 5+ consecutive same-role) and
        ``TaskDefinition.role`` (ungrouped, <5 tasks). First match wins.
        Memoised on first call.

        Returns the *full* path (outermost to innermost) so callers
        don't have to reconstruct the nesting from a single role name.
        An empty tuple means the task sits directly under a play with
        no role context.

        Consecutive duplicate role names are collapsed (``(A, A)`` →
        ``(A,)``) so the result matches the tree's structural model —
        the projection emits one ``role:`` header per unique level, not
        per element of the path.

        Runtime task names may carry the ``"role : "`` prefix
        (e.g. ``"podman : Install Podman"``); the stripped form is
        also tried so that lookups succeed against the preflight index
        which stores bare task names.
        """
        self._refresh_tree_cache()
        if self._role_index is None:
            idx: dict[str, tuple[str, ...]] = {}
            known_roles: set[str] = set()
            for play_def in self._state.definitions:
                for task_def, role_path in iter_preflight_task_defs(play_def.tasks):
                    if role_path:
                        idx.setdefault(task_def.name, _collapse_role_path(role_path))
                        known_roles.add(role_path[-1])
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
        result: tuple[str, ...] | None = self._role_index.get(task_name)
        if result is None:
            result = self._role_index.get(strip_role_prefix(task_name))
        if result is None:
            # Try template-variable match: runtime name "Get ID for
            # angie-sidecar" vs index key "Get ID for {{ username }}".
            for preflight_name, role_path in self._role_index.items():
                if _is_template_match(preflight_name, task_name):
                    return role_path
        if not result and " : " in task_name:
            # Runtime "role : task" prefix with no preflight entry —
            # extract role name directly from the prefix (include_role).
            # Only accept if the role was seen in preflight or repeated
            # across runtime tasks (avoids false positives from task names
            # that happen to contain " : ").
            role_from_prefix = task_name.split(" : ", 1)[0].strip()
            if not role_from_prefix or any(ch.isspace() for ch in role_from_prefix):
                return ()
            if self._known_roles is not None and role_from_prefix in self._known_roles:
                return (role_from_prefix,)
            if (
                self._runtime_role_counts is not None
                and self._runtime_role_counts.get(role_from_prefix, 0) > 1
            ):
                return (role_from_prefix,)
        return result or ()

    @staticmethod
    def _task_line(task: TaskRunState, depth: int, pending: int = 0) -> TreeLine:
        # Count tally for the parenthesised summary on the task line.
        # Order matters for the label: ok, changed, running, failed,
        # unreachable, skipped, pending — same order as the spec example.
        # ``pending`` (hosts the play targets that have not started this
        # task yet — throttle/serial/free) is supplied by the caller;
        # it is not derivable from ``task.hosts`` alone.
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
            ("pending", pending),
        ):
            if n > 0:
                parts.append(f"{n} {label}")
        suffix = f"  ({', '.join(parts)})" if parts else ""
        return TreeLine(
            depth=depth,
            kind="task",
            label=f"{strip_role_prefix(task.name)}{suffix}",
            glyph=None,
            status=Status.RUNNING,
            elapsed_s=None,
        )
