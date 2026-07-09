"""Memory bounds constants for AOM.

This module previously also housed an ``ExecutionState`` enum and a
``StateMachine`` class implementing an 8-state execution state machine
(SPECIFICATION.md §6.4). Those types were never wired into production
code — the TUI tracked state as a plain string, the compact renderer
relied on the ``RunState`` data model, and the runner passed lowercase
strings ("completed" / "failed" / "crashed") to ``handle_completion``.

GRUMPI_QA finding 9A flagged them as dead code. The classes have been
removed; this module now contains only the memory-bounds constants
that are actually imported by production code (``parser.py`` and
``tui/widgets/log_panel.py`` use ``MAX_LOG_LINES``).

Memory bounds (SPECIFICATION.md §6.5):
- MAX_PLAYS: Maximum 1000 plays tracked
- MAX_TASKS_PER_PLAY: Maximum 10000 tasks per play
- MAX_HOSTS_PER_TASK: Maximum 10000 hosts per task
- MAX_TOTAL_HOST_RUN_STATES: Maximum 1,000,000 total HostRunState entries
- MAX_LOG_LINES: Maximum 50000 log panel lines
"""

MAX_PLAYS = 1000
MAX_TASKS_PER_PLAY = 10000
MAX_HOSTS_PER_TASK = 10000
MAX_TOTAL_HOST_RUN_STATES = 1000000
MAX_LOG_LINES = 50000
