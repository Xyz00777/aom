"""Password handling for compact mode.

Terminal pass-through pattern for password prompts.
See SPECIFICATION.md Section 5.10.
"""

from __future__ import annotations

import getpass
import re
import sys
from typing import Any

# From SPECIFICATION.md Section 5.10
PASSWORD_PATTERNS: list[str] = [
    r"Vault password: ",
    r"Vault password \([^)]+\): ",  # vault_id variant
    r"SSH password: ",
    r"BECOME password: ",
    r"BECOME password\[defaults to SSH password\]: ",
    r"New Vault password: ",
    r"Confirm New Vault password: ",
]

DEFAULT_PASSWORD_TIMEOUT = 60


def is_password_prompt(text: str) -> bool:
    """Check if text matches any known password prompt pattern.

    Args:
        text: The text to check for password prompt patterns.

    Returns:
        True if text matches any password prompt pattern, False otherwise.
    """
    return any(re.search(pattern, text) for pattern in PASSWORD_PATTERNS)


def handle_password_prompt(
    prompt_text: str,
    child: Any = None,
) -> str:
    """Handle password prompt using terminal pass-through for compact mode.

    The caller is responsible for stopping Rich Live before calling this
    function and resuming it after.

    Args:
        prompt_text: The prompt text from pexpect (e.g., "Vault password: ").
        child: pexpect.spawn instance (unused in compact mode, kept for
            interface compatibility with TUI mode).

    Returns:
        Password entered by user, or empty string on error/cancellation.
    """
    try:
        sys.stdout.write("\033[999;0H\n")
        sys.stdout.flush()
    except OSError, AttributeError:
        pass  # Non-TTY environment

    try:
        return getpass.getpass(prompt_text)
    except EOFError, KeyboardInterrupt, OSError:
        return ""
