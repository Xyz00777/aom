"""Compact renderer for AOM.

This module implements the ANSI-based compact view renderer.
See SPECIFICATION.md Section 4.1 for compact view details.
"""

from __future__ import annotations

import os
import re
import time

from ansible_aom.compact.display import Display
from ansible_aom.compact.password import handle_password_prompt as do_handle_password_prompt
from ansible_aom.core.heartbeat import HeartbeatTracker, LivenessState
from ansible_aom.core.icons import (
    STATUS_ICONS,
    STATUS_ICONS_ASCII,
    get_running_frame,
    is_unicode_terminal,
)
from ansible_aom.core.models import (
    PlayDefinition,
    RoleGroupDefinition,
    RunState,
    Status,
)
from ansible_aom.core.tree import TreeProjection


# =============================================================================
# ANSI color helpers
# =============================================================================
#
# Display writes raw bytes via ``sys.stdout.write``, so we embed SGR
# escape sequences directly rather than going through Rich's markup
# parser. Colors are gated on ``is_tty`` and the ``NO_COLOR`` env var
# (https://no-color.org) so non-TTY output (pipes, CI, redirected to
# file) and users who set NO_COLOR see plain ASCII.

_RESET = "\x1b[0m"
_DIM = "\x1b[2m"
_BOLD = "\x1b[1m"
_GREEN = "\x1b[32m"
_YELLOW = "\x1b[33m"
_RED = "\x1b[31m"
_MAGENTA = "\x1b[35m"
_CYAN = "\x1b[36m"


def _color_enabled(is_tty: bool) -> bool:
    """True if we should emit SGR codes — TTY only, NO_COLOR honored."""
    return is_tty and not os.environ.get("NO_COLOR")


def _wrap(text: str, code: str, colorize: bool) -> str:
    """``text`` wrapped in an SGR sequence, or plain ``text`` if not colorising."""
    if not colorize or not text:
        return text
    return f"{code}{text}{_RESET}"


_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_sgr(text: str) -> str:
    """Strip SGR escapes so visible-length comparisons are accurate."""
    return _SGR_RE.sub("", text)


def _truncate_visible(text: str, width: int, *, colorize: bool = False) -> str:
    """Truncate to `width` visible chars while preserving any open SGR
    state by appending RESET. SGR escapes are zero-width.

    `colorize=False` (the default) means the input string is plain ASCII
    with no SGR codes — in that mode the RESET is suppressed so the
    output stays pure ASCII (`NO_COLOR` / non-TTY contract).
    """
    if width <= 1:
        return text[:width]
    visible = 0
    out: list[str] = []
    i = 0
    while i < len(text) and visible < width - 1:
        if text[i] == "\x1b":
            j = text.find("m", i)
            if j == -1:
                break
            out.append(text[i:j + 1])
            i = j + 1
        else:
            out.append(text[i])
            visible += 1
            i += 1
    out.append("…")
    if colorize:
        out.append(_RESET)
    return "".join(out)


# R2: per-event ``msg`` cap for live-display lines. A task that does
# register-then-debug on a host returning multi-MB stdout would otherwise
# stall Rich's render thread; the full payload still lands in
# events.jsonl, so ``aom inspect show`` can dump the untruncated form.
_MSG_DISPLAY_CAP = 4096


def _truncate_msg(msg: str) -> str:
    """Cap a JSONL ``msg`` field for live display.

    The suffix includes the original byte length so the user knows how
    much was hidden — important for grep'ing the right session later.
    """
    if len(msg) <= _MSG_DISPLAY_CAP:
        return msg
    return f"{msg[:_MSG_DISPLAY_CAP]}…(truncated, {len(msg)} bytes)"


# ansible-playbook flags worth surfacing as a status-bar chip. Each
# entry pairs the flag aliases with the (label, colour) chip.
_MODE_FLAGS: tuple[tuple[frozenset[str], str, str], ...] = (
    (frozenset({"--check", "-C"}), "DRY RUN", _YELLOW),
    (frozenset({"--diff", "-D"}), "DIFF", _CYAN),
)


