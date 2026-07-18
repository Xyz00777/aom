"""Compact renderer — Rich Live lifecycle and per-event log emission.

Pure formatters live in :mod:`ansible_aom.compact.format`;
exit-code derivation lives in :mod:`ansible_aom.compact.exit_code`.
Both are re-exported here so historical
``from ansible_aom.compact.renderer import format_status_bar`` (etc.)
imports keep working. See ARCHITECTURE.md §7.3.

See SPECIFICATION.md Section 4.1 for compact view behaviour.

Note on ``print()``: the ``print()`` calls in
:meth:`CompactRenderer.handle_completion` (``_print_final_status`` block)
write user-facing completion output — snapshot tree, host recap, final
status, failure recap, unknown-events hint — that the test suite and the
golden snapshot ``tests/compact/golden/unknown_event_type__80x24.txt``
capture via ``capsys.readouterr().out``. Converting them to
``logger.*`` calls would route the output through the logging handler
configuration and silently break those assertions, so they stay as
``print()``. Structured logging is still available via ``logger`` below
for any future debug-only diagnostics.
"""

from __future__ import annotations

import logging
import shutil
import time
from typing import TYPE_CHECKING, cast

from ansible_aom.compact.display import Display
from ansible_aom.compact.exit_code import determine_exit_code  # noqa: F401 — re-export
from ansible_aom.compact.format import (
    _BOLD,  # noqa: F401 — re-export
    _CYAN,
    _DIM,
    _GREEN,
    _MAGENTA,
    _MSG_DISPLAY_CAP,  # noqa: F401 — re-export
    _ORANGE,
    _RED,
    _RESET,  # noqa: F401 — re-export
    _SGR_RE,  # noqa: F401 — re-export
    _YELLOW,
    _color_enabled,
    _compute_mode_label,
    _compute_tree_budget,
    _format_count_cells,  # noqa: F401 — re-export
    _strip_sgr,  # noqa: F401 — re-export
    _truncate_msg,
    _truncate_visible,  # noqa: F401 — re-export
    _verbose_ok_body,
    _wrap,
    collect_tags,  # noqa: F401 — re-export
    count_completed_tasks,
    count_total_tasks,
    count_total_tasks_seen,
    format_failure_recap,
    format_host_rows,
    format_host_summary,  # noqa: F401 — re-exported for test access
    format_preflight_summary,
    format_status_bar,
    format_tree_block,
)
from ansible_aom.compact.password import handle_password_prompt as do_handle_password_prompt
from ansible_aom.core import diagnostics
from ansible_aom.core._async_poll import is_async_poll_payload
from ansible_aom.core.duration import format_duration_decimal
from ansible_aom.core.estimate import (
    RunEstimate,
    RunProgress,
    add_completed,
    add_in_flight,
    project_remaining,
)
from ansible_aom.core.event_types import JsonlEvent, JsonlTask
from ansible_aom.core.heartbeat import HeartbeatTracker, LivenessState  # noqa: F401
from ansible_aom.core.icons import is_unicode_terminal
from ansible_aom.core.log_filter import (
    normalize_hide_states,
    should_hide_event,
    should_hide_host_result,
)
from ansible_aom.core.models import RunState, Status
from ansible_aom.core.tree import TreeProjection, run_state_status_counts
from ansible_aom.core.tree_projection import task_complete_on_all_targets

if TYPE_CHECKING:
    from ansible_aom.session.history import PriorRun

logger = logging.getLogger(__name__)

# Terminal per-host runner events: each may be the last target host to
# finish a task, triggering that task's completion check.
_TERMINAL_RUNNER_EVENTS = frozenset(
    {
        "v2_runner_on_ok",
        "v2_runner_on_failed",
        "v2_runner_on_unreachable",
        "v2_runner_on_skipped",
    }
)

# Host-death events. A death shrinks the play's live-target set, which
# can complete OTHER pending tasks the dead host was blocking — the one
# case that still needs a sweep over the whole pending list (rare, so
# the sweep cost is off the per-event hot path).
_DEATH_RUNNER_EVENTS = frozenset({"v2_runner_on_failed", "v2_runner_on_unreachable"})


class _BoundedSet(set):  # noqa: FURB189 — subclassing set is intentional
    """A ``set`` that drops itself when it exceeds a cap on insert.

    R14: the compact renderer carries several set-shaped dedupe
    containers that grow monotonically with the event stream. A
    pathological loop fan-out or warning storm can fill them past any
    reasonable cap in seconds. ``_BoundedSet`` enforces a soft ceiling:

    - When the cap is exceeded on ``add()``, the entire set is cleared.
      A clear is simpler than per-element FIFO eviction (which would
      require an ``OrderedDict`` or deque to track insertion order) and
      is correct for the renderer's use cases: the containers are
      dedupe helpers, so losing the older entries just means future
      repeats of those values are "seen" again, which the renderer
      handles gracefully (no crash, slightly louder output).
    - Membership tests (``in``) and iteration behave like a plain
      ``set``.

    The cap is fixed at construction time; nothing in the renderer
    mutates it post-init. Pick the cap based on the *upper bound on
    useful dedupe* for each container — anything beyond that is the
    runaway case the cap is meant to suppress.
    """

    __slots__ = ("_cap",)

    def __init__(self, cap: int) -> None:
        super().__init__()
        self._cap = cap

    def add(self, value: object) -> None:  # type: ignore[override]
        # Drop everything when we cross the cap *before* inserting the
        # new value. This keeps the post-cap set size bounded by
        # ``_cap`` (the cap means "remember at most this many recent
        # entries"; insert at cap + 1 resets to just the new entry).
        if len(self) >= self._cap:
            self.clear()
        super().add(value)


# R14: per-container cap values. Picked to be generous enough that no
# realistic run trips them, but small enough that a misbehaving host
# can't OOM the renderer.
_STREAMED_LOOP_ITEMS_CAP = 10_000
_ANNOUNCED_TASK_UUIDS_CAP = 10_000
_COMPLETED_TASK_IDS_CAP = 10_000
_SEEN_WARNING_MESSAGES_CAP = 5_000


# HS-1/HS-8: status-panel compute throttle. Aligned with Display.update's
# write throttle (0.25 s) so a compute whose output Display would
# coalesce is short-circuited entirely. The clean-tick refresh uses the
# same 0.25 s window so the spinner glyph (◐→◓→◑→◒) and elapsed-time
# segment animate at 4 FPS during quiet periods.
_PANEL_COMPUTE_THROTTLE_S = 0.25
_PANEL_TICK_REFRESH_S = 0.25
# Dirty-path coalesce window. When state changes keep arriving faster
# than ``_PANEL_COMPUTE_THROTTLE_S`` we still want to render *eventually*
# (the old gate skipped every call within the throttle window, which
# could starve the panel forever during a burst). This short window
# collapses truly simultaneous events (e.g. one task_start followed by
# five runner_on_ok within microseconds) without burning CPU, but lets
# the next render proceed as soon as the burst settles.
_PANEL_DIRTY_COALESCE_S = 0.05


def _extract_error_msg(result: dict) -> str:
    """Extract the most informative error string from a runner result.

    Ansible modules surface error details in different fields depending
    on the failure mode (``msg`` for normal exceptions, ``module_stderr``
    / ``stderr`` for shell command failures, ``module_stdout`` /
    ``stdout`` for raw output).  This helper walks the fields in priority
    order and returns the first one that has non-whitespace content,
    passed through :func:`_truncate_msg` so the result respects the
    display cap and surrogate normalisation.

    When ``_ansible_no_log`` is ``True`` and none of the standard error
    fields have content, returns the project's canonical redacted marker
    ``(no_log)`` so the user sees ``FAILED! => (no_log)`` instead of a
    bare ``FAILED!`` with no explanation.

    When ``_ansible_no_log`` is not set but a ``censored`` field exists
    (an edge case), falls back to the raw ``censored`` value.

    Returns an empty string when no field yields content, so callers
    can render ``FAILED!`` / ``UNREACHABLE!`` without a trailing ``=>``.
    """
    for key in ("msg", "module_stderr", "stderr", "module_stdout", "stdout"):
        value = result.get(key, "")
        if isinstance(value, str) and value.strip():
            return _truncate_msg(value)
    if result.get("_ansible_no_log") is True:
        return "(no_log)"
    censored = result.get("censored", "")
    if isinstance(censored, str) and censored.strip():
        return _truncate_msg(censored)
    return ""


def _first_line(value: str) -> str:
    """Return the first line from a possibly multiline string."""
    return value.splitlines()[0] if value else ""


