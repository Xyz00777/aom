"""Main AOM TUI Application.

This module implements the Textual-based TUI renderer.
See SPECIFICATION.md Section 4.2 for full TUI details.

TDD: This file contains STUB implementations only. Tests come first.
"""

from typing import Any

from textual.app import App


class AOMApp(App[None]):
    """Textual-based TUI renderer satisfying the Renderer Protocol."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        pass

    def start(self, playbook: str, args: list[str]) -> None:
        raise NotImplementedError("start - tests first")

    def update_state(self, event: dict) -> None:
        raise NotImplementedError("update_state - tests first")

    def handle_password_prompt(self, prompt_text: str) -> str:
        raise NotImplementedError("handle_password_prompt - tests first")

    def handle_completion(self, exit_code: int, state: str) -> None:
        raise NotImplementedError("handle_completion - tests first")

    def stop(self) -> None:
        raise NotImplementedError("stop - tests first")