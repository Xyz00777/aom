"""Password handling for compact mode.

Terminal pass-through pattern for password prompts.
See SPECIFICATION.md Section 5.10 for password handling.

TDD: This file contains STUB implementations only. Tests come first.
"""

from typing import Any


def handle_password_prompt(
    prompt_text: str,
    child: Any,
    live: Any,
) -> str:
    """Handle password prompt using terminal pass-through.

    Args:
        prompt_text: The prompt text from pexpect.
        child: pexpect.spawn instance.
        live: Rich Live instance.

    Returns:
        Password entered by user.
    """
    raise NotImplementedError("handle_password_prompt - tests first")
