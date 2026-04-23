"""Renderer Protocol for AOM.

This module defines the Protocol that both CompactRenderer and AOMApp
must satisfy, enabling the shared core to work with either backend.

See SPECIFICATION.md Section 2.3 for Renderer Protocol definition.
"""

from typing import Protocol


class Renderer(Protocol):
    """Protocol that both CompactRenderer and AOMApp satisfy."""

    def start(self, playbook: str, args: list[str]) -> None:
        """Start rendering a playbook run."""
        ...

    def update_state(self, event: dict) -> None:
        """Handle a new JSONL event."""
        ...

    def handle_password_prompt(self, prompt_text: str) -> str:
        """Handle a password prompt. Returns the password."""
        ...

    def handle_completion(self, exit_code: int, state: str) -> None:
        """Handle playbook completion (success/failure/crash)."""
        ...

    def stop(self) -> None:
        """Stop rendering and clean up."""
        ...