def _compute_mode_label(args: list[str], colorize: bool) -> str:
    """Render the status-bar mode chip(s) from ansible-playbook args.

    Multiple chips render space-joined (`DRY RUN DIFF`). Each chip is
    colour-wrapped only if ``colorize`` is True so non-TTY consumers
    still see the label without escape codes around it.

    The detection is conservative: only literal flag aliases (no
    ``--check=foo`` style suffixes — those don't exist for these
    flags in ansible-playbook) so a stray substring in some other
    arg can't trigger a false chip.
    """
    chips: list[str] = []
    args_set = set(args)
    for aliases, label, color in _MODE_FLAGS:
        if args_set & aliases:
            chips.append(_wrap(label, color, colorize))
    return " ".join(chips)


# =============================================================================
# Module-Level Formatting Functions
# =============================================================================


def format_status_bar(
    playbook: str,
    hosts_completed: int,
    hosts_total: int,
    warnings: int,
    deprecations: int,
    elapsed_seconds: float,
    tasks_completed: int = 0,
    tasks_total: int = 0,
    ascii_mode: bool = False,
    colorize: bool = False,
    mode_label: str = "",
    liveness: LivenessState | None = None,
) -> str:
    """Format the status bar for compact mode display.

    Args:
        playbook: Path to the playbook file.
        hosts_completed: Number of hosts that completed.
        hosts_total: Total number of hosts.
        warnings: Number of warnings encountered.
        deprecations: Number of deprecations encountered.
        elapsed_seconds: Elapsed time in seconds.
        tasks_completed: Tasks past PENDING/RUNNING. Suppressed when 0.
        tasks_total: Total tasks from preflight. Segment is omitted when 0
            (no preflight definitions, or only dynamic include_tasks).
        colorize: If True, segments are wrapped in SGR escape codes —
            playbook path dimmed, separators dimmed, completed
            host/task counters in green, warning glyph in yellow,
            deprecation glyph in magenta, elapsed dimmed. Off by
            default so the function stays pure-string and snapshot
            tests aren't disturbed.

    Returns:
        Formatted status bar string. Task segment included only when
        ``tasks_total > 0``::

            "playbook │ X/Y hosts │ A/B tasks │ ⚠ N ✱ N │ H:MM:SS"

    Example:
        >>> format_status_bar("site.yml", 3, 10, 2, 1, 323)
        'site.yml │ 3/10 hosts │ ⚠ 2 ✱ 1 │ 0:05:23'
    """
    elapsed_int = int(elapsed_seconds)
    elapsed_h = elapsed_int // 3600
    elapsed_m = (elapsed_int % 3600) // 60
    elapsed_s = elapsed_int % 60
    elapsed_str = f"{elapsed_h}:{elapsed_m:02d}:{elapsed_s:02d}"

    sep_glyph = "|" if ascii_mode else "│"
    warn_glyph = "!" if ascii_mode else "⚠"
    deprec_glyph = "*" if ascii_mode else "✱"

    # Counter colouring: green only when the run is in fact complete
    # (X==Y and at least one). Stays default otherwise to avoid
    # nagging the user with progress hues during a normal in-flight run.
    hosts_seg = f"{hosts_completed}/{hosts_total} hosts"
    if hosts_total > 0 and hosts_completed == hosts_total:
        hosts_seg = _wrap(hosts_seg, _GREEN, colorize)

    parts = []
    if mode_label:
        # Mode chip(s) sit before the playbook path so the user sees
        # them immediately even on a narrow terminal that truncates
        # later segments. The caller renders the chip with its own
        # colour (yellow for DRY RUN, cyan for DIFF) — we don't
        # re-style here so a no-colour run gets a plain ``DRY RUN``.
        parts.append(mode_label)
    parts.extend([_wrap(playbook, _DIM, colorize), hosts_seg])

    if tasks_total > 0:
        tasks_seg = f"{tasks_completed}/{tasks_total} tasks"
        if tasks_completed == tasks_total:
            tasks_seg = _wrap(tasks_seg, _GREEN, colorize)
        parts.append(tasks_seg)

    if warnings > 0:
        parts.append(_wrap(f"{warn_glyph} {warnings}", _YELLOW, colorize))
    if deprecations > 0:
        parts.append(_wrap(f"{deprec_glyph} {deprecations}", _MAGENTA, colorize))

    if liveness is not None:
        # Hug the preceding segment (no separator pipe) so it reads as
        # an annotation on it rather than a peer counter. ``parts`` is
        # never empty here — at minimum the hosts segment is present.
        live_glyph_unicode = {"live": "●", "working": "○", "stuck": "!"}
        live_glyph_ascii = {"live": "*", "working": "o", "stuck": "!"}
        live_color = {"live": _GREEN, "working": _DIM, "stuck": _RED}
        glyph = (live_glyph_ascii if ascii_mode else live_glyph_unicode)[liveness.level]
        live_seg = _wrap(f"{glyph} {liveness.age_s}s", live_color[liveness.level], colorize)
        # Annotate non-default reasons so the user can tell *why* the
        # dot is the colour it is. ``pty`` on LIVE and ``stuck`` on
        # STUCK are the expected default cases and stay un-annotated to
        # keep the bar terse; the interesting cases (CPU-promoted LIVE,
        # silent WORKING, CPU-rescued WORKING past stuck) are tagged.
        annotated_reasons = {("live", "cpu"), ("working", "silent"), ("working", "cpu")}
        if (liveness.level, liveness.reason) in annotated_reasons:
            reason_seg = _wrap(f"({liveness.reason})", _DIM, colorize)
            live_seg = f"{live_seg} {reason_seg}"
        parts[-1] = f"{parts[-1]} {live_seg}"

    parts.append(_wrap(elapsed_str, _DIM, colorize))

    sep = _wrap(sep_glyph, _DIM, colorize)
    return f" {sep} ".join(parts)