class CompactRenderer:
    """ANSI-based compact renderer satisfying the Renderer Protocol.

    Implements the Renderer interface defined in ansible_aom.renderer.protocol.
    Uses Rich Live display for terminal output.

    Attributes:
        _display: The Display instance for Rich Live output.
        _state: Current RunState for tracking execution.
        _playbook: Current playbook path.
        _args: Playbook arguments.
        _start_time: Timestamp when rendering started.
    """

    def __init__(
        self,
        is_tty: bool = True,
        hide_states: list[str] | None = None,
        record: bool = False,
        capture_verbose: bool = False,
        show_failed_hint: bool = True,
        show_warnings: bool = True,
        show_deprecations: bool = True,
    ) -> None:
        """Initialize the compact renderer.

        Args:
            is_tty: Whether stdout is a TTY. Non-TTY mode disables ANSI
                cursor control and prints log lines as plain text.
            hide_states: List of host states to suppress from the live
                compact log (e.g. ``["ok", "skipped"]``). The status
                panel, event recording, and aom inspect are unaffected.
        """
        self._display = Display(is_tty=is_tty)
        valid, _unknown = normalize_hide_states(hide_states or [])
        self._hide_states: frozenset[str] = valid
        self._state: RunState | None = None
        self._playbook: str = ""
        self._args: list[str] = []
        self._start_time: float = 0.0
        self._recording = record
        self._capture_verbose = capture_verbose
        self._show_failed_hint = show_failed_hint
        self._show_warnings = show_warnings
        self._show_deprecations = show_deprecations
        self._warnings_count: int = 0
        self._deprecations_count: int = 0
        self._definitions: list = []
        self._seen_warning_messages: set[str] = _BoundedSet(_SEEN_WARNING_MESSAGES_CAP)
        self._ascii_mode: bool = not is_unicode_terminal()
        self._colorize: bool = _color_enabled(is_tty)
        self._heartbeat = HeartbeatTracker()
        # Per-task timing: start timestamp (seconds since epoch) and name
        # keyed by task UUID, so a task's post-task summary can be emitted
        # whenever it *completes on all target hosts* — which under a free
        # strategy may be long after later tasks have started.
        self._task_start_times: dict[str, float] = {}
        self._task_names: dict[str, str] = {}
        # Latest ``_timestamp`` seen (Unix seconds). Used as "now" for the
        # run-end forced summary flush so durations stay consistent with
        # the event-derived task start times (wall-clock time.time() would
        # be on a different scale under replay / synthetic fixtures).
        self._last_event_time: float | None = None
        # UUIDs of announced-but-not-yet-summarised tasks, in announce
        # order (dict for O(1) membership/removal; insertion-ordered).
        # A task is emitted the moment it completes (see
        # ``task_complete_on_all_targets``) and removed — so a summarised
        # task is never revisited and this stays bounded by the in-flight
        # task set, not run length.
        self._announced_order: dict[str, None] = {}
        # Memo of each play's dead-host set (play_id → hostnames), fed to
        # ``task_complete_on_all_targets`` so completion checks don't
        # rescan the whole play per call (the quadratic sweep behind the
        # free-strategy display freeze). Invalidated wholesale on any
        # event that can change a dead set: a death, a play (re)start, or
        # an ok/skipped result overwriting a formerly-dead host's entry
        # (retry recovery). All are rare; the memo is hot the rest of the
        # time.
        self._play_dead_cache: dict[str, set[str]] = {}
        # "The task whose header is currently on screen" — the most
        # recently announced UUID. Drives the ``[task: …]`` straggler
        # suffix (a result whose task differs from this reads as
        # mis-attributed) and the "don't pre-empt the current task's
        # own next-announce summary" guard in the terminal-event sweep.
        self._last_task_uuid: str | None = None
        # Pre-rendered chips like ``DRY RUN`` / ``DIFF`` shown in the
        # status bar's leftmost slot. Computed once in ``start()``
        # from the ansible_args; never changes during a run.
        self._mode_label: str = ""
        # Skipped-task collapsing: hold ``skipping: [host]`` lines for
        # the in-flight task and decide on flush whether to print them
        # individually (mixed-result task) or compress into a single
        # ``… N hosts skipped`` line (all-skipped task). Reset on each
        # task_start; flushed by the next task_start or stats.
        self._pending_skipped_hosts: list[str] = []
        self._current_task_had_nonskipped_result: bool = False
        # Hosts that produced a per-host result line carrying an inline
        # duration suffix, keyed by task UUID. Used by the post-task
        # summary to suppress its own duration when exactly one host
        # already displayed it on its result line — avoiding duplication
        # on single-host runs (and on run_once / delegated tasks in
        # multi-host runs). Keyed per task because a task's summary may
        # now be emitted well after a later task has started.
        self._task_inline_duration_hosts: dict[str, set[str]] = {}
        # ``(host, task_id)`` pairs for which we have already streamed
        # per-item loop lines from ``v2_runner_item_on_*`` events. The
        # aggregate ``v2_runner_on_ok``/``on_failed`` then suppresses its
        # own ``results[]`` expansion for these pairs so items aren't
        # rendered twice. Empty under the plain ``ansible.posix.jsonl``
        # fallback (no item events), where the aggregate expansion stays
        # the only source of per-item lines.
        self._streamed_loop_items: set[tuple[str, str]] = _BoundedSet(_STREAMED_LOOP_ITEMS_CAP)
        # Optional prior-run stats for the preflight "Last run" hint.
        # Must be set via :meth:`set_prior_run` BEFORE
        # :meth:`set_definitions` so the hint is included in the
        # one-shot startup summary.
        self._prior_run: "PriorRun | None" = None
        # Phase 4 (diagnostics): per-renderer activity counters published
        # via :py:meth:`collect_stats` at :py:meth:`stop`. Render bumps
        # land in :py:meth:`_render_status_panel`; log-write bumps in
        # :py:meth:`print_log`. Both increment unconditionally — the
        # cost is one int add and the post-mortem signal is worth it.
        self._render_calls: int = 0
        self._log_writes: int = 0
        # HS-3: cached TreeProjection. ``TreeProjection`` memoizes its
        # role-index per instance and now refreshes its own shape-aware
        # caches when the underlying RunState revision changes, so the
        # same instance can survive across renders and quiet gaps.
        self._projection: TreeProjection | None = None
        # HS-2: incremental task counters. The format-layer functions
        # ``count_completed_tasks`` / ``count_total_tasks_seen`` walked
        # the full state on every render — fine for handle_completion
        # but quadratic per event. The counters here are bumped in
        # ``update_state`` and read directly by the status bar.
        # ``_completed_task_ids`` guards against double-counting when a
        # terminal event arrives more than once for the same task
        # (e.g. host-by-host events under the free strategy).
        self._tasks_seen: int = 0
        self._tasks_completed: int = 0
        self._completed_task_ids: set[str] = _BoundedSet(_COMPLETED_TASK_IDS_CAP)
        # Live run-duration estimate. ``_estimate`` is the matching prior
        # run's result-segmented per-task wall profile (built in
        # ``set_prior_run``); ``_progress`` accumulates covered prior work as
        # tasks complete (bumped alongside ``_tasks_completed``, under the
        # same once-per-task guard). The status bar feeds these — plus
        # in-flight top-ups computed each render — through
        # ``project_remaining``. See :mod:`ansible_aom.core.estimate`.
        self._estimate: RunEstimate | None = None
        self._progress: RunProgress = RunProgress()
        # Currently-running tasks: ``task_id -> (task.path, start_wall)``,
        # where ``start_wall`` is ``time.time()`` at the task's first
        # announcement (same clock as the status-bar elapsed). Lets the ETA
        # credit a long in-flight task's progress against its prior
        # duration instead of letting it inflate the estimate. Entries are
        # popped when the task completes.
        self._running_task_starts: dict[str, tuple[str, float]] = {}
        # Tasks whose TASK [..] header has already been printed. Under
        # the free strategy ansible.posix.jsonl emits v2_runner_on_start
        # per host instead of one v2_playbook_on_task_start up front, so
        # the header is emitted from either event — whichever arrives
        # first. This set keeps us from printing it twice when both fire.
        self._announced_task_uuids: set[str] = _BoundedSet(_ANNOUNCED_TASK_UUIDS_CAP)
        # HS-1/HS-8: dirty-flag + compute throttle on the status panel.
        # The flag turns on when state changes; the panel computation
        # is throttled to the same 0.25 s window Display.update uses
        # to coalesce stdout writes — beyond that window the compute
        # output is invisible anyway. A 1 s "clock advance" threshold
        # lets the elapsed-time segment in the status bar keep ticking
        # during quiet periods without computing on every tick().
        self._panel_dirty: bool = False
        self._last_panel_compute_time: float = 0.0
        # HS-1/HS-8: monotonic timestamp of the most recent state change.
        # Tracked separately from ``_last_panel_compute_time`` so the
        # dirty-path gate can distinguish "last compute already saw the
        # latest state" from "last compute is stale — render now". Without
        # this split, a burst of state changes arriving faster than the
        # compute throttle could starve the panel indefinitely.
        self._last_state_change_monotonic: float = 0.0

    def start(self, playbook: str, args: list[str]) -> None:
        """Start rendering a playbook run.

        Initializes the RunState, starts the Rich Live display,
        and shows the initial status bar.

        Args:
            playbook: Path to the playbook file.
            args: Additional arguments passed to ansible-playbook.
        """
        self._playbook = playbook
        self._args = args
        self._start_time = time.time()
        self._mode_label = _compute_mode_label(
            args,
            self._colorize,
            recording=self._recording,
            capture_verbose=self._capture_verbose,
        )

        # Reset the incremental counters so a re-used renderer instance
        # (e.g. ``aom replay`` driving a fresh run on the same object)
        # starts at zero rather than carrying state over.
        self._tasks_seen = 0
        self._tasks_completed = 0
        self._completed_task_ids = _BoundedSet(_COMPLETED_TASK_IDS_CAP)
        self._announced_task_uuids = _BoundedSet(_ANNOUNCED_TASK_UUIDS_CAP)
        self._play_dead_cache = {}
        # ``_estimate`` is set by ``set_prior_run`` and not reset here, the
        # same way ``_prior_run`` isn't — only the per-run accumulators are.
        self._progress = RunProgress()
        self._running_task_starts = {}

        # Initialize RunState
        self._state = RunState(playbook=playbook)

        # Start the display
        self._display.start()

        # Show initial status bar
        status_bar = format_status_bar(
            playbook=playbook,
            hosts_completed=0,
            hosts_total=0,
            warnings=0,
            deprecations=0,
            elapsed_seconds=0.0,
            ascii_mode=self._ascii_mode,
            colorize=self._colorize,
            mode_label=self._mode_label,
        )
        self._display.update(status_bar)

    def set_prior_run(self, prior_run: "PriorRun | None") -> None:
        """Store the matching prior-run stats for the preflight summary.

        Must be called before :meth:`set_definitions` so the hint line
        is included in the one-shot startup summary. ``None`` means no
        matching prior run — the line is silently omitted.

        The prior run's mined ``loop_totals`` are also copied onto the
        RunState so the tree can render ``N/total`` loop progress live.
        """
        self._prior_run = prior_run
        if prior_run is not None and prior_run.prior_wall_total_s > 0:
            self._estimate = RunEstimate(
                task_wall_s=dict(prior_run.task_wall_s),
                variable_paths=prior_run.variable_paths,
                prior_wall_total_s=prior_run.prior_wall_total_s,
                prior_var_total_s=prior_run.prior_var_total_s,
            )
        else:
            self._estimate = None
        if self._state is not None:
            self._state.loop_totals = dict(prior_run.loop_totals) if prior_run else {}

    def set_definitions(self, definitions: list) -> None:
        """Store preflight definitions and emit the startup summary.

        Two effects:
        1. The status bar's host count switches from `0/0` to `0/N` from
           the next frame onwards, using the union of every play's
           resolved_hosts as the denominator.
        2. A one-shot startup summary (PLAY/host/task counts per play)
           is printed above the status panel, mirroring nom's preview.
        """
        self._definitions = list(definitions)

        summary = format_preflight_summary(self._definitions, prior_run=self._prior_run)
        if summary is not None:
            self._display.print_log(summary)

        if self._state is None:
            return
        # Mirror onto state so the state machine's task_start handler
        # can look up per-play resolved_hosts (used to synthesise the
        # per-host RUNNING entries under linear strategy, where the
        # JSONL callback does not emit v2_runner_on_start).
        self._state.definitions = list(self._definitions)
        # HS-1/HS-8: mark dirty so the next render computes against the
        # fresh definitions. Stamp the state-change clock so the
        # dirty-path throttle gate can recognise "stale compute" vs
        # "compute already saw this state".
        self._panel_dirty = True
        self._last_state_change_monotonic = time.monotonic()
        self._render_status_panel()

    def update_state(self, event: JsonlEvent) -> None:
        """Handle a new JSONL event.

        Processes the event to update RunState, then refreshes the display.

        Args:
            event: JSONL event dictionary from ansible.
        """
        if self._state is None:
            return

        et = self._event_time(event)
        if et is not None:
            self._last_event_time = et

        # Stream the event as a log line above the status panel BEFORE
        # mutating state — keeps the visual story "what happened, then
        # the panel reflects it". Throttling on the panel update means
        # the panel may visibly trail the logs, which matches nom.
        self._emit_event_log(event)

        # Update RunState with the event
        self._state.handle_event(event)

        # Keep the dead-host memo honest BEFORE any completion check. A
        # death or play (re)start changes dead sets outright; an ok/
        # skipped result for a host the memo believes dead means a FAILED
        # entry was overwritten (retry recovery) — the host is alive
        # again and must block completion of tasks it hasn't reached.
        event_name = event.get("_event")
        if event_name == "v2_playbook_on_play_start" or event_name in _DEATH_RUNNER_EVENTS:
            self._play_dead_cache.clear()
        elif event_name in _TERMINAL_RUNNER_EVENTS and self._play_dead_cache:
            event_hosts = self._hosts_dict(event)
            if any(h in dead for dead in self._play_dead_cache.values() for h in event_hosts):
                self._play_dead_cache.clear()

        # A terminal event may have been the last target host to finish an
        # earlier task (a free-strategy straggler completing a task whose
        # header scrolled off long ago). Detect completion AFTER
        # handle_event so the just-finished host is counted. A task can
        # only newly complete via one of its OWN terminal events, so the
        # check is scoped to the event's task — sweeping the whole pending
        # list per event is quadratic under a free strategy with straggler
        # hosts (the mid-run display freeze). The exceptions that DO need
        # the sweep: host deaths (shrink the live-target set for every
        # pending task) and events with no task id (can't be scoped). The
        # currently-on-screen task is left to be summarised at the next
        # task announcement, preserving the linear inter-task placement.
        if event_name in _TERMINAL_RUNNER_EVENTS:
            event_time = self._event_time(event)
            if event_time is not None:
                task_uuid = self._task_dict(event).get("id", "")
                if event_name in _DEATH_RUNNER_EVENTS or not task_uuid:
                    self._flush_ready_summaries(event_time, behind_only=True)
                elif task_uuid != self._last_task_uuid:
                    self._maybe_flush_completed(task_uuid, event_time)

        # HS-2: bump the incremental counters using the freshly-mutated
        # state. Done after ``handle_event`` so the task's hosts dict
        # reflects the event we just processed.
        self._bump_task_counters(event)

        # HS-1/HS-8: mark the panel as needing recompute. The actual
        # decision to compute is gated inside ``_render_status_panel``.
        self._panel_dirty = True
        # HS-1/HS-8: stamp the state-change clock so the dirty-path
        # gate can recognise "stale compute" vs "already rendered this
        # state".
        self._last_state_change_monotonic = time.monotonic()

        # Refresh the status panel with current state + elapsed time.
        self._render_status_panel()

    def _bump_task_counters(self, event: JsonlEvent) -> None:
        """Update ``_tasks_seen`` / ``_tasks_completed`` from a single event.

        Tracks the same ground truth as ``count_completed_tasks`` but at
        per-event cost — at most one task lookup plus an O(H) walk over
        that task's hosts. ``_completed_task_ids`` keeps the count
        idempotent across replayed or per-host-fanned-out events.
        """
        if self._state is None:
            return
        event_type = event.get("_event", "")
        if event_type == "v2_playbook_on_task_start":
            self._tasks_seen += 1
            self._record_running_start(event)
            # Under linear, RunState's task_start handler force-completes
            # the previous task in place (flipping its RUNNING hosts to
            # OK) when its terminal events were lost. That mutation emits
            # no v2_runner_on_* the per-event branch below could hook, so
            # reconcile here — same reasoning as the play-boundary case.
            # Cheap: already-counted tasks short-circuit on a set lookup.
            self._reconcile_completed_tasks()
            return
        if event_type == "v2_runner_on_start":
            # Free strategy announces tasks per-host here instead of via
            # task_start; record the first sighting so in-flight credit
            # works under both strategies.
            self._record_running_start(event)
            # The first runner_on_start of a play flips RunState's
            # strategy detection from linear to free and purges the
            # synthesised RUNNING host guesses — which can leave an
            # earlier task with only terminal hosts, i.e. newly
            # completed without any terminal event. Reconcile like the
            # boundary cases; already-counted tasks short-circuit on a
            # set lookup so the walk stays cheap per event.
            self._reconcile_completed_tasks()
            return
        if event_type in ("v2_playbook_on_play_start", "v2_playbook_on_stats"):
            # A new play (or the final stats event) is proof that every prior
            # play is done: RunState._finalize_play flips their lingering
            # RUNNING hosts to a terminal status *in place*, without emitting
            # any v2_runner_on_* the per-event branch below could hook.
            # ``ansible.builtin.pause`` is the canonical case — it yields no
            # v2_runner_on_ok at all. Reconcile every newly-terminal task so
            # _tasks_completed keeps matching the count_completed_tasks oracle
            # (HS-2). These boundary events are rare (once per play / once at
            # end), so the full walk is cheap beside the per-runner-event path.
            self._reconcile_completed_tasks()
            return
        if event_type not in (
            "v2_runner_on_ok",
            "v2_runner_on_failed",
            "v2_runner_on_skipped",
            "v2_runner_on_unreachable",
        ):
            return
        task_id = self._task_dict(event).get("id", "")
        if not task_id or task_id in self._completed_task_ids:
            return
        play_id = self._state._resolve_play_id(event)
        play = self._state.plays.get(play_id) if play_id else None
        if play is None:
            # Fallback: scan plays for the task. Free-strategy events
            # may carry no usable play_id at all; the lookup degrades
            # but stays O(P) rather than O(P×T).
            for candidate in self._state.plays.values():
                if task_id in candidate.tasks:
                    play = candidate
                    break
        if play is None:
            return
        task = play.tasks.get(task_id)
        if task is None or not task.hosts:
            return
        if all(hs.status != Status.RUNNING for hs in task.hosts.values()):
            path = self._task_dict(event).get("path", "") or (task.path or "")
            self._count_completed_task(task_id, path)

    def _reconcile_completed_tasks(self) -> None:
        """Count tasks finalised in RunState without a terminal runner event.

        ``RunState._finalize_play`` (fired at play-start and stats
        boundaries) flips a play's lingering RUNNING hosts to terminal in
        place, so a pause — or any action with no v2_runner_on_* result —
        never reaches the per-event branch in ``_bump_task_counters``. Walk
        every play once and count any task that is now terminal and not yet
        counted, mirroring ``count_completed_tasks`` exactly so the
        incremental counter cannot drift below the oracle (HS-2).
        """
        if self._state is None:
            return
        for play in self._state.plays.values():
            for task_id, task in play.tasks.items():
                if task_id in self._completed_task_ids or not task.hosts:
                    continue
                if all(hs.status != Status.RUNNING for hs in task.hosts.values()):
                    self._count_completed_task(task_id, task.path or "")

    def _count_completed_task(self, task_id: str, path: str) -> None:
        """Fold one finished task into the incremental progress counters.

        Idempotent via ``_completed_task_ids``. The task is no longer in
        flight, so its recorded start gives this run's actual wall (the
        work-pace numerator); fall back to the prior wall when no start was
        recorded — a finalised pause has none (neutral, pace ≈ 1). Keyed by
        task path, the only cross-run stable identity; an unmatched path
        contributes nothing.
        """
        self._completed_task_ids.add(task_id)
        self._tasks_completed += 1
        start = self._running_task_starts.pop(task_id, None)
        if self._estimate is not None:
            prior_wall = self._estimate.task_wall_s.get(path)
            actual_wall = (time.time() - start[1]) if start is not None else (prior_wall or 0.0)
            add_completed(self._estimate, self._progress, path, actual_wall)

    def _record_running_start(self, event: JsonlEvent) -> None:
        """Note when a task entered flight, for the live ETA's in-flight credit.

        Records ``task_id -> (task.path, wall_now)`` on the task's first
        announcement (task_start under linear, the first runner_on_start
        under free). Only tasks carrying both an id and a path are tracked
        — a path is needed to look up the prior duration to credit against —
        and only the first sighting wins so a per-host fan-out doesn't reset
        the clock.
        """
        task = self._task_dict(event)
        task_id = task.get("id")
        path = task.get("path")
        if not task_id or not path or task_id in self._running_task_starts:
            return
        self._running_task_starts[task_id] = (path, time.time())

    def tick(self) -> None:
        """Refresh the status panel without processing an event.

        The runner calls this during quiet periods (no PTY output for a
        timeout window) so the elapsed-time counter keeps moving even
        when ansible isn't emitting any events. Display throttling means
        rapid ticks coalesce; calling every 0.5s is fine.
        """
        if self._state is None:
            return
        # Backstop flush for log batching: the last lines of a burst sit
        # in Display's buffer until some frame carries them out. Events
        # and panel writes do that during activity; the quiet-period
        # tick covers the trailing edge.
        self._display.flush_logs()
        self._render_status_panel()

    def note_pty_bytes(self) -> None:
        self._heartbeat.note_bytes(time.monotonic())

    def note_subprocess_active(self, active: bool) -> None:
        self._heartbeat.note_cpu_sample(time.monotonic(), active)

    def _task_total_with_prior(self, base_total: int) -> tuple[int, bool]:
        """Fold the matching prior run's observed task count into the total.

        Preflight ``--list-tasks`` can't see dynamic ``include_tasks``, so
        ``base_total`` (preflight + what's been seen so far) under-counts a
        role-heavy playbook. A matching prior run *observed* the real total,
        so seed the denominator with it. Returns ``(total, estimated)``: the
        total is flagged as an estimate only for a *loose* prior match whose
        count still exceeds the live signal — a strict match is trusted as a
        plain number, and once real progress overtakes the estimate the live
        count wins and the flag drops.
        """
        prior = self._prior_run
        prior_total = prior.observed_task_count if prior else 0
        total = max(base_total, prior_total)
        estimated = prior is not None and not prior.exact_match and prior_total > base_total
        return total, estimated

    def _render_status_panel(self) -> None:
        """Compute and push the current panel (status bar + tree + hosts).

        Composes three regions into a single Display update:
        1. Status bar (existing — counts, elapsed, warnings, liveness).
        2. Tree block (Task 7) — visible only while a task is RUNNING.
        3. Per-host summary table (Task 6) — visible whenever the run
           targets more than one host.

        All three pieces are joined with newlines; Display tracks the
        resulting row count for cursor management.
        """
        if self._state is None:
            return

        # HS-1/HS-8: skip the heavy compute when its output would either
        # be coalesced away by Display.update (within the same 0.25 s
        # write window) or would just re-render the previous picture
        # (no state change, no meaningful clock advance).
        #
        # Dirty-path gating: the previous gate compared only against
        # ``_last_panel_compute_time`` and skipped every call within the
        # 0.25 s window. If state changes kept arriving faster than that,
        # the gate kept suppressing forever — the panel froze on stale
        # output. The fix tracks when the most recent state change
        # arrived (``_last_state_change_monotonic``) and uses the
        # comparison ``last_compute >= last_state_change`` to recognise
        # "we already rendered this state" vs "we owe the user a render".
        now = time.monotonic()
        last_compute = self._last_panel_compute_time
        if last_compute > 0.0:
            elapsed_since_compute = now - last_compute
            if self._panel_dirty:
                last_change = self._last_state_change_monotonic
                if last_compute >= last_change:
                    # Last compute already saw the latest state — safe
                    # to wait for the longer 1 s clock-advance refresh.
                    if elapsed_since_compute < _PANEL_TICK_REFRESH_S:
                        return
                else:
                    # Last compute is stale (state changed since).
                    # Coalesce only a very short burst window so
                    # simultaneous events don't fan out into multiple
                    # computes, but render as soon as the burst settles.
                    if elapsed_since_compute < _PANEL_DIRTY_COALESCE_S:
                        return
            else:
                if elapsed_since_compute < _PANEL_TICK_REFRESH_S:
                    return

        # Counted after the early-return so a state-less call (e.g. an
        # update_state that hit a renderer that already stopped) doesn't
        # inflate the metric.
        self._render_calls += 1

        # --- Region 1: status bar (existing logic) -------------------------
        # Per-host status: last terminal state wins. We skip RUNNING
        # entries because a host's HostRunState in the *current* task
        # is transiently RUNNING while previous tasks left it at OK —
        # without this guard the `X/Y hosts` count would oscillate
        # back to zero every time a new task started.
        host_statuses: dict[str, Status] = {}
        for play in self._state.plays.values():
            for task in play.tasks.values():
                for hostname, host_state in task.hosts.items():
                    if host_state.status == Status.RUNNING:
                        continue
                    host_statuses[hostname] = host_state.status

        # Prefer the preflight-resolved host count when JSONL hasn't yet
        # filled in any host states, so the user sees `0/N hosts` from
        # the first frame instead of `0/0 hosts`.
        preflight_hosts: set[str] = set()
        for play_def in self._definitions:
            preflight_hosts.update(play_def.resolved_hosts)
        hosts_total = max(len(host_statuses), len(preflight_hosts))

        hosts_completed = sum(
            1
            for s in host_statuses.values()
            if s in (Status.OK, Status.CHANGED, Status.SKIPPED, Status.COMPLETED)
        )

        now_wall = time.time()
        elapsed = now_wall - self._start_time
        remaining_seconds: float | None = None
        if self._estimate is not None:
            # Top up a copy of completed progress with tasks still in flight,
            # crediting each against its prior duration so a long-running task
            # burns the estimate down instead of inflating it. The copy keeps
            # in-flight work out of the warmup gate (which is on completed
            # work only).
            progress = self._progress.copy()
            for path, start in self._running_task_starts.values():
                add_in_flight(self._estimate, progress, path, now_wall - start)
            remaining_seconds = project_remaining(self._estimate, progress)
        base_total = max(count_total_tasks(self._definitions), self._tasks_seen)
        tasks_total, estimated_total = self._task_total_with_prior(base_total)
        status_bar = format_status_bar(
            playbook=self._playbook,
            hosts_completed=hosts_completed,
            hosts_total=hosts_total,
            warnings=self._warnings_count,
            deprecations=self._deprecations_count,
            elapsed_seconds=elapsed,
            remaining_seconds=remaining_seconds,
            tasks_completed=self._tasks_completed,
            tasks_total=tasks_total,
            estimated_total=estimated_total,
            ascii_mode=self._ascii_mode,
            colorize=self._colorize,
            mode_label=self._mode_label,
            liveness=self._heartbeat.state(time.monotonic()),
            task_counts=run_state_status_counts(self._state),
        )

        # --- Regions 2 & 3: tree + host rows -------------------------------
        # HS-3: reuse the cached projection between renders. The
        # projection refreshes its own revision-aware caches when the
        # underlying RunState shape changes.
        if self._projection is None or self._projection._state is not self._state:
            self._projection = TreeProjection.from_run_state(self._state)
        projection = self._projection
        cols, rows = shutil.get_terminal_size((80, 24))
        active_hosts = sum(1 for s in host_statuses.values() if s == Status.RUNNING)
        budget = _compute_tree_budget(rows, active_hosts)
        # Spinner frame derived from wall clock so the running glyph
        # actually animates between renders. 4 FPS matches the panel
        # refresh budget — anything faster would tear past the throttle.
        frame = int(now * 4)
        tree_lines = format_tree_block(
            projection,
            budget=budget,
            width=cols,
            ascii_mode=self._ascii_mode,
            colorize=self._colorize,
            animation_frame=frame,
        )
        host_lines: list[str] = []
        if projection.is_host_summary_visible():
            host_lines = format_host_rows(
                projection,
                width=cols,
                ascii_mode=self._ascii_mode,
                colorize=self._colorize,
                animation_frame=frame,
            )

        # Status bar is the BOTTOM line so it stays anchored where the
        # user's eye expects a status line. Tree + host rows render
        # above it (and grow upward into the log area as needed).
        parts: list[str] = []
        if tree_lines:
            parts.append("\n".join(tree_lines))
        if host_lines:
            parts.append("\n".join(host_lines))
        parts.append(status_bar)
        self._display.update("\n".join(parts))
        # HS-1/HS-8: record successful compute and clear the dirty flag
        # so the next call's gate evaluates against this timestamp.
        self._panel_dirty = False
        self._last_panel_compute_time = now

    def _render_status_bar(self) -> None:
        """Deprecated alias — kept for any test references that still call
        the old name. New code calls ``_render_status_panel``."""
        self._render_status_panel()

    def handle_interactive_prompt(self, prompt_text: str) -> str:
        """Surface a pause / vars_prompt-style prompt and capture one line.

        Mirrors ``handle_password_prompt`` but uses ``input()`` for an
        echoing read — pause and vars_prompt are not secrets. The Rich
        Live panel is stopped before the prompt prints so the user can
        actually see the captured prompt text; the panel restarts in a
        finally block so a crashing ``input()`` never leaves the
        terminal headless.

        Two non-obvious correctness details:

        1. The prompt is written to ``sys.stdout`` explicitly via
           ``write()+flush()`` rather than passed as ``input()``'s
           prompt argument. CPython's ``input(prompt)`` routes the
           prompt through ``readline`` when both stdin and stdout
           are TTYs, and readline emits the prompt on **stderr** —
           so a user running ``aom site.yml 2>file`` never sees the
           prompt. Writing to stdout directly bypasses that.
        2. ``KeyboardInterrupt`` propagates. The pause module
           advertises "Press Enter to continue or Ctrl+C to abort" —
           translating a Ctrl+C into a returned empty string
           (i.e. Enter) silently reversed the abort. Now Ctrl+C
           bubbles up to the runner's outer handler, which SIGINTs
           the child and exits 130.
        """
        import sys

        self._display.stop()
        try:
            sys.stdout.write(prompt_text)
            sys.stdout.flush()
            return input()
        except EOFError:
            # Ctrl+D / closed stdin — treat as "user pressed Enter"
            # so the playbook can proceed in non-interactive
            # environments. KeyboardInterrupt is intentionally NOT
            # caught here; see docstring.
            return ""
        finally:
            self._display.start()

    def handle_password_prompt(self, prompt_text: str) -> str:
        """Handle a password prompt.

        Stops the Rich Live display, delegates to the password module
        for terminal pass-through, then restarts the display.

        Args:
            prompt_text: The password prompt text from ansible.

        Returns:
            The password entered by user, or empty string on error/cancellation.
        """
        # Stop display before password prompt
        self._display.stop()

        try:
            # Delegate to password module for terminal pass-through
            password = do_handle_password_prompt(prompt_text)
            return password
        finally:
            # Restart display after password prompt
            self._display.start()

    def print_log(self, message: str) -> None:
        """Print a log line above the status panel.

        Thin pass-through to the Display. Used by the runner to surface
        preflight errors verbatim — these are too important to hide
        behind just a counter.
        """
        self._log_writes += 1
        self._display.print_log(message)
        # Sustained log storms can otherwise starve panel refreshes: the
        # display writes the log immediately, then this periodic repaint keeps
        # the tree/status panel moving on the same cadence as quiet ticks.
        if self._state is not None and self._display.is_tty and self._display.is_running:
            self._render_status_panel()

    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        """Add a warning or deprecation detected from PTY stream.

        Bumps the counter AND prints the message above the panel so the
        user can see what the warning is about — `⚠ 1` on its own is
        opaque. Repeated identical messages (e.g. the same deprecation
        firing per-host on a many-host run) are deduped to one print
        but still each contribute to the counter.

        Args:
            message: The warning message text.
            is_deprecation: True if this is a deprecation warning.
        """
        if is_deprecation:
            self._deprecations_count += 1
        else:
            self._warnings_count += 1

        if message in self._seen_warning_messages:
            return
        self._seen_warning_messages.add(message)

        if is_deprecation:
            if not self._show_deprecations:
                return
        elif not self._show_warnings:
            return

        # The parser keeps the raw `[WARNING]: ...` / `[DEPRECATION WARNING]: ...`
        # prefix on the message. Don't double it up.
        if message.startswith("["):
            text = message
        else:
            prefix = "DEPRECATION" if is_deprecation else "WARNING"
            text = f"[{prefix}] {message}"
        color = _ORANGE if is_deprecation else _YELLOW
        self._display.print_log(_wrap(text, color, self._colorize))

    def handle_completion(self, exit_code: int, state: str) -> None:
        """Handle playbook completion (success/failure/crash).

        Shows final status and stops the Live display.

        Args:
            exit_code: Exit code from ansible-playbook.
            state: Final state string ('completed', 'failed', 'crashed').
        """
        # Calculate final elapsed time
        elapsed = time.time() - self._start_time

        # Force-flush any task summaries not yet emitted. On a clean run
        # v2_playbook_on_stats already drained them (this is a no-op); on a
        # cancel/crash with no stats event, this is where the in-flight and
        # never-completed tasks finally get their summary line, before the
        # final recap and the panel teardown below. Use the last event
        # timestamp (not wall-clock) so the duration matches the
        # event-derived task start times.
        flush_now = self._last_event_time if self._last_event_time is not None else time.time()
        self._flush_ready_summaries(flush_now, force=True)

        # Calculate final statistics
        hosts_completed = 0
        hosts_total = 0

        if self._state is not None:
            # Skip RUNNING so a cancelled-mid-task run still counts the
            # host as "completed earlier tasks" — see _render_status_panel
            # for the rationale.
            host_statuses: dict[str, Status] = {}
            for play in self._state.plays.values():
                for task in play.tasks.values():
                    for hostname, host_state in task.hosts.items():
                        if host_state.status == Status.RUNNING:
                            continue
                        host_statuses[hostname] = host_state.status

            preflight_hosts: set[str] = set()
            for play_def in self._definitions:
                preflight_hosts.update(play_def.resolved_hosts)
            hosts_total = max(len(host_statuses), len(preflight_hosts))

            for status in host_statuses.values():
                if status in (Status.OK, Status.CHANGED, Status.SKIPPED, Status.COMPLETED):
                    hosts_completed += 1

        # Use the runtime-grown denominator here too — otherwise on
        # cancellation the count snaps back to the preflight-only total,
        # which can be smaller than the runtime-announced count
        # (dynamic include_tasks). User-reported `30/4 tasks` regression.
        base_total = (
            count_total_tasks_seen(self._definitions, self._state)
            if self._state
            else count_total_tasks(self._definitions)
        )
        tasks_total, estimated_total = self._task_total_with_prior(base_total)
        tasks_completed = count_completed_tasks(self._state) if self._state else 0

        # Format final status bar
        status_bar = format_status_bar(
            playbook=self._playbook,
            hosts_completed=hosts_completed,
            hosts_total=hosts_total,
            warnings=self._warnings_count,
            deprecations=self._deprecations_count,
            elapsed_seconds=elapsed,
            tasks_completed=tasks_completed,
            tasks_total=tasks_total,
            estimated_total=estimated_total,
            task_counts=run_state_status_counts(self._state) if self._state else None,
            ascii_mode=self._ascii_mode,
            colorize=self._colorize,
            mode_label=self._mode_label,
        )

        # Add final state indicator with a label so the user can
        # distinguish a clean exit (●) from a failure (✖ failed),
        # a user-initiated Ctrl+C (✖ cancelled, exit 130), or a
        # mid-run crash (✖ crashed). Without the label, every
        # non-zero exit looked identical and gave the user no clue
        # whether the playbook or AOM was to blame.
        if self._ascii_mode:
            icon = {"completed": "*", "failed": "X", "crashed": "X"}.get(state, "?")
        else:
            icon = {"completed": "●", "failed": "✖", "crashed": "✖"}.get(state, "?")

        if state == "completed":
            label = ""
            indicator_color = _GREEN
        elif state == "crashed" and exit_code == 130:
            label = " cancelled by user"
            indicator_color = _YELLOW
        elif state == "crashed" and exit_code == 127:
            label = " ansible-playbook not found"
            indicator_color = _RED
        elif state == "crashed":
            label = " crashed"
            indicator_color = _RED
        else:
            label = " failed"
            indicator_color = _RED

        indicator = _wrap(f"{icon}{label}", indicator_color, self._colorize)
        final_status = f"{status_bar} {indicator}"

        # Capture frozen host-table and (on failure) tree lines BEFORE
        # display.stop() wipes the live panel.
        snapshot_tree, snapshot_host = self._capture_panel_snapshot()

        # Last in-panel update — visible briefly during stop() in TTY mode,
        # a no-op in non-TTY. Throttling can swallow this; the print() below
        # is what guarantees the final state survives.
        self._display.update(final_status)

        # Wipe the panel and release the cursor.
        self._display.stop()

        # On failure, replay the tree + host table so the user can see what
        # was in flight at the moment of failure. On success the tree is
        # omitted — running-task spinners would be misleading when the run
        # is already complete.
        if exit_code != 0:
            for line in snapshot_tree:
                print(line)
        for line in snapshot_host:
            print(line)

        # Print the final summary OUTSIDE any DEC-2026 frame so the panel
        # clear above can't erase it. In TTY mode this lands at the cursor
        # position the panel used to occupy, leaving the user with the run
        # outcome as the last visible line. In non-TTY (pipes, CI) it's
        # the only output Display ever produces (PQ6).
        print(final_status)

        # On a non-clean exit, also list which (host, task) pairs failed.
        # The aggregate counts answer "did it work?"; the recap answers
        # "what do I need to look at?". Skipped on success — there's
        # nothing to list and the clutter would be misleading.
        if exit_code != 0 and self._state is not None:
            for line in format_failure_recap(self._state, colorize=self._colorize):
                print(f"  {line}")

        # R5: future-version-drift hint. If ansible-core (or a third-party
        # callback) emitted any _event values we don't handle, list them
        # so the user knows something was unhandled — easier than reading
        # logs after the fact when a run "completed but did the wrong thing".
        if self._state is not None and self._state.unknown_events:
            parts = ", ".join(
                f"{name}×{count}"
                for name, count in sorted(
                    self._state.unknown_events.items(),
                    key=lambda kv: (-kv[1], kv[0]),
                )
            )
            total = sum(self._state.unknown_events.values())
            print(f"  ({total} unknown events: {parts})")

        # Terminal runner events that matched no known task even after
        # the path/name fallback. Each one left host state stale until
        # the stats-time cleanup, so a non-zero count explains "the tree
        # lagged behind the log" without reading debug logs.
        if self._state is not None and self._state.unmatched_events:
            parts = ", ".join(
                f"{name}×{count}"
                for name, count in sorted(
                    self._state.unmatched_events.items(),
                    key=lambda kv: (-kv[1], kv[0]),
                )
            )
            total = sum(self._state.unmatched_events.values())
            print(f"  ({total} unmatched result events: {parts})")

        # R12: surface any memory-cap hits so the user knows the run
        # was clipped. Same one-line footer shape as the unknown-events
        # hint — easy to skim for "did the run finish normally?".
        if self._state is not None and self._state.truncated_events:
            parts = ", ".join(
                f"{name}={count}"
                for name, count in sorted(
                    self._state.truncated_events.items(),
                    key=lambda kv: (-kv[1], kv[0]),
                )
            )
            print(f"  (truncated: {parts})")

    def _capture_panel_snapshot(self) -> tuple[list[str], list[str]]:
        """Render the current tree and host overview as static lines.

        Returns a ``(tree_lines, host_lines)`` tuple. Callers print tree
        lines only on failure (stale running spinners are misleading on
        success) but always print host lines for the per-host breakdown.
        """
        if self._state is None:
            return [], []
        if self._projection is None or self._projection._state is not self._state:
            self._projection = TreeProjection.from_run_state(self._state)
        projection = self._projection
        cols, rows = shutil.get_terminal_size((80, 24))
        active_hosts = sum(
            1
            for play in self._state.plays.values()
            for task in play.tasks.values()
            for hs in task.hosts.values()
            if hs.status == Status.RUNNING
        )
        budget = _compute_tree_budget(rows, active_hosts)
        tree_lines = format_tree_block(
            projection,
            budget=budget,
            width=cols,
            ascii_mode=self._ascii_mode,
            colorize=self._colorize,
            animation_frame=0,
        )
        host_lines: list[str] = []
        if projection.is_host_summary_visible():
            host_lines = format_host_rows(
                projection,
                width=cols,
                ascii_mode=self._ascii_mode,
                colorize=self._colorize,
                animation_frame=0,
            )
        return tree_lines, host_lines

    def collect_stats(self) -> diagnostics.RendererStats:
        """Return an immutable snapshot of this renderer's activity counters.

        Called from :py:meth:`stop` and surfaced via
        :func:`diagnostics.get_last_renderer_stats` so phase 5
        (``diagnostics.json``) can fold the numbers into the run record
        without coupling the session layer to the renderer.
        """
        return diagnostics.RendererStats(
            render_calls=self._render_calls,
            log_writes=self._log_writes,
        )

    def stop(self) -> None:
        """Stop rendering and clean up resources.

        Restores terminal state, flushes output, and cleans up
        any running Rich Live display.
        """
        diagnostics.set_last_renderer_stats(self.collect_stats())
        self._display.stop()
        self._state = None

    def _maybe_emit_pause_seconds_hint(self, task: JsonlTask) -> None:
        """Surface a one-line hint when a pause-with-seconds task starts.

        ``ansible.builtin.pause`` with ``seconds:`` doesn't read stdin
        and emits no further output during the wait — without this
        hint, the task name appears and then the panel sits silent
        until the sleep finishes. We can't know the elapsed without
        wiring a per-task timer; just printing the requested duration
        is enough signal.
        """
        action = (task.get("action") or "").lower()
        # Accept "pause", "ansible.builtin.pause", and any FQCN variant.
        if not action.endswith("pause"):
            return
        seconds = task.get("args", {}).get("seconds")
        if seconds is None:
            return
        # Tolerate string serialisations — ansible sometimes wraps int args.
        try:
            seconds_num = int(float(str(seconds)))
        except TypeError, ValueError:
            return
        self._display.print_log(f"[pause] sleeping {seconds_num}s…")

    def _event_time(self, event: JsonlEvent) -> float | None:
        """Parse ``_timestamp`` from a JSONL event into a Unix float.

        Returns ``None`` when the timestamp is missing or malformed —
        callers fall back to wall-clock or skip timing for that event.
        """
        ts = event.get("_timestamp")
        if not ts:
            return None
        try:
            from ansible_aom.core.timestamp import parse_iso_timestamp

            return parse_iso_timestamp(ts).timestamp()
        except ValueError, TypeError, AttributeError:
            return None

    def _format_duration(self, seconds: float) -> str:
        """Compact human duration: ``0.4s`` / ``12.3s`` / ``1m23s`` / ``1h02m``.

        Thin wrapper around :func:`ansible_aom.core.duration.format_duration_decimal`
        — kept here so historical callers and tests that reach into the
        renderer keep working.
        """
        return format_duration_decimal(seconds)

    def _flush_ready_summaries(
        self, now: float, *, force: bool = False, behind_only: bool = False
    ) -> None:
        """Emit summaries for announced tasks that are now complete.

        Walks the pending (announced, not-yet-summarised) tasks in order
        and prints a summary for any that has finished on every target
        host (see ``task_complete_on_all_targets``). Completion is checked
        independently per task rather than stopping at the first incomplete
        one, so a task that never completes (all-host silent skip, or a
        cancelled run) does not block later, genuinely-complete tasks.

        A summarised task is dropped from ``_announced_order`` and its
        per-task bookkeeping discarded, so all of it stays bounded by the
        set of *in-flight* tasks rather than growing with the whole run
        (the R14 bounding guarantee — see ``_announced_task_uuids``).

        ``force`` emits every remaining task that produced a result,
        regardless of completion — used at stats / cancellation to drain
        the tail.

        ``behind_only`` skips the task whose header is currently on screen
        (the most recently announced UUID). The terminal-event sweep uses
        it so it never pre-empts a still-current task's summary: under the
        linear strategy that summary must land at the *next* task's
        announcement (with the announce timestamp), matching how ansible's
        profile_tasks callback attributes the inter-task gap.
        """
        if self._state is None:
            return
        emitted: list[str] = []
        for task_uuid in self._announced_order:
            if behind_only and task_uuid == self._last_task_uuid:
                continue
            if force:
                # Drain the tail at run end — but only tasks that actually
                # produced a result. A task still purely in-flight (or never
                # reached) at cancel has nothing to summarise; a bare
                # ``— 0.0s`` line would be noise.
                emit = self._task_has_terminal_result(task_uuid)
                # Time the summary to the task's last host result, not the
                # run-end moment — otherwise a partially-done task at cancel
                # reads as spanning to cancel-time (misleadingly long) when
                # its hosts actually finished much earlier.
                summary_now = self._task_last_result_time(task_uuid) or now
            else:
                emit = task_complete_on_all_targets(
                    self._state, task_uuid, dead_by_play=self._play_dead_cache
                )
                summary_now = now
            if emit:
                self._emit_task_summary(task_uuid, summary_now)
                self._discard_task_state(task_uuid)
                emitted.append(task_uuid)
        for task_uuid in emitted:
            del self._announced_order[task_uuid]

    def _maybe_flush_completed(self, task_uuid: str, now: float) -> None:
        """Emit ``task_uuid``'s summary if it just completed on all targets.

        The event-scoped fast path of ``_flush_ready_summaries``: called
        with the task a terminal event belongs to (or, at announce time,
        the task being displaced as "current"), so ordinary events pay one
        completion check instead of a sweep over every pending task.
        """
        if self._state is None or task_uuid not in self._announced_order:
            return
        if task_complete_on_all_targets(self._state, task_uuid, dead_by_play=self._play_dead_cache):
            self._emit_task_summary(task_uuid, now)
            self._discard_task_state(task_uuid)
            del self._announced_order[task_uuid]

    def _discard_task_state(self, task_uuid: str) -> None:
        """Drop a summarised task's per-task bookkeeping (keeps memory
        bounded by in-flight tasks, not total run length)."""
        self._task_start_times.pop(task_uuid, None)
        self._task_names.pop(task_uuid, None)
        self._task_inline_duration_hosts.pop(task_uuid, None)

    def _task_has_terminal_result(self, task_uuid: str) -> bool:
        """True when ``task_uuid`` has at least one non-RUNNING host result."""
        if self._state is None:
            return False
        for play in self._state.plays.values():
            task = play.tasks.get(task_uuid)
            if task is None:
                continue
            return any(hs.status != Status.RUNNING for hs in task.hosts.values())
        return False

    def _task_last_result_time(self, task_uuid: str) -> float | None:
        """Latest host ``end_time`` (Unix seconds) across the task's hosts.

        Used to time a force-flushed summary to when the task's hosts
        actually finished, rather than the run-end moment. Returns None
        when no host has a recorded end_time (caller falls back to now).
        """
        if self._state is None:
            return None
        for play in self._state.plays.values():
            task = play.tasks.get(task_uuid)
            if task is None:
                continue
            latest: float | None = None
            for hs in task.hosts.values():
                if hs.end_time is not None:
                    ts = hs.end_time.timestamp()
                    if latest is None or ts > latest:
                        latest = ts
            return latest
        return None

    def _emit_task_summary(self, task_uuid: str, now: float) -> None:
        """Print a one-line summary of ``task_uuid``. Format:

            [HH:MM:SS] <task name> — N.Ns (H:MM:SS)  (1 failed, 2 ok)

        The wall-clock prefix and ``N.Ns`` duration are measured to
        ``now`` — the moment the task actually completed (its last target
        host finished), or its last host-result time when force-flushed at
        run end. The parenthesized value is cumulative playbook elapsed
        time; the trailing status counts summarise how many hosts ended in each
        terminal state. ``--hide-state`` is honoured.
        """
        start = self._task_start_times.get(task_uuid)
        name = self._task_names.get(task_uuid)
        if start is None or name is None:
            return
        duration = now - start
        cum = now - self._start_time

        # Local-time timestamp keeps the format consistent with what
        # users see from ansible's profile_tasks callback.
        from datetime import datetime

        wall = datetime.fromtimestamp(now).strftime("%H:%M:%S")
        prefix = _wrap(f"[{wall}]", _DIM, self._colorize)
        cum_str = _wrap(f"({self._format_duration(cum)})", _DIM, self._colorize)

        summary_suffix = self._build_status_suffix(task_uuid)

        # Drop the per-task duration when exactly one host already
        # displayed it on its inline result line — keeping the cleaner
        # ``— (cum)`` shape for single-host runs and run_once tasks.
        if len(self._task_inline_duration_hosts.get(task_uuid, ())) == 1:
            line = f"{prefix} {name} — {cum_str}{summary_suffix}"
        else:
            duration_str = _wrap(self._format_duration(duration), _CYAN, self._colorize)
            line = f"{prefix} {name} — {duration_str} {cum_str}{summary_suffix}"
        self._display.print_log(line)

    def _build_status_suffix(self, task_uuid: str) -> str:
        """Build the trailing ``(N failed, M ok)`` status summary.

        Walks ``task_uuid``'s host states, tallies per-status counts,
        respects ``--hide-state``, and returns a coloured string like
        ``"  (1 failed, 2 ok)"`` or an empty string when no counts are
        available or all are hidden.
        """
        if self._state is None:
            return ""
        task = None
        for play in self._state.plays.values():
            if task_uuid in play.tasks:
                task = play.tasks[task_uuid]
                break
        if task is None:
            return ""

        # OK+changed → CHANGED (same rule as tree projection).
        counts: dict[Status, int] = {}
        for hs in task.hosts.values():
            effective = Status.CHANGED if hs.status == Status.OK and hs.changed else hs.status
            if effective in (
                Status.FAILED,
                Status.UNREACHABLE,
                Status.CHANGED,
                Status.OK,
                Status.SKIPPED,
            ):
                counts[effective] = counts.get(effective, 0) + 1

        has_errors = any(counts.get(s, 0) > 0 for s in (Status.FAILED, Status.UNREACHABLE))
        # (Status, display label, ANSI colour, always_show)
        # FAILED/UNREACHABLE always appear even with --hide-state.
        # fmt: off
        entries: list[tuple[Status, str, str, bool]] = [
            (Status.FAILED,      "failed",      _RED,     True),
            (Status.UNREACHABLE, "unreachable", _MAGENTA, True),
            (Status.CHANGED,     "changed",     _YELLOW,  False),
            (Status.OK,          "ok",          _GREEN,   False),
            (Status.SKIPPED,     "skipped",     _CYAN,    False),
        ]
        # fmt: on
        parts: list[str] = []
        for status, label, colour, always_show in entries:
            n = counts.get(status, 0)
            if n == 0:
                continue
            if not always_show and status.value in self._hide_states:
                continue
            if has_errors and status not in (Status.FAILED, Status.UNREACHABLE):
                colour = _DIM
            parts.append(f"{n} {_wrap(label, colour, self._colorize)}")

        if not parts:
            return ""
        return f"  ({', '.join(parts)})"

    def _flush_pending_skips(self, *, force_individual: bool) -> None:
        """Drain the per-task skipped-host buffer.

        ``force_individual=True`` is the mixed-task case: a non-skipped
        result arrived for the same task, so the user expects the
        per-host detail. Print each skipped host as the original
        ``skipping: [host]`` line (cyan, like ansible's default
        callback).

        ``force_individual=False`` is the all-skipped case: the task
        finished without any other result type. Collapse into a
        single ``… N host(s) skipped`` line. For ≤3 hosts the names
        are inlined for context; beyond that just the count.
        """
        if not self._pending_skipped_hosts:
            return
        hosts = self._pending_skipped_hosts
        self._pending_skipped_hosts = []
        if force_individual:
            for host in hosts:
                self._display.print_log(_wrap(f"skipping: [{host}]", _CYAN, self._colorize))
            return
        count = len(hosts)
        plural = "" if count == 1 else "s"
        if count <= 3:
            host_list = ", ".join(hosts)
            line = f"… {count} host{plural} skipped: {host_list}"
        else:
            line = f"… {count} hosts skipped"
        # Compressed line: cyan to match the per-host colour but
        # leading with ``…`` so the user can tell at a glance it's an
        # aggregate, not an individual host record.
        self._display.print_log(_wrap(line, _CYAN, self._colorize))

    def _enter_terminal_event(self, event_name: str) -> bool:
        """Bookkeeping for a non-skipped terminal result event.

        Flushes any buffered skipping lines (force_individual=True
        because a non-skipped result just arrived — mixed-result task
        detail wins), marks the current task as having produced a real
        result (so the per-task summary treats it as non-skipped),
        and checks whether the event should be hidden per
        ``--hide-state``.

        Returns:
            ``True`` if the caller should ``return`` immediately
            (event suppressed); ``False`` to proceed with normal
            rendering.
        """
        self._flush_pending_skips(force_individual=True)
        self._current_task_had_nonskipped_result = True
        return should_hide_event(event_name, self._hide_states)

    def _announce_task(
        self,
        *,
        task_uuid: str,
        task_name: str,
        event_time: float | None,
        task_meta: JsonlTask,
    ) -> None:
        """Emit the TASK [..] header and reset per-task bookkeeping.

        Called from either ``v2_playbook_on_task_start`` (linear
        strategy) or the first ``v2_runner_on_start`` for a task
        (free strategy). Idempotent on ``task_uuid``.
        """
        if task_uuid and task_uuid in self._announced_task_uuids:
            return
        # First: dispose of any skipped-host buffer left over from the
        # previous task. If that task only ever produced skipped
        # results, collapse them; otherwise (the buffer would have been
        # drained by an earlier non-skipped result), this is a no-op.
        self._flush_pending_skips(force_individual=self._current_task_had_nonskipped_result)
        # Reset per-task state for the task we're about to print.
        self._current_task_had_nonskipped_result = False
        # If the task being displaced as "current" is complete, its
        # summary lands BEFORE this new TASK header (under linear
        # strategy that's the task that just finished, attached to its
        # own output). It is the only task the terminal-event checks can
        # have deferred: every other pending task was checked the moment
        # its own last host reported (``behind_only`` skips only the
        # current one), so no sweep is needed here.
        if event_time is not None and self._last_task_uuid is not None:
            self._maybe_flush_completed(self._last_task_uuid, event_time)
        self._display.print_log(f"\nTASK [{task_name}] " + "*" * 50)
        self._maybe_emit_pause_seconds_hint(task_meta)
        # Stash timing/name and register the task in announce order so its
        # summary can be emitted whenever it completes.
        if event_time is not None:
            self._task_start_times[task_uuid] = event_time
            self._task_names[task_uuid] = task_name
            self._last_task_uuid = task_uuid
        if task_uuid:
            self._announced_task_uuids.add(task_uuid)
            self._announced_order[task_uuid] = None

    def _task_dict(self, event: JsonlEvent) -> JsonlTask:
        """Extract the ``task`` field as a dict.

        ansible.posix.jsonl may emit ``task`` as a bare UUID string or
        ``None`` when the mitogen transport drops mid-task.  Return an
        empty dict in those cases so callers can safely call ``.get()``.
        """
        task = event.get("task")
        return cast(JsonlTask, task) if isinstance(task, dict) else cast(JsonlTask, {})

    def _hosts_dict(self, event: JsonlEvent) -> dict:
        """Extract the ``hosts`` field as a dict.

        mitogen bulk-reconnect events can emit ``hosts`` as a list of
        hostnames instead of the canonical ``{hostname: result}`` dict.
        Return an empty dict so callers can safely call ``.items()`` or
        iterate without materialising bogus host entries.
        """
        hosts = event.get("hosts")
        return hosts if isinstance(hosts, dict) else {}

    def _emit_event_log(self, event: JsonlEvent) -> None:
        """Print one nom-style log line for a JSONL event.

        Stats events are intentionally silent — the live panel and the
        final-summary print already cover what they would say. Unknown
        event types are silent too: the panel still updates from state,
        we just don't add to the log noise.

        Coloring matches ansible's stock default callback so users
        switching from raw ``ansible-playbook`` see the same per-task
        cues — ok green, changed yellow, fatal red, unreachable
        magenta, skipping cyan. (We synthesize these lines from JSONL
        events; ansible's normal callback isn't running because AOM
        forces the ``ansible.posix.jsonl`` callback for structured
        output — hence why ansible itself isn't producing them.)

        Per-host result lines also carry an inline duration in
        parentheses (e.g. ``ok: [web1] (2.3s)``), computed as the
        gap between the event's ``_timestamp`` and the parent task's
        recorded start time. On the *next* task_start, a summary
        line for the previous task lands first so the user sees how
        long it took with a wall-clock timestamp.
        """
        name = event.get("_event")
        event_time = self._event_time(event)
        if name == "v2_playbook_on_play_start":
            play_name = event.get("play", {}).get("name", "") or "(unnamed)"
            self._display.print_log(f"\nPLAY [{play_name}] " + "*" * 50)
        elif name == "v2_playbook_on_task_start":
            task = self._task_dict(event)
            self._announce_task(
                task_uuid=task.get("id", ""),
                task_name=task.get("name", "") or "(unnamed)",
                event_time=event_time,
                task_meta=task,
            )
        elif name == "v2_runner_on_start":
            # Free strategy: no v2_playbook_on_task_start before runner
            # events. Use the first runner_start per task as the
            # fallback signal for the TASK header so the streaming log
            # is still anchored to a task name.
            task = self._task_dict(event)
            task_uuid = task.get("id", "")
            if task_uuid and task_uuid not in self._announced_task_uuids:
                self._announce_task(
                    task_uuid=task_uuid,
                    task_name=task.get("name", "") or "(unnamed)",
                    event_time=event_time,
                    task_meta=task,
                )
        elif name == "v2_runner_on_ok":
            # Flush skips and flag task as having a real result, but do NOT
            # early-return on the event-level hide check. The ok/changed
            # distinction is per-host (result.changed), so we filter inside
            # the host loop instead.
            self._flush_pending_skips(force_individual=True)
            self._current_task_had_nonskipped_result = True
            suffix = self._inline_duration_suffix(event, event_time)
            stale = self._stale_task_suffix(event)
            task_id = self._task_dict(event).get("id", "")
            lines: list[str] = []
            for host, result in self._hosts_dict(event).items():
                # Items already streamed live from v2_runner_item_on_* —
                # the aggregate adds nothing per-item, so skip it entirely.
                if (host, task_id) in self._streamed_loop_items:
                    continue
                # Per-host hide filter: ok vs changed is determined by
                # result.changed, not by the event type alone.
                if should_hide_host_result(result, name, self._hide_states):
                    continue
                # Looped task (plain jsonl fallback): expand the per-item
                # ``results`` array into one line per item (matching
                # ansible's default callback) instead of a single aggregate
                # host line — this array is the only source of per-item
                # detail when no item events streamed.
                item_lines = self._loop_item_lines(host, result)
                if item_lines:
                    lines.extend(item_lines)
                    continue
                if suffix:
                    self._task_inline_duration_hosts.setdefault(task_id, set()).add(host)
                changed = result.get("changed")
                label, color = ("changed", _YELLOW) if changed else ("ok", _GREEN)
                text = f"{label}: [{host}]{suffix}"
                # debug/assert results (``_ansible_verbose_always``) exist to
                # inform — surface their msg inline like ansible's default
                # callback, instead of dropping the body.
                body = _verbose_ok_body(result)
                if body is not None:
                    text += f" => {body}"
                lines.append(_wrap(text, color, self._colorize) + stale)
            if lines:
                self._display.print_log("\n".join(lines))
        elif name == "v2_runner_on_failed":
            if self._enter_terminal_event(name):
                return
            suffix = self._inline_duration_suffix(event, event_time)
            stale = self._stale_task_suffix(event)
            task_id = self._task_dict(event).get("id", "")
            lines = []
            for host, result in self._hosts_dict(event).items():
                # Items already streamed live (including the failed item) —
                # the aggregate fatal line would duplicate them, so skip.
                if (host, task_id) in self._streamed_loop_items:
                    continue
                # Looped task that failed (plain jsonl fallback): the
                # per-item lines (including the ``failed:`` item) replace
                # the aggregate ``fatal:`` line, matching ansible's default.
                item_lines = self._loop_item_lines(host, result)
                if item_lines:
                    lines.extend(item_lines)
                    continue
                if suffix:
                    self._task_inline_duration_hosts.setdefault(task_id, set()).add(host)
                prefix = f"fatal: [{host}]{suffix}: FAILED!"
                if self._show_failed_hint:
                    msg = _first_line(_extract_error_msg(result))
                    text = f"{prefix} => {msg}" if msg else prefix
                else:
                    text = prefix
                lines.append(
                    _wrap(
                        text,
                        _RED,
                        self._colorize,
                    )
                    + stale
                )
            if lines:
                self._display.print_log("\n".join(lines))
        elif name == "v2_runner_on_unreachable":
            if self._enter_terminal_event(name):
                return
            suffix = self._inline_duration_suffix(event, event_time)
            stale = self._stale_task_suffix(event)
            task_id = self._task_dict(event).get("id", "")
            lines = []
            for host, result in self._hosts_dict(event).items():
                if suffix:
                    self._task_inline_duration_hosts.setdefault(task_id, set()).add(host)
                prefix = f"fatal: [{host}]{suffix}: UNREACHABLE!"
                if self._show_failed_hint:
                    msg = _first_line(_extract_error_msg(result))
                    text = f"{prefix} => {msg}" if msg else prefix
                else:
                    text = prefix
                lines.append(
                    _wrap(
                        text,
                        _MAGENTA,
                        self._colorize,
                    )
                    + stale
                )
            if lines:
                self._display.print_log("\n".join(lines))
        elif name == "v2_runner_on_skipped":
            if should_hide_event(name, self._hide_states):
                return
            # Hold individual skipping lines until we know whether
            # they're worth printing one-by-one (mixed-result task)
            # or worth collapsing (all-skipped task). The flush
            # happens at task transition or stats.
            self._pending_skipped_hosts.extend(self._hosts_dict(event).keys())
        elif name in (
            "v2_runner_item_on_ok",
            "v2_runner_item_on_failed",
            "v2_runner_item_on_skipped",
        ):
            if name == "v2_runner_item_on_ok":
                # Per-host filter: ok vs changed is per-item, not per-event.
                # Still flush skips and flag the task if any non-skipped item
                # is visible (not hidden).
                self._flush_pending_skips(force_individual=True)
                self._current_task_had_nonskipped_result = True
                task_id = self._task_dict(event).get("id", "")
                streamed_lines: list[str] = []
                for host, raw in self._hosts_dict(event).items():
                    if not isinstance(raw, dict):
                        continue
                    if should_hide_host_result(raw, name, self._hide_states):
                        continue
                    # Suppress in-flight async-poll bookkeeping payloads
                    # (finished=False) — they are not real loop items and
                    # would render as noise. A real item event follows when
                    # the job finishes.
                    if is_async_poll_payload(raw) and not raw.get("finished", True):
                        continue
                    self._streamed_loop_items.add((host, task_id))
                    streamed_lines.append(self._format_loop_item_line(host, raw, name))
                if streamed_lines:
                    self._display.print_log("\n".join(streamed_lines))
            else:
                # v2_runner_item_on_failed and v2_runner_item_on_skipped have
                # unambiguous states — event-level hide is correct.
                if should_hide_event(name, self._hide_states):
                    if name != "v2_runner_item_on_skipped":
                        self._flush_pending_skips(force_individual=True)
                        self._current_task_had_nonskipped_result = True
                    return
                task_id = self._task_dict(event).get("id", "")
                streamed_lines_alt: list[str] = []
                for host, raw in self._hosts_dict(event).items():
                    if not isinstance(raw, dict):
                        continue
                    self._streamed_loop_items.add((host, task_id))
                    streamed_lines_alt.append(self._format_loop_item_line(host, raw, name))
                if streamed_lines_alt:
                    if name != "v2_runner_item_on_skipped":
                        self._flush_pending_skips(force_individual=True)
                        self._current_task_had_nonskipped_result = True
                    self._display.print_log("\n".join(streamed_lines_alt))
        elif name == "v2_playbook_on_stats":
            # Drain the final task's skipped buffer with the same
            # mixed-vs-all-skipped rule we use at task transitions.
            self._flush_pending_skips(force_individual=self._current_task_had_nonskipped_result)
            self._current_task_had_nonskipped_result = False
            # Run is over: force-flush every still-un-summarised task,
            # complete or not (the final task, plus any task left
            # incomplete because a host never reached it). Counts reflect
            # whatever each task actually recorded.
            if event_time is not None:
                self._flush_ready_summaries(event_time, force=True)
                # Clear so a subsequent run doesn't see a stale last task.
                self._last_task_uuid = None

    def _loop_item_lines(self, host: str, result: dict) -> list[str]:
        """Expand a looped task's per-host ``results`` array into log lines.

        Returns one line per loop item — ``ok``/``changed``/``failed``/
        ``skipping`` with an ``=> (item=<label>)`` suffix — coloured like
        ansible's default callback. Returns an empty list when ``result``
        has no loop (``results`` absent/empty), so callers fall back to the
        single aggregate host line.

        The item label mirrors ``core.inspect_model._make_loop_item``:
        ``_ansible_item_label`` when ansible computed one, else the raw
        ``item`` value. Per-item lines carry no inline duration (ansible
        doesn't time individual items either); the per-task summary line
        still reports the loop's total wall time.
        """
        results = result.get("results")
        if not isinstance(results, list) or not results:
            return []
        return [self._format_loop_item_line(host, raw) for raw in results if isinstance(raw, dict)]

    def _format_loop_item_line(self, host: str, raw: dict, event_type: str | None = None) -> str:
        """Format one loop item's result as a coloured log line.

        Returns ``ok``/``changed``/``failed``/``skipping: [host] =>
        (item=<label>)`` coloured like ansible's default callback. Shared
        by the end-of-loop aggregate expansion (:meth:`_loop_item_lines`)
        and the live ``v2_runner_item_on_*`` streaming path so both render
        identically. The label mirrors ``core.inspect_model._make_loop_item``:
        ``_ansible_item_label`` when ansible computed one, else ``item``.

        ``event_type`` is the JSONL event name (e.g.
        ``v2_runner_item_on_failed``).  When supplied, it takes precedence
        over ``raw.get("failed")``/``raw.get("skipped")`` because the real
        ``aom_jsonl`` callback omits those flags on per-item payloads.
        The aggregate path (``_loop_item_lines``) passes ``event_type=None``
        since the aggregate ``results[]`` entries carry the flags correctly.

        Async-poll bookkeeping payloads (``ansible_job_id`` present, no
        ``_ansible_item_label``/``item``) are rendered with a recognisable
        ``(async, job_id=XXX)`` label instead of leaking the raw dict.
        """
        # Async-poll bookkeeping: ansible_job_id present, no item label.
        if is_async_poll_payload(raw):
            job_id = raw.get("ansible_job_id", "?")
            if event_type == "v2_runner_item_on_failed" or raw.get("failed"):
                msg = _extract_error_msg(raw)
                text = f"failed: [{host}] => (async, job_id={job_id})"
                if msg:
                    text += f" => {msg}"
                return _wrap(text, _RED, self._colorize)
            # In-flight async poll (finished=False) on v2_runner_item_on_ok
            # should be suppressed by the caller, but if it reaches here
            # render it as changed (the poll is still running).
            return _wrap(
                f"changed: [{host}] => (async, job_id={job_id})",
                _YELLOW,
                self._colorize,
            )
        label = str(raw.get("_ansible_item_label") or raw.get("item") or "")
        if event_type == "v2_runner_item_on_failed" or raw.get("failed"):
            msg = _extract_error_msg(raw)
            text = f"failed: [{host}] => (item={label})"
            if msg:
                text += f" => {msg}"
            return _wrap(text, _RED, self._colorize)
        if event_type == "v2_runner_item_on_skipped" or raw.get("skipped"):
            return _wrap(f"skipping: [{host}] => (item={label})", _CYAN, self._colorize)
        changed = raw.get("changed")
        label_word, color = ("changed", _YELLOW) if changed else ("ok", _GREEN)
        text = f"{label_word}: [{host}] => (item={label})"
        body = _verbose_ok_body(raw)
        if body is not None:
            text += f" => {body}"
        return _wrap(text, color, self._colorize)

    def _stale_task_suffix(self, event: JsonlEvent) -> str:
        """Return `` [task: <name>]`` when a result belongs to a task other
        than the most recently announced ``TASK [...]`` header.

        Log lines print in arrival order under the latest header; with
        throttle/free-strategy interleaving a straggler result for an
        earlier task lands under the newer header and reads as the wrong
        task's result. The suffix names the task the line really belongs
        to. Empty when the result matches the current header (the common
        case) or when no header has been announced yet.
        """
        task = self._task_dict(event)
        task_uuid = task.get("id", "")
        if not task_uuid or self._last_task_uuid is None or task_uuid == self._last_task_uuid:
            return ""
        name = task.get("name", "") or "different task"
        return " " + _wrap(f"[task: {name}]", _DIM, self._colorize)

    def _inline_duration_suffix(self, event: JsonlEvent, event_time: float | None) -> str:
        """Return `` (2.3s)`` for the per-host result line, or empty.

        Empty when timing data is unavailable (missing ``_timestamp``,
        no recorded task start) so the result line still renders.
        Skipped tasks are intentionally NOT timed inline — they
        haven't really run, the duration is meaningless.
        """
        if event_time is None:
            return ""
        task_id = self._task_dict(event).get("id", "")
        start = self._task_start_times.get(task_id)
        if start is None:
            return ""
        delta = event_time - start
        if delta < 0:
            return ""
        return f" ({self._format_duration(delta)})"
