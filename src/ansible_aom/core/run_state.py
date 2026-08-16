"""RunState: the mutable, in-memory execution state for an AOM run.

This module owns the ``RunState`` dataclass and the small helpers it
shares with the rest of ``core/``:

- Timestamp parsing (``_parse_timestamp``, ``_parse_play_window_start``)
- Preflight tree flatteners (``_iter_leaf_task_defs``, ``_leaves_of_role_group``)
- ``count_leaf_tasks`` — leaf count, used by infra callers that need a
  number without materialising the list

RunState's only cross-module dependency is a lazy
``from ansible_aom.core.includes import discover_include_with_runtime_path``
inside the two task-start handlers, which avoids an import cycle
(includes.py imports RunState to populate its caches; run_state.py must
not import includes.py at module load time).

Lives in ``core/`` because every consumer — infrastructure (compact,
tui, formats, ansible runner) and other ``core/`` modules — imports
from here. The class is the central state object of AOM; it must not
import from ``compact/``, ``tui/``, ``formats/``, or ``renderer/``.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, cast

from ansible_aom.core.event_types import JsonlEvent, JsonlHostResult, JsonlPlay, JsonlTask
from ansible_aom.core.models import (
    HostRunState,
    IncludeCacheEntry,
    PlayDefinition,
    PlayRunState,
    RoleCacheEntry,
    RoleGroupDefinition,
    Status,
    TaskDefinition,
    TaskRunState,
    _is_template_match,
    _iter_task_def_tree,
    runtime_role_from_task_name,
    strip_role_prefix,
)
from ansible_aom.core.state_machine import (
    MAX_HOSTS_PER_TASK,
    MAX_PLAYS,
    MAX_TASKS_PER_PLAY,
    MAX_TOTAL_HOST_RUN_STATES,
)
from ansible_aom.core.timestamp import parse_iso_timestamp

logger = logging.getLogger(__name__)

_JINJA_RE = re.compile(r"\{\{.*?\}\}")


def _extract_role_from_include_stub(name: str) -> str | None:
    """Extract the target role from an ``include_role`` / ``import_role`` stub name.

    ``--list-tasks`` emits the stub with the directive as its display name
    (e.g. ``"include_role: podman"`` or
    ``"angie_ssl_terminator : include_role: podman"`` when nested inside
    another role).  Returns the bare role name (``"podman"``) or ``None``
    when *name* is not an include/import stub.

    Accepts both the short form (``include_role:``) and the FQCN form
    (``ansible.builtin.include_role:``).
    """
    for part in name.split(" : "):
        for directive in (
            "include_role:",
            "import_role:",
            "ansible.builtin.include_role:",
            "ansible.builtin.import_role:",
        ):
            if part.startswith(directive):
                role = part[len(directive) :].strip()
                if role:
                    return role
    return None


def _parse_timestamp(event: JsonlEvent) -> datetime:
    """Parse timestamp from event, defaulting to current time."""
    ts_str = event.get("_timestamp")
    if not ts_str:
        return datetime.now(timezone.utc)
    try:
        return parse_iso_timestamp(ts_str)
    except ValueError, TypeError:
        return datetime.now(timezone.utc)


def _parse_play_window_start(play_data: JsonlPlay) -> str | None:
    """Extract the window discriminator from ``play.duration.start`` if present."""
    duration = play_data.get("duration")
    if not isinstance(duration, dict):
        return None
    window_start = duration.get("start")
    return window_start if isinstance(window_start, str) else None


def _iter_leaf_task_defs(plays: list[PlayDefinition]) -> list[TaskDefinition]:
    """Flatten preflight definitions into the leaf TaskDefinitions visible by name.

    ``RoleGroupDefinition`` is unwrapped so its inner tasks are reachable; nested
    ``TaskDefinition.children`` are also traversed so recursive include/import
    expansions are visible to the grafting logic. A nested
    ``RoleGroupDefinition`` inside a role group's ``tasks`` is recursed into
    too — this is the role-in-role data shape that the recursive-nesting plan
    introduced.
    """
    leaves: list[TaskDefinition] = []
    for play in plays:
        for entry in play.tasks:
            if isinstance(entry, RoleGroupDefinition):
                for inner in entry.tasks:
                    if isinstance(inner, RoleGroupDefinition):
                        leaves.extend(_leaves_of_role_group(inner))
                    else:
                        leaves.extend(_iter_task_def_tree(inner))
            else:
                leaves.extend(_iter_task_def_tree(entry))
    return leaves


def _leaves_of_role_group(group: RoleGroupDefinition) -> list[TaskDefinition]:
    """Return leaf TaskDefinitions reachable from a possibly-nested role group."""
    leaves: list[TaskDefinition] = []
    for entry in group.tasks:
        if isinstance(entry, RoleGroupDefinition):
            leaves.extend(_leaves_of_role_group(entry))
        else:
            leaves.extend(_iter_task_def_tree(entry))
    return leaves


def count_leaf_tasks(plays: list[PlayDefinition]) -> int:
    """Total number of leaf TaskDefinitions across all preflight plays.

    Shared by infrastructure callers that need a task count without
    materialising the list (the runner persisting ``preflight_task_count``
    to ``meta.json``, the compact renderer's status-bar denominator, …).
    Lives in ``core/`` so layering rules (no infra-to-infra imports) are
    satisfied with one definition.
    """
    return len(_iter_leaf_task_defs(plays))


class _BoundedSet(set):  # noqa: FURB189 — subclassing set is intentional
    """A ``set`` that drops itself when it exceeds a cap on insert.

    R15: ``RunState`` carries several set-shaped dedupe containers that
    can grow without bound as events arrive. ``_BoundedSet`` enforces
    a soft ceiling — when ``add`` is called at or past the cap, the
    entire set is cleared before inserting the new value.

    Clear-on-cap is simpler than per-element FIFO eviction and is
    correct for the dedupe helpers here: losing older entries means a
    future duplicate of those values is "seen" again, which the graft
    pass handles gracefully (a re-seen task is re-grafted; cheap and
    bounded by the cap).
    """

    __slots__ = ("_cap",)

    def __init__(self, cap: int) -> None:
        super().__init__()
        self._cap = cap

    def add(self, value: object) -> None:  # type: ignore[override]
        if len(self) >= self._cap:
            self.clear()
        super().add(value)


class _BoundedDict(dict):  # noqa: FURB189 — subclassing dict is intentional
    """A ``dict`` that drops itself when it exceeds a cap on insert.

    R15 sibling to ``_BoundedSet`` for the per-play ``_play_window_counts``
    dict — same clear-on-cap behaviour, same rationale.
    """

    __slots__ = ("_cap",)

    def __init__(self, cap: int) -> None:
        super().__init__()
        self._cap = cap

    def __setitem__(self, key: object, value: object) -> None:  # type: ignore[override]
        if key not in self and len(self) >= self._cap:
            self.clear()
        super().__setitem__(key, value)


# R15: cap values. Aligned with the documented memory bounds from
# state_machine.py so a cap hit here has a documented rationale and a
# consistent order of magnitude across the codebase.
_GRAFTED_UUIDS_CAP = MAX_TASKS_PER_PLAY
_GRAFTED_ROLE_NAMES_CAP = MAX_TASKS_PER_PLAY
_PLAY_WINDOW_COUNTS_CAP = MAX_PLAYS


def _reserve_host_run_state(
    state: RunState,
    task: TaskRunState,
    hostname: str,
    new_state: HostRunState,
) -> bool:
    """Bookkeeping for inserting a HostRunState under R12's caps.

    Two ceilings apply to host insertion:

    - ``MAX_HOSTS_PER_TASK``: a per-task cap on the ``task.hosts`` dict
      so a single task with a runaway fan-out (one host per loop iter
      over a 100 000-entry list) doesn't blow up one task in particular.
    - ``MAX_TOTAL_HOST_RUN_STATES``: a per-run cap on the cumulative
      number of HostRunState objects created across every play/task
      pair. Even with per-task caps, a playbook with 200 plays × 5 000
      hosts per task would still be 1 000 000 HostRunState objects —
      this is the global guard that catches the aggregate case.

    The caller has already decided *what* HostRunState to insert; this
    helper enforces the caps and bumps ``truncated_events`` if either
    ceiling is hit. Returns ``True`` if the insertion was allowed,
    ``False`` if it was dropped. The caller is expected to no-op when
    ``False`` is returned (no partial state mutation).

    ``task`` and ``hostname`` are read-only here — the helper does not
    mutate them; it only decides whether the caller's intended
    insertion should proceed.
    """
    if hostname in task.hosts:
        # Replacing an existing host entry is not growth — no cap
        # accounting required.
        return True
    if len(task.hosts) >= MAX_HOSTS_PER_TASK:
        state.truncated_events["hosts"] = state.truncated_events.get("hosts", 0) + 1
        logger.warning(
            "MAX_HOSTS_PER_TASK=%d reached on task %r; dropping host %r",
            MAX_HOSTS_PER_TASK,
            task.task_id,
            hostname,
        )
        return False
    if state._total_host_run_states >= MAX_TOTAL_HOST_RUN_STATES:
        state.truncated_events["total_hosts"] = state.truncated_events.get("total_hosts", 0) + 1
        logger.warning(
            "MAX_TOTAL_HOST_RUN_STATES=%d reached; dropping host %r on task %r",
            MAX_TOTAL_HOST_RUN_STATES,
            hostname,
            task.task_id,
        )
        return False
    state._total_host_run_states += 1
    return True


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
    _last_matched_task_def: TaskDefinition | None = field(default=None, init=False, repr=False)
    _grafted_uuids: set[str] = field(
        default_factory=lambda: _BoundedSet(_GRAFTED_UUIDS_CAP),
        init=False,
        repr=False,
    )
    # Per-(parent, role) dedupe keys for ``_graft_role_pending_siblings``.
    # When a runtime task reveals a new ``include_role``, this set records
    # the pair so the role's full task list is grafted only once even if
    # later task_start events for tasks in the same role arrive.
    _grafted_role_names: set[str] = field(
        default_factory=lambda: _BoundedSet(_GRAFTED_ROLE_NAMES_CAP), init=False, repr=False
    )
    # R5: count unknown _event values so the renderer can surface a
    # one-line "(N unknown events: foo×3)" hint at completion. Events
    # with no _event field at all are degenerate (not "future-version
    # drift") and aren't counted here.
    unknown_events: dict[str, int] = field(default_factory=dict)
    # Terminal runner events (v2_runner_on_ok/failed/skipped/unreachable)
    # whose (play_id, task_id) — and the path/name fallback in
    # ``_resolve_runner_task`` — matched no known task. Each drop leaves
    # host state stale (the exact "silently dropped" class the stats
    # handler cleans up at run end), so it must be observable. Keyed by
    # event type; surfaced as a completion footer by the renderers.
    unmatched_events: dict[str, int] = field(default_factory=dict)
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
    _task_def_index: dict[str, TaskDefinition] | None = field(default=None, init=False, repr=False)
    _task_def_by_path: dict[str, TaskDefinition] | None = field(
        default=None, init=False, repr=False
    )
    _play_def_by_id: dict[str, PlayDefinition] | None = field(default=None, init=False, repr=False)
    _play_def_by_name: dict[str, PlayDefinition] | None = field(
        default=None, init=False, repr=False
    )
    _include_cache: dict[str, IncludeCacheEntry] = field(
        default_factory=dict, init=False, repr=False
    )
    _role_cache: dict[str, RoleCacheEntry] = field(default_factory=dict, init=False, repr=False)
    _play_window_counts: dict[str, int] = field(
        default_factory=lambda: _BoundedDict(_PLAY_WINDOW_COUNTS_CAP), init=False, repr=False
    )
    # R12: running tally of HostRunState entries created across the
    # entire run, used to enforce MAX_TOTAL_HOST_RUN_STATES (a
    # whole-run ceiling that complements the per-task cap).
    _total_host_run_states: int = field(default=0, init=False, repr=False)
    # R12: counters for events dropped by the in-state memory caps
    # (MAX_PLAYS / MAX_TASKS_PER_PLAY / MAX_HOSTS_PER_TASK /
    # MAX_TOTAL_HOST_RUN_STATES). Keys are the cap name (``"plays"``,
    # ``"tasks"``, ``"hosts"``, ``"total_hosts"``); values are the
    # number of events dropped since the run started. Empty dict means
    # no caps were hit. The renderers surface these in a one-line
    # completion footer so the user knows the run was clipped.
    truncated_events: dict[str, int] = field(default_factory=dict)
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

    def handle_event(self, event: JsonlEvent) -> None:
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
            "aom_stderr_line": self._handle_internal_event,
            "aom_connection_acquired": self._handle_internal_event,
            "aom_connection_released": self._handle_internal_event,
        }

        handler = handler_map.get(event_type)
        if handler:
            handler(event, ts)
        elif event_type:
            self.unknown_events[event_type] = self.unknown_events.get(event_type, 0) + 1
            logger.debug(f"Unknown event type: {event_type}")

    def _handle_internal_event(self, event: JsonlEvent, ts: datetime) -> None:
        """Recognize an AOM-internal synthetic event that carries no run-state.

        ``aom_stderr_line`` (from the PTY parser) and the ``aom_connection_*``
        pair (from the bundled aom_connection notification callback) are
        consumed by other layers — the parser's per-host connection tracking
        and the inspect verbose panel — not by the run-state machine. They are
        dispatched here so they are *handled* like every other known event
        type instead of falling through to the R5 future-drift counter, which
        would otherwise report a bogus "(N unknown events: aom_stderr_line×N)"
        footer on any run that records stderr lines.
        """

    def _handle_v2_playbook_on_start(self, event: JsonlEvent, ts: datetime) -> None:
        """Handle v2_playbook_on_start event."""
        if self.start_time is None:
            self.start_time = ts
            self.status = Status.RUNNING

    def _finalize_play(self, play: PlayRunState, ts: datetime) -> None:
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

    def _handle_v2_playbook_on_play_start(self, event: JsonlEvent, ts: datetime) -> None:
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
        # the entry is replaced below anyway). Skip plays under
        # strategy: free — hosts run tasks independently there, so a
        # play_start for the next play can arrive while the prior play's
        # hosts are still running their tasks. Force-finalising them
        # destroys live state and produces a stale "all OK" tree.
        for prior_id, prior in self.plays.items():
            if prior_id == play_id:
                continue
            if prior.detected_strategy == "free":
                continue
            self._finalize_play(prior, ts)
            if prior.status == Status.RUNNING:
                prior.status = Status.COMPLETED

        # Cross-play graft guard — the cursor must reset at every play
        # boundary so unknown tasks in the new play don't attach to the
        # previous play's last matched task. Without this, an unknown
        # task_start arriving between this play_start and the new play's
        # first matched task would be grafted as a child of the prior
        # play's last preflight task.
        self._last_matched_task_def = None

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
            # R12 memory bound. A runaway include loop or a malformed
            # play stream must not grow self.plays without ceiling;
            # an unbounded play dict OOMs the renderer and freezes
            # the live tree. The re-emit case (same play_id already
            # present) is handled above and is never subject to this
            # check — refreshing an existing play's window metadata
            # isn't a memory growth.
            if len(self.plays) >= MAX_PLAYS:
                self.truncated_events["plays"] = self.truncated_events.get("plays", 0) + 1
                logger.warning(
                    "MAX_PLAYS=%d reached; dropping play %r (%d plays dropped so far)",
                    MAX_PLAYS,
                    play_id,
                    self.truncated_events["plays"],
                )
                return
            self.plays[play_id] = PlayRunState(
                play_id=play_id,
                name=play_name,
                status=Status.RUNNING,
                window_start=play_window_start,
                window_ordinal=play_window_ordinal,
            )

    def _resolve_play_for_task(self, task_id: str) -> str | None:
        """Return the play_id that already owns this task_id, or ``None``.

        Searches the runtime plays dict for a play whose ``tasks`` already
        contains ``task_id``. Used as a fallback when an event arrives
        without a ``play`` field but carries a ``task.id`` we have already
        seen — we then know which play the event belongs to without
        trusting the cursor (``_current_play_id``), which can have moved
        forward under ``strategy: free`` even though late runner events for
        the prior play are still streaming in.
        """
        if not task_id:
            return None
        for play_id, play in self.plays.items():
            if task_id in play.tasks:
                return play_id
        return None

    def _resolve_play_id(self, event: JsonlEvent) -> str:
        """Resolve play_id from event, _current_play_id, or task ownership.

        Resolution order:

        1. ``event["play"]["id"]`` when the event carries an explicit play.
        2. The play that already owns ``event["task"]["id"]`` in our runtime
           state — this catches ``v2_runner_on_*`` events that arrive after
           a new ``v2_playbook_on_play_start`` has advanced ``_current_play_id``
           but still reference a task that belongs to the previous play.
        3. ``_current_play_id`` — last-resort cursor, used when the task is
           brand new (e.g. ``v2_runner_item_on_*`` before any matching
           ``v2_playbook_on_task_start`` has fired).
        """
        play_data = event.get("play")
        if play_data and isinstance(play_data, dict):
            return cast(str, play_data.get("id", ""))
        # No explicit play on the event — look up the play that owns this
        # task. Falls back to _current_play_id only when the task is brand
        # new (e.g., v2_runner_item_on_* before any task_start has fired).
        task_data = event.get("task")
        task_id = task_data.get("id", "") if isinstance(task_data, dict) else ""
        if task_id:
            owner = self._resolve_play_for_task(task_id)
            if owner is not None:
                return owner
        return self._current_play_id or ""

    def _resolve_runner_task(self, event: JsonlEvent) -> TaskRunState | None:
        """Find the TaskRunState a terminal runner event belongs to.

        Terminal events (``v2_runner_on_ok`` and friends) used to be
        dropped silently whenever the ``(play_id, task_id)`` lookup
        missed — leaving hosts stuck as RUNNING in the tree while the
        log already streamed their results. Resolution order:

        1. ``task.id`` inside the play resolved by ``_resolve_play_id``.
        2. ``task.id`` owned by any other play (covers events carrying a
           stale or unknown ``play.id``).
        3. Within the resolved play (or the ``_current_play_id`` cursor
           when the event's play is unknown): a task with the same
           ``task.path``, then the same ``task.name``. Among several
           matches, prefer the most recent RUNNING one — a completed
           earlier instance of a re-run task must not swallow results
           meant for the live one.

        Returns ``None`` when nothing matches; the caller counts the
        drop in ``unmatched_events``.
        """
        task_data = self._task_dict(event)
        task_id = task_data.get("id", "")
        play = self.plays.get(self._resolve_play_id(event))
        if play is not None and task_id in play.tasks:
            return play.tasks[task_id]
        if task_id:
            owner_id = self._resolve_play_for_task(task_id)
            if owner_id is not None:
                return self.plays[owner_id].tasks[task_id]
        if play is None:
            play = self.plays.get(self._current_play_id or "")
        if play is None:
            return None
        task_path = task_data.get("path")
        task_name = task_data.get("name", "")
        candidates: list[TaskRunState] = []
        if task_path:
            candidates = [t for t in play.tasks.values() if t.path == task_path]
        if not candidates and task_name:
            candidates = [t for t in play.tasks.values() if t.name == task_name]
        if not candidates:
            return None
        for task in reversed(candidates):
            if task.status == Status.RUNNING:
                return task
        return candidates[-1]

    def _note_unmatched(self, event: JsonlEvent) -> None:
        """Count a terminal runner event that matched no known task."""
        event_type = event.get("_event", "")
        self.unmatched_events[event_type] = self.unmatched_events.get(event_type, 0) + 1
        logger.warning(
            "Unmatched %s event dropped (task=%r); host state may go stale",
            event_type,
            self._task_dict(event).get("name", ""),
        )

    def _parent_role_from_cache(self, task_name: str) -> str | None:
        """Return the parent role recorded in ``_role_cache`` for a runtime task.

        Used by ``_handle_v2_playbook_on_task_start`` /
        ``_handle_v2_runner_on_start`` to populate ``TaskRunState.parent_role``
        when a runtime task carries the ``"role : "`` prefix of a role that
        ``includes.py`` discovered as nested in another role. Returns
        ``None`` when the task has no ``" : "`` prefix, or when the role
        cache has no entry (or the entry's ``parent_role`` is unset).

        The cache key uses the lowercase-stripped role name (matches
        ``_discover_role``'s normalisation), so we normalise the runtime
        prefix the same way before lookup.
        """
        runtime_role = runtime_role_from_task_name(task_name)
        if runtime_role is None:
            return None
        cache_key = runtime_role.lower().strip()
        entry = self._role_cache.get(cache_key)
        if entry is None:
            return None
        return entry.parent_role

    def _graft_or_match_task(
        self,
        task_id: str,
        task_name: str,
        task_path: str | None = None,
        play_id: str | None = None,
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

        leaf: TaskDefinition | None = None
        play_def_target: PlayDefinition | None = None

        if play_id:
            if self._play_def_by_id:
                play_def_target = self._play_def_by_id.get(play_id)
            if play_def_target is None and play_id in self.plays and self._play_def_by_name:
                play_def_target = self._play_def_by_name.get(self.plays[play_id].name.strip())

        task_name_stripped = strip_role_prefix(task_name)

        if play_def_target is not None:
            # First search within the target play's task definitions
            if task_path:
                for cand in _iter_leaf_task_defs([play_def_target]):
                    if cand.path == task_path:
                        leaf = cand
                        break
            if leaf is None:
                for cand in _iter_leaf_task_defs([play_def_target]):
                    if cand.name == task_name or strip_role_prefix(cand.name) == task_name_stripped:
                        leaf = cand
                        break
                    if "{{" in cand.name:
                        cand_stripped = strip_role_prefix(cand.name)
                        if (
                            _is_template_match(cand.name, task_name)
                            or _is_template_match(cand.name, task_name_stripped)
                            or _is_template_match(cand_stripped, task_name)
                            or _is_template_match(cand_stripped, task_name_stripped)
                        ):
                            leaf = cand
                            break

        if leaf is None and play_def_target is None:
            # Fall back to global index when play is unknown
            path_index = self._task_def_by_path
            if task_path and path_index is not None:
                leaf = path_index.get(task_path)

            index = self._task_def_index
            if leaf is None and index is not None:
                leaf = index.get(task_name)
                if leaf is None:
                    leaf = index.get(task_name_stripped)
                if leaf is None:
                    for preflight_name, tdef in index.items():
                        if "{{" not in preflight_name:
                            continue
                        preflight_stripped = strip_role_prefix(preflight_name)
                        if (
                            _is_template_match(preflight_name, task_name)
                            or _is_template_match(preflight_name, task_name_stripped)
                            or _is_template_match(preflight_stripped, task_name)
                            or _is_template_match(preflight_stripped, task_name_stripped)
                        ):
                            leaf = tdef
                            break

        if leaf is not None:
            self._last_matched_task_def = leaf
            return

        parent = self._last_matched_task_def
        if parent is not None and play_def_target is not None:
            # Ensure parent belongs to the target play definition
            if parent.play_id != play_def_target.id:
                parent = None
                current_play_leaves = list(_iter_leaf_task_defs([play_def_target]))
                if current_play_leaves:
                    parent = current_play_leaves[-1]

        if parent is None:
            # No preflight task has matched yet — leave the unknown task as
            # an orphan rather than grafting it onto an arbitrary node.
            return

        # Idempotency: when ``_graft_role_pending_siblings`` already
        # grafted the runtime task's siblings (which include the
        # runtime task itself, prefixed with the role), don't re-add
        # the same name under the same parent. Without this every
        # subsequent ``task_start`` for a role task would re-graft
        # the task the sibling helper already inserted, growing the
        # children list past the role's real task count.
        matched_child: TaskDefinition | None = None
        task_name_stripped = strip_role_prefix(task_name)
        for child in parent.children:
            if child.name == task_name or strip_role_prefix(child.name) == task_name_stripped:
                matched_child = child
                break
            if "{{" in child.name:
                child_stripped = strip_role_prefix(child.name)
                if (
                    _is_template_match(child.name, task_name)
                    or _is_template_match(child.name, task_name_stripped)
                    or _is_template_match(child_stripped, task_name)
                    or _is_template_match(child_stripped, task_name_stripped)
                ):
                    matched_child = child
                    break
        if matched_child is not None:
            if task_id:
                self._grafted_uuids.add(task_id)
            self._last_matched_task_def = matched_child
            return

        # Grafted task: detect role-in-role via the runtime prefix. When the
        # runtime name carries ``"role : "`` with a different role than the
        # preflight parent, the grafted TaskDefinition lives under the *inner*
        # role. ``parent_role`` carries the outer role so the projection can
        # render the inner role as a sub-branch. Plain dynamic includes
        # (``include_tasks`` with no role prefix) inherit the parent role
        # and propagate the existing ``parent_role`` chain.
        runtime_role = runtime_role_from_task_name(task_name)
        # Generalized include_role target detection.
        #
        # When the parent is an include_role/import_role stub whose name
        # contains the directive (e.g. ``"include_role: podman"``), use
        # the stub's target role instead of the outermost ``" : "`` prefix
        # from the runtime task name.  That outer prefix may be the
        # *enclosing* role chain (e.g. ``"angie_ssl_terminator"`` from
        # ``"angie_ssl_terminator : podman : Install podman"``), not the
        # inner role that include_role actually targets.
        #
        # When the stub has an *explicit* name (e.g. ``"Apply podman role"``)
        # the directive text never appears in the preflight name, so the
        # stub-name check above won't fire.  In that case we fall back to
        # examining the runtime task name: if it has at least three ``" : "``
        # segments (``outer_role : inner_role : task_name``), the
        # second-to-last segment is the include_role target.  This handles
        # both role-wrapped include_role (where ``outer_role == parent.role``)
        # and play-level include_role with an accidental outer prefix
        # (where ``parent.role is None``).
        target_role: str | None = None
        if parent.name is not None:
            target_role = _extract_role_from_include_stub(parent.name)
        if target_role is None:
            parts = task_name.split(" : ")
            if len(parts) >= 3:
                # ``"outer : inner : task"`` — parts[-2] is the inner role
                target_role = parts[-2]
        if target_role is not None:
            runtime_role = target_role
        graft_role: str | None
        graft_parent_role: str | None
        if runtime_role is not None and parent.role is not None and runtime_role != parent.role:
            graft_role = runtime_role
            graft_parent_role = parent.role
        elif runtime_role is not None and parent.role is None:
            # ``include_role:`` stub grafted from a role-less parent
            # (top-level task under a play). The runtime task reveals
            # the actual role via the ``"role : "`` prefix, so use it
            # directly. Without this branch the role would stay ``None``
            # on the grafted TaskDefinition and the projection's
            # ``role_total_tasks`` counter would miss the role entirely
            # (it keys on the innermost role name).
            graft_role = runtime_role
            graft_parent_role = parent.parent_role
        else:
            graft_role = parent.role
            graft_parent_role = parent.parent_role

        parent.children.append(
            TaskDefinition(
                name=task_name,
                role=graft_role,
                parent_role=graft_parent_role,
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

        # If the just-grafted task is the first task seen from an
        # ``include_role``, graft every other task of that role as
        # siblings under the same parent. ``--list-tasks`` does not
        # expand ``include_role`` directives (it surfaces only the
        # ``include_role:`` stub itself), so without this graft the
        # preflight tree never sees the role's pending tasks — the
        # tree projection shows only the currently-running task and
        # the rest stay invisible until they each fire their own
        # ``task_start`` event one by one.
        #
        # We use ``_grafted_role_names`` to dedupe so the sibling
        # graft runs once per (parent, role) pair. ``_role_cache``
        # already records the role's task list (``_discover_role``
        # populates it) — we read it back here so we don't re-parse
        # the role YAML on every task_start.
        if runtime_role is not None:
            self._graft_role_pending_siblings(
                role_name=runtime_role,
                current_task_name=task_name,
                parent=parent,
                graft_role=graft_role,
                graft_parent_role=graft_parent_role,
            )

    def _graft_role_pending_siblings(
        self,
        *,
        role_name: str,
        current_task_name: str,
        parent: TaskDefinition,
        graft_role: str | None,
        graft_parent_role: str | None,
    ) -> None:
        """Graft every other task of *role_name* as a sibling of the
        just-grafted current task under *parent*.

        Called from ``_graft_or_match_task`` when the runtime task
        reveals a new role (i.e. carries the ``"role : "`` prefix that
        ``include_role`` adds at runtime). ``--list-tasks`` does not
        expand ``include_role``, so without this pass the preflight
        tree only carries the one task that triggered the graft — the
        rest of the role's tasks stay invisible until each one fires
        its own ``task_start`` event. By grafting them up front the
        projection can show them all as pending right away.

        Idempotent: a per-``(parent_id, role_name)`` key in
        ``_grafted_role_names`` skips the second-and-later pass for
        the same role under the same parent. Tasks already present
        under *parent* are also skipped (the current task's own
        grafted entry would otherwise be duplicated).

        When the role's tasks file is missing or unparseable
        (``_discover_role`` returns ``None``) the graft is a no-op —
        the existing per-event graft remains the fallback for the
        currently-running task only.
        """
        from ansible_aom.core.includes import _discover_role

        parent_key = f"{parent.play_id}:{graft_parent_role or ''}:{role_name.lower()}"
        if parent_key in self._grafted_role_names:
            return
        self._grafted_role_names.add(parent_key)

        entry = _discover_role(self, role_name)
        if entry is None:
            return

        # Skip names already grafted under this parent — both the
        # current task (which ``_graft_or_match_task`` just added)
        # and any earlier siblings from a previous task_start. The
        # existing ``children`` list is the source of truth for
        # what's already known about this subtree.
        existing_names = {child.name for child in parent.children}

        # Also skip names already started at runtime under the same
        # play — their ``TaskRunState`` entries mean they've already
        # been grafted by ``_graft_or_match_task`` and re-adding
        # them would double the count in the tree.
        play = self.plays.get(parent.play_id)
        runtime_started_names: set[str] = set()
        if play is not None:
            for runtime_task in play.tasks.values():
                runtime_started_names.add(runtime_task.name)
                stripped = strip_role_prefix(runtime_task.name)
                if stripped != runtime_task.name:
                    runtime_started_names.add(stripped)

        def _sibling_matches(candidate: str, target: str) -> bool:
            if candidate == target:
                return True
            c_stripped = strip_role_prefix(candidate)
            t_stripped = strip_role_prefix(target)
            if c_stripped == t_stripped or candidate == t_stripped or c_stripped == target:
                return True
            if "{{" in candidate:
                if (
                    _is_template_match(candidate, target)
                    or _is_template_match(candidate, t_stripped)
                    or _is_template_match(c_stripped, target)
                    or _is_template_match(c_stripped, t_stripped)
                ):
                    return True
            if "{{" in target:
                if (
                    _is_template_match(target, candidate)
                    or _is_template_match(target, c_stripped)
                    or _is_template_match(t_stripped, candidate)
                    or _is_template_match(t_stripped, c_stripped)
                ):
                    return True
            return False

        for role_task_name in entry.task_names:
            # The runtime task name carries the ``"role : "`` prefix
            # (e.g. ``"podman : Install podman"``); the cached name
            # does not. Match against both forms so a pre-grafted
            # sibling isn't duplicated.
            prefixed = f"{role_name} : {role_task_name}"
            if _sibling_matches(prefixed, current_task_name) or _sibling_matches(
                role_task_name, current_task_name
            ):
                continue
            # Nested include_role: the current task may carry a
            # deeper role chain than ``role_name : role_task_name``
            # (e.g. ``angie_ssl_terminator : podman : Install podman``
            # when ``role_name="podman"``). Compare the bare task name
            # (everything after the last ``" : "``) against
            # ``role_task_name`` so the just-grafted current task
            # isn't duplicated under its own bare form. A simple
            # ``strip_role_prefix`` only removes ONE level, which is
            # insufficient for arbitrarily deep role chains.
            current_task_tail = (
                current_task_name.rsplit(" : ", 1)[-1]
                if " : " in current_task_name
                else current_task_name
            )
            if _sibling_matches(role_task_name, current_task_tail) or _sibling_matches(
                prefixed, current_task_tail
            ):
                continue
            if any(
                _sibling_matches(prefixed, en) or _sibling_matches(role_task_name, en)
                for en in existing_names
            ):
                continue
            if any(
                _sibling_matches(prefixed, rn) or _sibling_matches(role_task_name, rn)
                for rn in runtime_started_names
            ):
                continue
            parent.children.append(
                TaskDefinition(
                    name=prefixed,
                    role=graft_role,
                    parent_role=graft_parent_role,
                    tags=[],
                    play_id=parent.play_id,
                    play_order=parent.play_order,
                    task_order=-1,
                    is_dynamic=True,
                    path=None,
                )
            )
        # Always bump — even if no siblings were added we want the
        # projection's role-cache consumer to see the new state.
        self._bump_tree_revision()

    def _handle_v2_playbook_on_task_start(self, event: JsonlEvent, ts: datetime) -> None:
        """Handle v2_playbook_on_task_start event."""
        from ansible_aom.core.includes import discover_include_with_runtime_path

        task_data = self._task_dict(event)
        play_id = self._resolve_play_id(event)
        task_id = task_data.get("id", "")
        task_name = task_data.get("name", "")
        task_path = task_data.get("path")
        play_missing = play_id not in self.plays

        if task_path and ":" in task_path:
            parent_role = self._parent_role_from_cache(task_name)
            discover_include_with_runtime_path(self, task_path, parent_role)

        self._graft_or_match_task(task_id, task_name, task_path, play_id=play_id)

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
            # R12 per-play task cap. A run that emits more than
            # MAX_TASKS_PER_PLAY tasks under one play would OOM the
            # renderer. Re-emits of an existing task_id refresh the
            # entry below and never hit this branch.
            if len(play.tasks) >= MAX_TASKS_PER_PLAY:
                self.truncated_events["tasks"] = self.truncated_events.get("tasks", 0) + 1
                logger.warning(
                    "MAX_TASKS_PER_PLAY=%d reached in play %r; dropping task %r",
                    MAX_TASKS_PER_PLAY,
                    play_id,
                    task_id,
                )
                return
            play.tasks[task_id] = TaskRunState(
                task_id=task_id,
                name=task_name,
                status=Status.RUNNING,
                start_time=ts,
                path=task_path,
                parent_role=self._parent_role_from_cache(task_name),
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
        if not resolved_hosts and play.detected_strategy == "linear":
            # No preflight match (preflight failed, or the play name in
            # --list-tasks output differs from the JSONL play name).
            # Under linear every host runs every task in lockstep, so
            # the hosts seen on earlier tasks of this play are the task's
            # host set too. Without this, the task keeps an empty hosts
            # map and the tree falls back to rendering every play target
            # as RUNNING forever, contradicting the streamed results.
            # Not applicable under free strategy, where per-host
            # v2_runner_on_start is the start signal.
            #
            # Hosts whose latest result is FAILED or UNREACHABLE are
            # excluded: ansible removes them from the play, so later
            # tasks never run on them.
            last_status: dict[str, Status] = {}
            for other_task in play.tasks.values():
                if other_task.task_id == task_id:
                    continue
                for hostname, hs in other_task.hosts.items():
                    last_status[hostname] = hs.status
            resolved_hosts = sorted(
                hostname
                for hostname, status in last_status.items()
                if status not in (Status.FAILED, Status.UNREACHABLE)
            )
        for hostname in resolved_hosts:
            if hostname not in play.tasks[task_id].hosts:
                play.tasks[task_id].hosts[hostname] = HostRunState(
                    hostname=hostname,
                    status=Status.RUNNING,
                    start_time=ts,
                    synthesised=True,
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

    def _resolve_play_hosts(self, play: PlayRunState) -> list[str]:
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

    def _handle_v2_playbook_on_handler_task_start(self, event: JsonlEvent, ts: datetime) -> None:
        """Handle v2_playbook_on_handler_task_start event (same as task_start)."""
        self._handle_v2_playbook_on_task_start(event, ts)

    def _handle_v2_runner_on_start(self, event: JsonlEvent, ts: datetime) -> None:
        """Handle v2_runner_on_start event."""
        from ansible_aom.core.includes import discover_include_with_runtime_path

        task_data = self._task_dict(event)
        hostname = event.get("host", "")
        task_id = task_data.get("id", "")
        task_name = task_data.get("name", "")
        task_path = task_data.get("path")
        play_id = self._resolve_play_id(event)

        if task_path and ":" in task_path:
            parent_role = self._parent_role_from_cache(task_name)
            discover_include_with_runtime_path(self, task_path, parent_role)

        self._graft_or_match_task(task_id, task_name, task_path, play_id=play_id)

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
            # by task_start was premature. Any still-RUNNING host
            # entries synthesised under that premature assumption are
            # guesses about hosts that may not have started the task;
            # drop them and let the per-host start events rebuild the
            # map. Entries with real terminal results were replaced
            # wholesale by the terminal handlers and survive.
            self.plays[play_id].detected_strategy = "free"
            for task in self.plays[play_id].tasks.values():
                stale = [
                    stale_host
                    for stale_host, hs in task.hosts.items()
                    if hs.synthesised and hs.status == Status.RUNNING
                ]
                for stale_host in stale:
                    del task.hosts[stale_host]

        play = self.plays[play_id]

        if task_id not in play.tasks:
            # R12 per-play task cap (same logic as
            # _handle_v2_playbook_on_task_start). Free-strategy events
            # can be the first sighting of a task for a given play,
            # so this is also a possible cap-hit site.
            if len(play.tasks) >= MAX_TASKS_PER_PLAY:
                self.truncated_events["tasks"] = self.truncated_events.get("tasks", 0) + 1
                logger.warning(
                    "MAX_TASKS_PER_PLAY=%d reached in play %r; dropping task %r",
                    MAX_TASKS_PER_PLAY,
                    play_id,
                    task_id,
                )
                return
            play.tasks[task_id] = TaskRunState(
                task_id=task_id,
                name=task_name,
                status=Status.RUNNING,
                start_time=ts,
                path=task_path,
                parent_role=self._parent_role_from_cache(task_name),
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
            new_hs = HostRunState(
                hostname=hostname,
                status=Status.RUNNING,
                start_time=ts,
            )
            if _reserve_host_run_state(self, play.tasks[task_id], hostname, new_hs):
                play.tasks[task_id].hosts[hostname] = new_hs

    def _handle_v2_runner_item_on(self, event: JsonlEvent, ts: datetime) -> None:
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
                new_hs = HostRunState(
                    hostname=hostname,
                    status=Status.RUNNING,
                    start_time=ts,
                )
                # R12: cap on first-time loop-item insertion. A task
                # looping over a 100k-item list otherwise grows the
                # host dict one entry per loop iter.
                if not _reserve_host_run_state(self, task, hostname, new_hs):
                    continue
                host = new_hs
                task.hosts[hostname] = host
            host.loop_items_done += 1

    def _task_dict(self, event: JsonlEvent) -> JsonlTask:
        """Extract the ``task`` field as a dict.

        ansible.posix.jsonl may emit ``task`` as a bare UUID string or
        ``None`` when the mitogen transport drops mid-task.  Return an
        empty dict in those cases so callers can safely call ``.get()``.
        """
        task = event.get("task")
        return task if isinstance(task, dict) else {}

    def _hosts_dict(self, event: JsonlEvent) -> dict[str, JsonlHostResult]:
        """Extract the ``hosts`` field as a dict.

        mitogen bulk-reconnect events can emit ``hosts`` as a list of
        hostnames instead of the canonical ``{hostname: result}`` dict.
        Return an empty dict so callers can safely call ``.items()`` or
        iterate without materialising bogus host entries.
        """
        hosts = event.get("hosts")
        return hosts if isinstance(hosts, dict) else {}

    @staticmethod
    def _prior_host_start_time(task: TaskRunState, hostname: str) -> datetime | None:
        """Carry the host's recorded start_time into a terminal HostRunState.

        Terminal handlers replace the host entry wholesale; without this
        the start recorded by v2_runner_on_start (or synthesised at
        task_start) is lost and per-host durations render as 0s.
        """
        prior = task.hosts.get(hostname)
        return prior.start_time if prior is not None else None

    def _handle_v2_runner_on_ok(self, event: JsonlEvent, ts: datetime) -> None:
        """Handle v2_runner_on_ok event."""
        hosts_data = self._hosts_dict(event)
        task = self._resolve_runner_task(event)
        if task is None:
            self._note_unmatched(event)
            return

        for hostname, host_result in hosts_data.items():
            changed = host_result.get("changed", False)
            new_hs = HostRunState(
                hostname=hostname,
                status=Status.CHANGED if changed else Status.OK,
                changed=changed,
                start_time=self._prior_host_start_time(task, hostname),
                end_time=ts,
            )
            # R12: enforce host caps only when the host entry is new.
            # A terminal event for a host we already track is just a
            # status update — no growth, no cap accounting.
            if _reserve_host_run_state(self, task, hostname, new_hs):
                task.hosts[hostname] = new_hs

        if not any(
            hs.status in (Status.RUNNING, Status.FAILED, Status.UNREACHABLE)
            for hs in task.hosts.values()
        ):
            task.status = Status.COMPLETED

    def _handle_v2_runner_on_failed(self, event: JsonlEvent, ts: datetime) -> None:
        """Handle v2_runner_on_failed event."""
        hosts_data = self._hosts_dict(event)
        task = self._resolve_runner_task(event)
        if task is None:
            self._note_unmatched(event)
            return

        for hostname, host_result in hosts_data.items():
            # Ansible passes ``ignore_errors`` as a parameter to the
            # ``v2_runner_on_failed`` callback; the aom_jsonl callback emits it
            # at the top level of the host result. Older/synthetic payloads
            # nested it under ``_ansible_verbose_always`` — honour both.
            ignore_errors = bool(host_result.get("ignore_errors", False))
            if not ignore_errors:
                verbose_always = host_result.get("_ansible_verbose_always", {})
                if isinstance(verbose_always, dict):
                    ignore_errors = bool(verbose_always.get("ignore_errors", False))

            msg = host_result.get("msg", "")

            if ignore_errors:
                new_hs = HostRunState(
                    hostname=hostname,
                    status=Status.OK,
                    changed=False,
                    message=msg,
                    start_time=self._prior_host_start_time(task, hostname),
                    end_time=ts,
                )
            else:
                new_hs = HostRunState(
                    hostname=hostname,
                    status=Status.FAILED,
                    changed=False,
                    message=msg,
                    start_time=self._prior_host_start_time(task, hostname),
                    end_time=ts,
                )
                self.status = Status.FAILED

            # R12: cap accounting skipped for already-tracked hosts;
            # see _handle_v2_runner_on_ok for the rationale.
            if _reserve_host_run_state(self, task, hostname, new_hs):
                task.hosts[hostname] = new_hs

        if not any(
            hs.status in (Status.RUNNING, Status.FAILED, Status.UNREACHABLE)
            for hs in task.hosts.values()
        ):
            task.status = Status.COMPLETED

    def _handle_v2_runner_on_skipped(self, event: JsonlEvent, ts: datetime) -> None:
        """Handle v2_runner_on_skipped event."""
        hosts_data = self._hosts_dict(event)
        task = self._resolve_runner_task(event)
        if task is None:
            self._note_unmatched(event)
            return

        for hostname in hosts_data:
            new_hs = HostRunState(
                hostname=hostname,
                status=Status.SKIPPED,
                start_time=self._prior_host_start_time(task, hostname),
                end_time=ts,
            )
            if _reserve_host_run_state(self, task, hostname, new_hs):
                task.hosts[hostname] = new_hs

        if not any(
            hs.status in (Status.RUNNING, Status.FAILED, Status.UNREACHABLE)
            for hs in task.hosts.values()
        ):
            task.status = Status.COMPLETED

    def _handle_v2_runner_on_unreachable(self, event: JsonlEvent, ts: datetime) -> None:
        """Handle v2_runner_on_unreachable event."""
        hosts_data = self._hosts_dict(event)
        task = self._resolve_runner_task(event)
        if task is None:
            self._note_unmatched(event)
            return

        for hostname, host_result in hosts_data.items():
            msg = host_result.get("msg", "")
            new_hs = HostRunState(
                hostname=hostname,
                status=Status.UNREACHABLE,
                message=msg,
                start_time=self._prior_host_start_time(task, hostname),
                end_time=ts,
            )
            if _reserve_host_run_state(self, task, hostname, new_hs):
                task.hosts[hostname] = new_hs

        self.status = Status.FAILED

        if not any(
            hs.status in (Status.RUNNING, Status.FAILED, Status.UNREACHABLE)
            for hs in task.hosts.values()
        ):
            task.status = Status.COMPLETED

    def _handle_v2_playbook_on_stats(self, event: JsonlEvent, ts: datetime) -> None:
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