def _format_count_cells(
    ok: int,
    changed: int,
    failed: int,
    unreachable: int,
    *,
    ascii_mode: bool,
    colorize: bool,
) -> list[str]:
    """Render non-zero status count cells. Order: ok, changed, failed, unreachable.

    Returned as a list of styled segments so callers can space-join or
    place them inside other layouts. Existing `format_host_summary`
    behaviour is preserved by joining with a single space.
    """
    icons = STATUS_ICONS_ASCII if ascii_mode else STATUS_ICONS
    cells: list[str] = []
    if ok > 0:
        cells.append(_wrap(f"{icons[Status.OK]} {ok} ok", _GREEN, colorize))
    if changed > 0:
        cells.append(_wrap(f"{icons[Status.CHANGED]} {changed} changed", _YELLOW, colorize))
    if failed > 0:
        cells.append(_wrap(f"{icons[Status.FAILED]} {failed} failed", _RED, colorize))
    if unreachable > 0:
        cells.append(
            _wrap(
                f"{icons[Status.UNREACHABLE]} {unreachable} unreachable",
                _MAGENTA,
                colorize,
            )
        )
    return cells


def format_host_summary(
    hostname: str,
    ok: int,
    changed: int,
    failed: int,
    unreachable: int,
    ascii_mode: bool = False,
    colorize: bool = False,
) -> str:
    """Format a host summary line with status icons.

    Only includes non-zero counts in the output.

    Args:
        hostname: The hostname.
        ok: Number of OK tasks.
        changed: Number of changed tasks.
        failed: Number of failed tasks.
        unreachable: Number of unreachable tasks.
        ascii_mode: Use ASCII fallback glyphs (no Unicode).
        colorize: Wrap each status segment in its semantic SGR
            colour (ok=green, changed=yellow, failed=red,
            unreachable=magenta). Hostname is dimmed. Off by
            default to keep the function pure-string for tests.

    Returns:
        Formatted host summary with icons: "hostname: ● N ok, ◆ M changed, ..."

    Example:
        >>> format_host_summary("web1", 12, 3, 0, 0)
        'web1: ● 12 ok ◆ 3 changed'
    """
    cells = _format_count_cells(
        ok, changed, failed, unreachable,
        ascii_mode=ascii_mode, colorize=colorize,
    )
    return " ".join([_wrap(f"{hostname}:", _DIM, colorize), *cells])


# --- Worst-status → SGR colour mapping for the hostname cell ---------------
# Failed hosts go red; unreachable magenta; changed yellow. OK/SKIPPED/PENDING
# stay default-foreground (the count cells already carry their own colour).
_HOSTNAME_COLOR_BY_WORST: dict[Status, str] = {
    Status.FAILED: _RED,
    Status.UNREACHABLE: _MAGENTA,
    Status.CHANGED: _YELLOW,
}


