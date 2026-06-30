"""Process exit-code derivation from a :class:`RunState`.

Pure: in → out, no I/O. Lives in :mod:`ansible_aom.core` so every layer
(renderers, parity reducer, JSON formatter, tests) depends on a single
canonical implementation. See ARCHITECTURE.md §7.3 for the layering rule
that put it here instead of in ``compact/`` or ``formats/``.
"""

from __future__ import annotations

from ansible_aom.core.models import Status
from ansible_aom.core.run_state import RunState


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
