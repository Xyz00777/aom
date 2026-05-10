"""Compact renderer for AOM.

This module implements the ANSI-based compact view renderer.
See SPECIFICATION.md Section 4.1 for compact view details.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from ansible_aom.compact.display import Display
from ansible_aom.compact.password import handle_password_prompt as do_handle_password_prompt
from ansible_aom.core.icons import STATUS_ICONS
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
) -> str:
    """Format the status bar for compact mode display.

    Args:
        playbook: Path to the playbook file.
        hosts_completed: Number of hosts that completed.
        hosts_total: Total number of hosts.
        warnings: Number of warnings encountered.
        deprecations: Number of deprecations encountered.
        elapsed_seconds: Elapsed time in seconds.

    Returns:
        Formatted status bar string: "playbook │ X/Y hosts │ ⚠ N ✱ N │ H:MM:SS"

    Example:
        >>> format_status_bar("site.yml", 3, 10, 2, 1, 323)
        'site.yml │ 3/10 hosts │ ⚠ 2 ✱ 1 │ 0:05:23'
    """
    elapsed_int = int(elapsed_seconds)
    elapsed_h = elapsed_int // 3600
    elapsed_m = (elapsed_int % 3600) // 60
    elapsed_s = elapsed_int % 60
    elapsed_str = f"{elapsed_h}:{elapsed_m:02d}:{elapsed_s:02d}"

    parts = [
        playbook,
        f"{hosts_completed}/{hosts_total} hosts",
    ]

    if warnings > 0:
        parts.append(f"⚠ {warnings}")
    if deprecations > 0:
        parts.append(f"✱ {deprecations}")

    parts.append(elapsed_str)

    return " │ ".join(parts)


def format_host_summary(
    hostname: str,
    ok: int,
    changed: int,
    failed: int,
    unreachable: int,
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
    parts = [f"{hostname}:"]

    if ok > 0:
        icon = STATUS_ICONS[Status.OK]
        parts.append(f"{icon} {ok} ok")
    if changed > 0:
        icon = STATUS_ICONS[Status.CHANGED]
        parts.append(f"{icon} {changed} changed")
    if failed > 0:
        icon = STATUS_ICONS[Status.FAILED]
        parts.append(f"{icon} {failed} failed")
    if unreachable > 0:
        icon = STATUS_ICONS[Status.UNREACHABLE]
        parts.append(f"{icon} {unreachable} unreachable")

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

    return "\n".join(lines)


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

    def __init__(self, **kwargs: object) -> None:
        """Initialize the compact renderer.

        Args:
            **kwargs: Additional configuration options.
                - is_tty: Whether stdout is a TTY (default: True).
        """
        is_tty = kwargs.get("is_tty", True)
        if isinstance(is_tty, bool):
            self._display = Display(is_tty=is_tty)
        else:
            self._display = Display(is_tty=True)

        self._state: RunState | None = None
        self._playbook: str = ""
        self._args: list[str] = []
        self._start_time: float = 0.0
        self._warnings_count: int = 0
        self._deprecations_count: int = 0
        self._definitions: list = []

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
        )
        self._display.update(status_bar)

    def set_definitions(self, definitions: list) -> None:
        """Store preflight definitions and recompute the initial status bar.

        The host count in the status bar is the union of every play's
        resolved_hosts. We compute it once here so the user sees `0/N hosts`
        from the very first frame instead of `0/0 hosts` until JSONL
        events start filling in hosts incrementally.
        """
        self._definitions = list(definitions)
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
        )
        self._display.update(status_bar)

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

    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        """Add a warning or deprecation detected from PTY stream.

        Called by the PTY stream handler when it detects warning patterns
        in stderr lines (warnings are not emitted as JSONL events).

        Args:
            message: The warning message text.
            is_deprecation: True if this is a deprecation warning.
        """
        if is_deprecation:
            self._deprecations_count += 1
        else:
            self._warnings_count += 1

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

        # Format final status bar
        status_bar = format_status_bar(
            playbook=self._playbook,
            hosts_completed=hosts_completed,
            hosts_total=hosts_total,
            warnings=self._warnings_count,
            deprecations=self._deprecations_count,
            elapsed_seconds=elapsed,
        )

        # Add final state indicator
        state_indicator = {
            "completed": "●",
            "failed": "✖",
            "crashed": "✖",
        }.get(state, "?")

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

    def stop(self) -> None:
        """Stop rendering and clean up resources.

        Restores terminal state, flushes output, and cleans up
        any running Rich Live display.
        """
        self._display.stop()
        self._state = None

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
            task_name = event.get("task", {}).get("name", "") or "(unnamed)"
            self._display.print_log(f"\nTASK [{task_name}] " + "*" * 50)
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