def format_host_rows(
    projection: TreeProjection,
    *,
    width: int,
    ascii_mode: bool = False,
    colorize: bool = False,
) -> list[str]:
    """Render the per-host summary table.

    One line per host: hostname (worst-status coloured) + count cells +
    current-task suffix. Idle / unreachable / finished hosts get the
    appropriate suffix; the projection has already classified them.
    """
    out: list[str] = []
    for row in projection.host_rows():
        hostname_color = _HOSTNAME_COLOR_BY_WORST.get(row.worst_status or Status.OK)
        hostname_seg = (
            _wrap(row.hostname, hostname_color, colorize)
            if hostname_color else row.hostname
        )

        cells = _format_count_cells(
            ok=row.counts.get(Status.OK, 0),
            changed=row.counts.get(Status.CHANGED, 0),
            failed=row.counts.get(Status.FAILED, 0),
            unreachable=row.counts.get(Status.UNREACHABLE, 0),
            ascii_mode=ascii_mode, colorize=colorize,
        )

        # Current-task suffix.
        if row.worst_status == Status.UNREACHABLE and row.current_task is None:
            suffix = _wrap("unreachable", _MAGENTA, colorize)
        elif row.current_task is None:
            suffix = _wrap("(idle)", _DIM, colorize)
        else:
            elapsed = int(row.current_elapsed_s or 0)
            glyph = get_running_frame(0)  # static frame in the per-host row
            suffix = (
                f"on: {row.current_task}  "
                f"{_wrap(f'{glyph} {elapsed}s', _CYAN, colorize)}"
            )

        # Two spaces between count cells and the current-task suffix for visual
        # separation; `" ".join` over [hostname_seg, *cells] gives the single
        # spaces inside that group.
        left = " ".join([hostname_seg, *cells])
        line = f"{left}  {suffix}"
        if len(_strip_sgr(line)) > width:
            line = _truncate_visible(line, width, colorize=colorize)
        out.append(line)
    return out


def _count_tasks(play: PlayDefinition) -> int:
    """Count leaf TaskDefinitions in a play, expanding any RoleGroupDefinition."""
    total = 0
    for entry in play.tasks:
        if isinstance(entry, RoleGroupDefinition):
            total += len(entry.tasks)
        else:
            total += 1
    return total


def count_total_tasks(definitions: list[PlayDefinition]) -> int:
    """Sum of leaf tasks across all preflight play definitions.

    Used for the status bar's `X/Y tasks` segment. Returns 0 for an empty
    list, which the renderer treats as "no preflight data — suppress the
    segment". Dynamic ``include_tasks`` are not counted (they aren't
    expanded by ``--list-tasks``); ``import_tasks`` are.
    """
    return sum(_count_tasks(play) for play in definitions)


def count_completed_tasks(state: RunState) -> int:
    """Count tasks across all plays that have produced at least one host result.

    The state machine populates ``TaskRunState.hosts`` only when a
    ``v2_runner_on_*`` event fires (ok / failed / skipped / unreachable),
    so a task with a non-empty ``hosts`` dict has finished execution from
    the perspective of every host that reported. Tasks that have only
    been *announced* (``v2_playbook_on_task_start``) but produced no
    results yet keep ``hosts`` empty and don't count — that's the
    in-flight state we want to exclude.

    For the status bar this is a monotonic, ansible-faithful progress
    signal: linear-strategy plays advance one task at a time, so the
    previous task's host results land before the next task starts.
    Multi-host free-strategy plays can briefly over-count by one, which
    is acceptable for a coarse indicator.
    """
    total = 0
    for play in state.plays.values():
        for task in play.tasks.values():
            if task.hosts:
                total += 1
    return total


def collect_tags(definitions: list[PlayDefinition]) -> list[str]:
    """Unique tags across every leaf TaskDefinition, alphabetically sorted.

    Used for the startup tag preview line. Expands ``RoleGroupDefinition``
    entries so tags inside role groups still surface.
    """
    seen: set[str] = set()
    for play in definitions:
        for entry in play.tasks:
            if isinstance(entry, RoleGroupDefinition):
                for task in entry.tasks:
                    seen.update(task.tags)
            else:
                seen.update(entry.tags)
    return sorted(seen)


