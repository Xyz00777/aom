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
from ansible_aom.core.models import RunState, Status

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

    def update_state(self, event: dict) -> None:
        """Handle a new JSONL event.

        Processes the event to update RunState, then refreshes the display.

        Args:
            event: JSONL event dictionary from ansible.
        """
        if self._state is None:
            return

        # Update RunState with the event
        self._state.handle_event(event)

        # Calculate current statistics from state
        hosts_completed = 0
        hosts_total = 0

        # Count hosts and states from RunState
        host_statuses: dict[str, Status] = {}

        for play in self._state.plays.values():
            for task in play.tasks.values():
                for hostname, host_state in task.hosts.items():
                    host_statuses[hostname] = host_state.status

        hosts_total = len(host_statuses)
        for status in host_statuses.values():
            if status in (Status.OK, Status.CHANGED, Status.SKIPPED, Status.COMPLETED):
                hosts_completed += 1

        # Calculate elapsed time
        elapsed = time.time() - self._start_time

        # Format and update status bar
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

            hosts_total = len(host_statuses)
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
