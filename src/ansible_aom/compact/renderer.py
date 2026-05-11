"""Compact renderer for AOM.

This module implements the ANSI-based compact view renderer.
See SPECIFICATION.md Section 4.1 for compact view details.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from ansible_aom.compact.display import Display
from ansible_aom.compact.password import handle_password_prompt as do_handle_password_prompt
from ansible_aom.core.icons import STATUS_ICONS, STATUS_ICONS_ASCII, is_unicode_terminal
from ansible_aom.core.models import (
    PlayDefinition,
    RoleGroupDefinition,
    RunState,
    Status,
)

if TYPE_CHECKING:
    pass


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

    sep = "|" if ascii_mode else "│"
    warn_glyph = "!" if ascii_mode else "⚠"
    deprec_glyph = "*" if ascii_mode else "✱"

    parts = [
        playbook,
        f"{hosts_completed}/{hosts_total} hosts",
    ]

    if tasks_total > 0:
        parts.append(f"{tasks_completed}/{tasks_total} tasks")

    if warnings > 0:
        parts.append(f"{warn_glyph} {warnings}")
    if deprecations > 0:
        parts.append(f"{deprec_glyph} {deprecations}")

    parts.append(elapsed_str)

    return f" {sep} ".join(parts)


def format_host_summary(
    hostname: str,
    ok: int,
    changed: int,
    failed: int,
    unreachable: int,
    ascii_mode: bool = False,
) -> str:
    """Format a host summary line with status icons.

    Only includes non-zero counts in the output.

    Args:
        hostname: The hostname.
        ok: Number of OK tasks.
        changed: Number of changed tasks.
        failed: Number of failed tasks.
        unreachable: Number of unreachable tasks.

    Returns:
        Formatted host summary with icons: "hostname: ● N ok, ◆ M changed, ..."

    Example:
        >>> format_host_summary("web1", 12, 3, 0, 0)
        'web1: ● 12 ok ◆ 3 changed'
    """
    icons = STATUS_ICONS_ASCII if ascii_mode else STATUS_ICONS
    parts = [f"{hostname}:"]

    if ok > 0:
        parts.append(f"{icons[Status.OK]} {ok} ok")
    if changed > 0:
        parts.append(f"{icons[Status.CHANGED]} {changed} changed")
    if failed > 0:
        parts.append(f"{icons[Status.FAILED]} {failed} failed")
    if unreachable > 0:
        parts.append(f"{icons[Status.UNREACHABLE]} {unreachable} unreachable")

    return " ".join(parts)


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


def format_failure_recap(state: RunState) -> list[str]:
    """Build per-failure lines naming the host and task that went wrong.

    Returns one line per (host, task) pair that ended in FAILED or
    UNREACHABLE. Empty list when nothing failed — handle_completion uses
    that as a signal to suppress the recap section entirely.

    Format::

        FAILED: web2 — install nginx
        UNREACHABLE: db1 — gather facts
    """
    lines: list[str] = []
    for play in state.plays.values():
        for task in play.tasks.values():
            for hostname, host_state in task.hosts.items():
                if host_state.status == Status.FAILED:
                    lines.append(f"FAILED: {hostname} — {task.name}")
                elif host_state.status == Status.UNREACHABLE:
                    lines.append(f"UNREACHABLE: {hostname} — {task.name}")
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
        )
        self._display.update(status_bar)

    def handle_interactive_prompt(self, prompt_text: str) -> str:
        """Surface a pause / vars_prompt-style prompt and capture one line.

        Mirrors ``handle_password_prompt`` but uses ``input()`` instead of
        ``getpass.getpass`` because pause and vars_prompt are not secrets —
        echo is expected. The Rich Live panel is stopped before the prompt
        prints so the user can actually see the captured prompt text; the
        panel restarts in a finally block so a crashing ``input()`` never
        leaves the terminal headless.
        """
        self._display.stop()
        try:
            return input(prompt_text)
        except EOFError, KeyboardInterrupt:
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
        )

        # Add final state indicator
        if self._ascii_mode:
            state_indicator = {"completed": "*", "failed": "X", "crashed": "X"}.get(state, "?")
        else:
            state_indicator = {"completed": "●", "failed": "✖", "crashed": "✖"}.get(state, "?")

        final_status = f"{status_bar} {state_indicator}"

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
            for line in format_failure_recap(self._state):
                print(f"  {line}")

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

    def _emit_event_log(self, event: dict) -> None:
        """Print one nom-style log line for a JSONL event.

        Stats events are intentionally silent — the live panel and the
        final-summary print already cover what they would say. Unknown
        event types are silent too: the panel still updates from state,
        we just don't add to the log noise.
        """
        name = event.get("_event")
        if name == "v2_playbook_on_play_start":
            play_name = event.get("play", {}).get("name", "") or "(unnamed)"
            self._display.print_log(f"\nPLAY [{play_name}] " + "*" * 50)
        elif name == "v2_playbook_on_task_start":
            task = event.get("task", {})
            task_name = task.get("name", "") or "(unnamed)"
            self._display.print_log(f"\nTASK [{task_name}] " + "*" * 50)
            self._maybe_emit_pause_seconds_hint(task)
        elif name == "v2_runner_on_ok":
            for host, result in event.get("hosts", {}).items():
                verb = "changed" if result.get("changed") else "ok"
                self._display.print_log(f"{verb}: [{host}]")
        elif name == "v2_runner_on_failed":
            for host, result in event.get("hosts", {}).items():
                msg = result.get("msg", "") or ""
                self._display.print_log(f"fatal: [{host}]: FAILED! => {msg}")
        elif name == "v2_runner_on_unreachable":
            for host, result in event.get("hosts", {}).items():
                msg = result.get("msg", "") or ""
                self._display.print_log(f"fatal: [{host}]: UNREACHABLE! => {msg}")
        elif name == "v2_runner_on_skipped":
            for host in event.get("hosts", {}):
                self._display.print_log(f"skipping: [{host}]")