def format_preflight_summary(definitions: list[PlayDefinition]) -> str | None:
    """Render a one-shot startup summary of plays/tasks/hosts from preflight.

    Printed once before any JSONL events flow, giving the user a sense
    of what's about to run — nom-style. Returns None for an empty list
    so the renderer can skip emitting it.

    Format::

        PLAY [Setup web servers] (webservers, 2 hosts, 3 tasks)
        PLAY [Setup database]    (dbservers, 1 host, 2 tasks)

    The bracketed name comes from the play's `name`. Host count uses
    `resolved_hosts` when populated; falls back to the raw `hosts`
    pattern when --list-hosts failed for that play.
    """
    if not definitions:
        return None

    lines: list[str] = []
    for play in definitions:
        host_count = len(play.resolved_hosts)
        task_count = _count_tasks(play)

        if host_count > 0:
            host_part = f"{play.hosts}, {host_count} host" + ("s" if host_count != 1 else "")
        else:
            host_part = play.hosts or "0 hosts"

        task_part = f"{task_count} task" + ("s" if task_count != 1 else "")

        lines.append(f"PLAY [{play.name}] ({host_part}, {task_part})")

    tags = collect_tags(definitions)
    if tags:
        lines.append(f"Tags: {', '.join(tags)}")

    return "\n".join(lines)


def format_failure_recap(state: RunState, colorize: bool = False) -> list[str]:
    """Build per-failure lines naming the host and task that went wrong.

    Returns one line per (host, task) pair that ended in FAILED or
    UNREACHABLE. Empty list when nothing failed — handle_completion uses
    that as a signal to suppress the recap section entirely.

    Format::

        FAILED: web2 — install nginx
        UNREACHABLE: db1 — gather facts

    With ``colorize=True``, the leading ``FAILED:`` / ``UNREACHABLE:``
    label is wrapped in the same colour the host summary uses for the
    matching count (red / magenta).
    """
    lines: list[str] = []
    for play in state.plays.values():
        for task in play.tasks.values():
            for hostname, host_state in task.hosts.items():
                if host_state.status == Status.FAILED:
                    label = _wrap("FAILED", _RED, colorize)
                    lines.append(f"{label}: {hostname} — {task.name}")
                elif host_state.status == Status.UNREACHABLE:
                    label = _wrap("UNREACHABLE", _MAGENTA, colorize)
                    lines.append(f"{label}: {hostname} — {task.name}")
    return lines


def determine_exit_code(state: RunState) -> int:
    """Determine exit code from RunState.

    Traverses the RunState to determine the appropriate exit code:
    - 0: All tasks completed OK, CHANGED, or SKIPPED
    - 1: Any task FAILED (takes precedence over UNREACHABLE)
    - 2: Any host UNREACHABLE (but not if any FAILED)

    Args:
        state: The RunState to analyze.

    Returns:
        Exit code (0, 1, or 2).

    Example:
        >>> state = RunState(playbook="test.yml")
        >>> determine_exit_code(state)
        0
    """
    # Check for FAILED first (takes precedence)
    for play in state.plays.values():
        for task in play.tasks.values():
            for host_state in task.hosts.values():
                if host_state.status == Status.FAILED:
                    return 1

    # Then check for UNREACHABLE
    for play in state.plays.values():
        for task in play.tasks.values():
            for host_state in task.hosts.values():
                if host_state.status == Status.UNREACHABLE:
                    return 2

    return 0


