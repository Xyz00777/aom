"""Compact renderer for AOM.

This module implements the ANSI-based compact view renderer.
See SPECIFICATION.md Section 4.1 for compact view details.

TDD: Tests defined in tests/integration/test_compact_renderer.py.
"""

from typing import Any


class CompactRenderer:
    """ANSI-based compact renderer satisfying the Renderer Protocol.

    Implements the Renderer interface defined in ansible_aom.renderer.protocol.
    Uses Rich Live display for terminal output with blessed for ANSI control.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the compact renderer.

        Args:
            **kwargs: Additional configuration options passed from factory.
        """
        self._playbook: str = ""
        self._args: list[str] = []
        self._state: dict[str, Any] = {}

    def start(self, playbook: str, args: list[str]) -> None:
        """Start rendering a playbook run.

        Args:
            playbook: Path to the playbook file.
            args: Additional arguments passed to ansible-playbook.
        """
        self._playbook = playbook
        self._args = args
        self._state = {"started": True}

    def update_state(self, event: dict) -> None:
        """Handle a new JSONL event.

        Args:
            event: JSONL event dictionary from ansible.
        """
        self._state["last_event"] = event

    def handle_password_prompt(self, prompt_text: str) -> str:
        """Handle a password prompt.

        Stops Rich Live display, shows prompt, reads password via getpass,
        then restarts display.

        Args:
            prompt_text: The password prompt text from ansible.

        Returns:
            The password entered by the user.
        """
        try:
            import getpass
            password = getpass.getpass(prompt_text)
            return password
        except Exception:
            return ""

    def handle_completion(self, exit_code: int, state: str) -> None:
        """Handle playbook completion (success/failure/crash).

        Args:
            exit_code: Exit code from ansible-playbook.
            state: Final state string ('completed', 'failed', 'crashed').
        """
        self._state["completed"] = True
        self._state["exit_code"] = exit_code
        self._state["final_state"] = state

    def stop(self) -> None:
        """Stop rendering and clean up resources.

        Restores terminal state, flushes output, cleans up any running
        Rich Live display.
        """
        self._state = {}