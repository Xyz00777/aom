"""Renderer Protocol for AOM.

This module defines the Protocol that both CompactRenderer and AOMApp
must satisfy, enabling the shared core to work with either backend.

See SPECIFICATION.md Section 2.3 for Renderer Protocol definition.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Renderer(Protocol):
    """Protocol that both CompactRenderer and AOMApp satisfy."""

    def start(self, playbook: str, args: list[str]) -> None:
        """Start rendering a playbook run."""
        ...

    def set_definitions(self, definitions: list) -> None:
        """Receive pre-flight playbook definitions (plays/tasks/hosts).

        Called once between start() and the first update_state(). Renderers
        use this to seed the task tree and total host count before any
        JSONL events arrive. May receive an empty list when preflight
        failed; renderers must tolerate that.
        """
        ...

    def update_state(self, event: dict) -> None:
        """Handle a new JSONL event."""
        ...

    def handle_password_prompt(self, prompt_text: str) -> str:
        """Handle a password prompt. Returns the password."""
        ...

    def handle_interactive_prompt(self, prompt_text: str) -> str:
        """Handle a non-password interactive prompt (pause, vars_prompt).

        Unlike ``handle_password_prompt`` this does NOT suppress echo —
        the user expects to see what they type. Renderers must:

        1. Stop / suspend any live panel (so the captured prompt text
           is visible).
        2. Surface ``prompt_text`` to the user (whatever the child has
           emitted with no trailing newline).
        3. Read one line from stdin.
        4. Restart the panel.
        5. Return the line (or empty string on EOF / KeyboardInterrupt).
        """
        ...

    def handle_completion(self, exit_code: int, state: str) -> None:
        """Handle playbook completion (success/failure/crash)."""
        ...

    def stop(self) -> None:
        """Stop rendering and clean up."""
        ...

    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        """Surface a warning or deprecation to the user.

        Implementations are expected to make the message visible (above
        the panel, in a dedicated panel, etc.) and bump any visible
        counter. Renderers that don't have a visible UI may treat this
        as a no-op.
        """
        ...

    def print_log(self, message: str) -> None:
        """Print a log line above the live panel.

        Implementations may render directly to stdout, log to a file,
        or no-op for headless renderers.
        """
        ...

    def tick(self) -> None:
        """Refresh time-based UI elements during quiet periods.

        Called by the runner when no output has been received for a
        timeout window. Renderers that show elapsed time use this to
        keep the clock moving; renderers with their own loop may no-op.
        """
        ...