# =============================================================================
# CompactRenderer Implementation
# =============================================================================


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

    def __init__(self, is_tty: bool = True) -> None:
        """Initialize the compact renderer.

        Args:
            is_tty: Whether stdout is a TTY. Non-TTY mode disables ANSI
                cursor control and prints log lines as plain text.
        """
        self._display = Display(is_tty=is_tty)
        self._state: RunState | None = None
        self._playbook: str = ""
        self._args: list[str] = []
        self._start_time: float = 0.0
        self._warnings_count: int = 0
        self._deprecations_count: int = 0
        self._definitions: list = []
        self._seen_warning_messages: set[str] = set()
        self._ascii_mode: bool = not is_unicode_terminal()
        self._colorize: bool = _color_enabled(is_tty)
        self._heartbeat = HeartbeatTracker()
        # Per-task timing: start timestamp (seconds since epoch) keyed by
        # task UUID, plus a tiny single-entry cache of "the task we just
        # printed a TASK header for" so the inline result lines and the
        # post-task summary can quote the right duration.
        self._task_start_times: dict[str, float] = {}
        self._last_task_uuid: str | None = None
        self._last_task_name: str | None = None
        self._last_task_start_time: float | None = None
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
        self._mode_label = _compute_mode_label(args, self._colorize)

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

        summary = format_preflight_summary(self._definitions)
        if summary is not None:
            self._display.print_log(summary)

        if self._state is None:
            return
        self._render_status_bar()

    def update_state(self, event: dict) -> None:
        """Handle a new JSONL event.

        Processes the event to update RunState, then refreshes the display.

        Args:
            event: JSONL event dictionary from ansible.
        """
        if self._state is None:
            return

        # Stream the event as a log line above the status panel BEFORE
        # mutating state — keeps the visual story "what happened, then
        # the panel reflects it". Throttling on the panel update means
        # the panel may visibly trail the logs, which matches nom.
        self._emit_event_log(event)

        # Update RunState with the event
        self._state.handle_event(event)

        # Refresh the status panel with current state + elapsed time.
        self._render_status_bar()

    def tick(self) -> None:
        """Refresh the status panel without processing an event.

        The runner calls this during quiet periods (no PTY output for a
        timeout window) so the elapsed-time counter keeps moving even
        when ansible isn't emitting any events. Display throttling means
        rapid ticks coalesce; calling every 0.5s is fine.
        """
        if self._state is None:
            return
        self._render_status_bar()

    def note_pty_bytes(self) -> None:
        self._heartbeat.note_bytes(time.monotonic())

    def note_subprocess_active(self, active: bool) -> None:
        self._heartbeat.note_cpu_sample(time.monotonic(), active)

    def _render_status_bar(self) -> None:
        """Compute and push the current status bar to the display."""
        if self._state is None:
            return

        host_statuses: dict[str, Status] = {}
        for play in self._state.plays.values():
            for task in play.tasks.values():
                for hostname, host_state in task.hosts.items():
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

        elapsed = time.time() - self._start_time
        status_bar = format_status_bar(
            playbook=self._playbook,
            hosts_completed=hosts_completed,
            hosts_total=hosts_total,
            warnings=self._warnings_count,
            deprecations=self._deprecations_count,
            elapsed_seconds=elapsed,
            tasks_completed=count_completed_tasks(self._state),
            tasks_total=count_total_tasks(self._definitions),
            ascii_mode=self._ascii_mode,
            colorize=self._colorize,
            mode_label=self._mode_label,
            liveness=self._heartbeat.state(time.monotonic()),
        )
        self._display.update(status_bar)

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
        self._display.print_log(message)

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
        # The parser keeps the raw `[WARNING]: ...` / `[DEPRECATION WARNING]: ...`
        # prefix on the message. Don't double it up.
        if message.startswith("["):
            self._display.print_log(message)
        else:
            prefix = "DEPRECATION" if is_deprecation else "WARNING"
            self._display.print_log(f"[{prefix}] {message}")

    def handle_completion(self, exit_code: int, state: str) -> None:
        """Handle playbook completion (success/failure/crash).

        Shows final status and stops the Live display.

        Args:
            exit_code: Exit code from ansible-playbook.
            state: Final state string ('completed', 'failed', 'crashed').
        """
        # Calculate final elapsed time
        elapsed = time.time() - self._start_time

        # Calculate final statistics
        hosts_completed = 0
        hosts_total = 0

        if self._state is not None:
            host_statuses: dict[str, Status] = {}
            for play in self._state.plays.values():
                for task in play.tasks.values():
                    for hostname, host_state in task.hosts.items():
                        host_statuses[hostname] = host_state.status

            preflight_hosts: set[str] = set()
            for play_def in self._definitions:
                preflight_hosts.update(play_def.resolved_hosts)
            hosts_total = max(len(host_statuses), len(preflight_hosts))

            for status in host_statuses.values():
                if status in (Status.OK, Status.CHANGED, Status.SKIPPED, Status.COMPLETED):
                    hosts_completed += 1

        tasks_total = count_total_tasks(self._definitions)
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

        # Last in-panel update — visible briefly during stop() in TTY mode,
        # a no-op in non-TTY. Throttling can swallow this; the print() below
        # is what guarantees the final state survives.
        self._display.update(final_status)

        # Wipe the panel and release the cursor.
        self._display.stop()

        # Print the final summary OUTSIDE any DEC-2026 frame so the panel
        # clear above can't erase it. In TTY mode this lands at the cursor
        # position the panel used to occupy, leaving the user with the run
        # outcome as the last visible line. In non-TTY (pipes, CI) it's
        # the only output Display ever produces (PQ6).
        print(final_status)

        # Per-host breakdown underneath. With one host this is barely
        # different from the aggregate, but with N hosts it's the only
        # way to see who succeeded vs who failed at a glance.
        for line in self._format_per_host_lines():
            print(f"  {line}")

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

    def _format_per_host_lines(self) -> list[str]:
        """Build one summary line per host, ordered by first-seen.

        Aggregates per-host status counts across every task in every
        play, then renders each host through `format_host_summary`.
        Returns an empty list when no hosts have any state — keeps the
        completion output clean in preflight-only-failure scenarios.
        """
        if self._state is None:
            return []

        host_counts: dict[str, dict[str, int]] = {}
        for play in self._state.plays.values():
            for task in play.tasks.values():
                for hostname, host_state in task.hosts.items():
                    counts = host_counts.setdefault(
                        hostname, {"ok": 0, "changed": 0, "failed": 0, "unreachable": 0}
                    )
                    if host_state.status == Status.OK:
                        counts["ok"] += 1
                    elif host_state.status == Status.CHANGED:
                        counts["changed"] += 1
                    elif host_state.status == Status.FAILED:
                        counts["failed"] += 1
                    elif host_state.status == Status.UNREACHABLE:
                        counts["unreachable"] += 1

        return [
            format_host_summary(
                hostname=hostname,
                ok=counts["ok"],
                changed=counts["changed"],
                failed=counts["failed"],
                unreachable=counts["unreachable"],
                ascii_mode=self._ascii_mode,
                colorize=self._colorize,
            )
            for hostname, counts in host_counts.items()
        ]

    def stop(self) -> None:
        """Stop rendering and clean up resources.

        Restores terminal state, flushes output, and cleans up
        any running Rich Live display.
        """
        self._display.stop()
        self._state = None

    def _maybe_emit_pause_seconds_hint(self, task: dict) -> None:
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

    def _event_time(self, event: dict) -> float | None:
        """Parse ``_timestamp`` from a JSONL event into a Unix float.

        Returns ``None`` when the timestamp is missing or malformed —
        callers fall back to wall-clock or skip timing for that event.
        """
        ts = event.get("_timestamp")
        if not ts:
            return None
        try:
            from datetime import datetime

            if ts.endswith("Z"):
                ts = ts[:-1] + "+00:00"
            return datetime.fromisoformat(ts).timestamp()
        except ValueError, TypeError, AttributeError:
            return None

    def _format_duration(self, seconds: float) -> str:
        """Compact human duration: ``0.4s`` / ``12.3s`` / ``1m23s`` / ``1h02m``."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        if seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes}m{int(seconds % 60):02d}s"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h{minutes:02d}m"

    def _emit_previous_task_summary(self, now: float) -> None:
        """Print a one-line summary of the task that just finished.

        Triggered right before the next task_start prints its TASK
        header so the user sees the duration of *the previous task*
        directly under that task's output. Format:

            [HH:MM:SS] <task name> — N.Ns (cum H:MM:SS)

        Where the timestamp is the wall-clock at the moment the new
        task started (which is also when the old task ended in
        linear strategy), ``N.Ns`` is the previous task's duration,
        and ``cum`` is the cumulative playbook elapsed time.

        Cumulative is dimmed so the per-task duration is the
        eye-catching figure; the timestamp prefix is dimmed for the
        same reason.
        """
        if self._last_task_start_time is None or self._last_task_name is None:
            return
        duration = now - self._last_task_start_time
        cum = now - self._start_time

        # Local-time timestamp keeps the format consistent with what
        # users see from ansible's profile_tasks callback.
        from datetime import datetime

        wall = datetime.fromtimestamp(now).strftime("%H:%M:%S")
        prefix = _wrap(f"[{wall}]", _DIM, self._colorize)
        cum_str = _wrap(f"(cum {self._format_duration(cum)})", _DIM, self._colorize)
        duration_str = _wrap(self._format_duration(duration), _CYAN, self._colorize)
        self._display.print_log(f"{prefix} {self._last_task_name} — {duration_str} {cum_str}")

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

    def _emit_event_log(self, event: dict) -> None:
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
            task = event.get("task", {})
            task_name = task.get("name", "") or "(unnamed)"
            task_uuid = task.get("id", "")
            # First: dispose of any skipped-host buffer left over from
            # the previous task. If that task only ever produced
            # skipped results, collapse them; otherwise (the buffer
            # would have been drained by an earlier non-skipped
            # result), this is a no-op.
            self._flush_pending_skips(force_individual=self._current_task_had_nonskipped_result)
            # Reset per-task state for the task we're about to print.
            self._current_task_had_nonskipped_result = False
            # Summary for the previous task lands BEFORE the new TASK
            # header — keeps it visually attached to its own output.
            if event_time is not None:
                self._emit_previous_task_summary(event_time)
            self._display.print_log(f"\nTASK [{task_name}] " + "*" * 50)
            self._maybe_emit_pause_seconds_hint(task)
            # Stash timing for the inline-duration logic below and for
            # the *next* summary line.
            if event_time is not None:
                self._task_start_times[task_uuid] = event_time
                self._last_task_uuid = task_uuid
                self._last_task_name = task_name
                self._last_task_start_time = event_time
        elif name == "v2_runner_on_ok":
            # A non-skipped result arrived: any buffered skipping lines
            # for this task should print individually (mixed-result
            # task — user wants the detail). Mark the task as having
            # produced a real result so the eventual flush at task
            # transition stays in individual-line mode.
            self._flush_pending_skips(force_individual=True)
            self._current_task_had_nonskipped_result = True
            suffix = self._inline_duration_suffix(event, event_time)
            for host, result in event.get("hosts", {}).items():
                if result.get("changed"):
                    self._display.print_log(
                        _wrap(f"changed: [{host}]{suffix}", _YELLOW, self._colorize)
                    )
                else:
                    self._display.print_log(_wrap(f"ok: [{host}]{suffix}", _GREEN, self._colorize))
        elif name == "v2_runner_on_failed":
            self._flush_pending_skips(force_individual=True)
            self._current_task_had_nonskipped_result = True
            suffix = self._inline_duration_suffix(event, event_time)
            for host, result in event.get("hosts", {}).items():
                msg = _truncate_msg(result.get("msg", "") or "")
                self._display.print_log(
                    _wrap(
                        f"fatal: [{host}]{suffix}: FAILED! => {msg}",
                        _RED,
                        self._colorize,
                    )
                )
        elif name == "v2_runner_on_unreachable":
            self._flush_pending_skips(force_individual=True)
            self._current_task_had_nonskipped_result = True
            suffix = self._inline_duration_suffix(event, event_time)
            for host, result in event.get("hosts", {}).items():
                msg = _truncate_msg(result.get("msg", "") or "")
                self._display.print_log(
                    _wrap(
                        f"fatal: [{host}]{suffix}: UNREACHABLE! => {msg}",
                        _MAGENTA,
                        self._colorize,
                    )
                )
        elif name == "v2_runner_on_skipped":
            # Hold individual skipping lines until we know whether
            # they're worth printing one-by-one (mixed-result task)
            # or worth collapsing (all-skipped task). The flush
            # happens at task transition or stats.
            self._pending_skipped_hosts.extend(event.get("hosts", {}).keys())
        elif name == "v2_playbook_on_stats":
            # Drain the final task's skipped buffer with the same
            # mixed-vs-all-skipped rule we use at task transitions.
            self._flush_pending_skips(force_individual=self._current_task_had_nonskipped_result)
            self._current_task_had_nonskipped_result = False
            # Final task's summary line — same logic as the inter-task
            # case, just triggered by stats instead of the next task_start.
            if event_time is not None:
                self._emit_previous_task_summary(event_time)
                # Clear so a subsequent run doesn't see a stale last task.
                self._last_task_uuid = None
                self._last_task_name = None
                self._last_task_start_time = None

    def _inline_duration_suffix(self, event: dict, event_time: float | None) -> str:
        """Return `` (2.3s)`` for the per-host result line, or empty.

        Empty when timing data is unavailable (missing ``_timestamp``,
        no recorded task start) so the result line still renders.
        Skipped tasks are intentionally NOT timed inline — they
        haven't really run, the duration is meaningless.
        """
        if event_time is None:
            return ""
        task_id = event.get("task", {}).get("id", "")
        start = self._task_start_times.get(task_id)
        if start is None:
            return ""
        delta = event_time - start
        if delta < 0:
            return ""
        return f" ({self._format_duration(delta)})"
