"""Pure prompt-detection heuristics.

Two responsibilities, both pure (str in → bool out):

* :func:`is_password_prompt` — does the text look like one of the
  known ansible / sudo / vault prompts?
* :func:`looks_like_interactive_prompt` — does the text look like a
  child waiting on stdin (``ansible.builtin.pause``, ``vars_prompt``,
  ``(yes/no)``)?

Pulled into ``core/`` per ARCHITECTURE.md §7.5 so the response
mechanism (terminal pass-through in compact, Textual modal in TUI)
can stay infrastructure-side. Pure functions belong in the domain
layer.
"""

from __future__ import annotations

import re

# =============================================================================
# Password prompts
# =============================================================================

# Ansible-native prompts (SPECIFICATION.md Section 5.10) plus a small
# set of sudo pass-through prompts. The sudo prompts matter when a
# module shells out (``community.general.homebrew`` running a formula
# whose post-install hooks invoke ``sudo``, or a ``shell``/``command``
# task that calls ``sudo`` directly): ansible itself doesn't wrap those
# in its own prompt format, so the raw sudo banner lands on the PTY.
PASSWORD_PATTERNS: list[str] = [
    r"Vault password: ",
    r"Vault password \([^)]+\): ",  # vault_id variant
    r"SSH password: ",
    r"BECOME password: ",
    r"BECOME password\[defaults to SSH password\]: ",
    r"New Vault password: ",
    r"Confirm New Vault password: ",
    r"\[sudo\] password for [^:\n]+: ",  # Linux sudo default; more specific, list first
    r"Password for [^:\n]+: ",  # sudo -p "Password for %u: " and similar
    r"Password: ",  # macOS sudo bare prompt — keep last as the broadest match
]


def is_password_prompt(text: str) -> bool:
    """Check if ``text`` matches any known password prompt pattern."""
    return any(re.search(pattern, text) for pattern in PASSWORD_PATTERNS)


# =============================================================================
# Interactive (non-password) prompts
# =============================================================================

# High-confidence prompt markers. When any of these substrings appears
# in the unread PTY buffer during a TIMEOUT branch, we're confident the
# child is blocked on stdin (``ansible.builtin.pause``, ``vars_prompt``,
# common yes/no confirmations).
INTERACTIVE_PROMPT_MARKERS: tuple[str, ...] = (
    "[pause]",
    "Press Enter",
    "press enter",
    "(yes/no)",
    "(y/n)",
    "[y/N]",
    "[Y/n]",
    "[yes/no]",
)

_VARS_PROMPT_RE = re.compile(r"^\s*\[[^\]\n]+\]\s*(\([^)]*\))?\s*:\s*$", re.MULTILINE)

# Real ansible decorates the pause prompt with a bracketed task-name
# header on its own line, e.g. ``[Confirm deployment]\n<prompt>:``.
# Detect that as a strong "this is a pause prompt" signal regardless
# of the prompt text the user typed in their playbook.
_BRACKETED_HEADER_RE = re.compile(r"^\s*\[[^\]\n]+\]\s*$", re.MULTILINE)

_ANSI_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    """Remove SGR escape sequences from ``text``."""
    return _ANSI_SGR_RE.sub("", text)


def looks_like_interactive_prompt(pending: str, prior_plaintext: str | None = None) -> bool:
    """True if ``pending`` (unread PTY buffer) looks like a child waiting on stdin.

    High-confidence signals only:

    - non-empty
    - last non-whitespace char is ``:`` or ``?`` (the universal
      "prompt waiting" terminator)
    - AND one of:

      * contains a known marker (``[pause]``, ``Press Enter``,
        ``(yes/no)``, …)
      * ends in ``?`` (any question — strong signal)
      * matches the ``vars_prompt`` default ``[name]: `` /
        ``[name] (default): `` format
      * has a bracketed header on its own line above the prompt
        inside ``pending``
      * ``prior_plaintext`` (the most recently consumed plaintext
        line, ANSI-stripped) is a bracketed header on its own —
        real ansible pause emits the header and the prompt on
        separate lines, and the header is consumed by the
        newline-matcher before the prompt's TIMEOUT fires.

    ANSI SGR escape sequences are stripped before any of these checks.
    ansible colorises the pause prompt by default, so the raw buffer
    often ends in ``\\x1b[0m`` (a reset code) rather than the
    visible ``:``.

    False positives still possible (e.g. a debug task ending in
    ``Installing packages:``) but rare; the cost is one spurious
    newline sent to the child, which is harmless when no module is
    reading from stdin. Pure trailing-``:`` without any other signal
    is intentionally rejected — it's too common in regular log lines.
    """
    clean = _strip_ansi(pending)
    text = clean.rstrip()
    if not text:
        return False
    last_char = text[-1]
    if last_char not in (":", "?"):
        return False
    if last_char == "?":
        return True
    if any(marker in clean for marker in INTERACTIVE_PROMPT_MARKERS):
        return True
    # vars_prompt default: the last line is ``[varname]: `` or
    # ``[varname] (default): ``. Anchor to MULTILINE start so log
    # lines that happen to contain ``[FOO]`` later don't trip it.
    last_line = clean.splitlines()[-1] if "\n" in clean else clean
    if _VARS_PROMPT_RE.match(last_line):
        return True
    # Real ansible pause output: a ``[Task name]`` header line.
    # Either above the prompt inside the same buffer, OR consumed
    # earlier as a separate plaintext line (newline-terminated, so
    # pexpect routed it through ``_feed`` before TIMEOUT fired).
    if _BRACKETED_HEADER_RE.search(clean):
        return True
    if prior_plaintext is not None:
        prior_clean = _strip_ansi(prior_plaintext).strip()
        if _BRACKETED_HEADER_RE.fullmatch(prior_clean):
            return True
    return False
