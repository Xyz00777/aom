"""Password handling for compact mode.

The pure detection heuristic (:func:`is_password_prompt`) and the list
of ansible/sudo prompt regexes (``PASSWORD_PATTERNS``) live in
:mod:`ansible_aom.core.prompts` — they're re-exported here for back
compat with code that learned to import them from this module.

This module owns only the *response* side: stopping Rich Live and
delegating to ``getpass`` for a terminal pass-through read. See
SPECIFICATION.md Section 5.10.
"""

from __future__ import annotations

import getpass
import sys
from typing import Any

from ansible_aom.core.prompts import PASSWORD_PATTERNS, is_password_prompt

__all__ = ["PASSWORD_PATTERNS", "is_password_prompt", "handle_password_prompt"]

DEFAULT_PASSWORD_TIMEOUT = 60


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
