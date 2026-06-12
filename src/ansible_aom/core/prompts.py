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


def reconstruct_pause_prompt(plaintext_lines: list[str], max_lookback: int = 100) -> str | None:
    """Rebuild a multi-line ``ansible.builtin.pause`` block from recent plaintext.

    A YAML block-scalar ``prompt:`` (``|``, ``>``, …) keeps a trailing
    newline, so ansible's ``"[%s]\\n%s:"`` pause format puts the
    terminating ``:`` on its OWN line. Every line of the block ends in
    ``\\r\\n``, so pexpect's newline matcher consumes the whole block and
    the unread PTY buffer is empty when the read TIMEOUTs. Neither the
    (empty) buffer nor the immediate prior line — a bare ``:`` — carries
    a signal, and the identifying ``[Task name]`` header may be many
    lines back (e.g. behind a long deploy-preview block). So the
    line-at-a-time detection misses it and the child blocks on stdin
    forever.

    Walk backwards from the LITERAL last line: when it ends in a prompt
    terminator (``:`` or ``?``), look within ``max_lookback`` lines for an
    *anchor* that identifies the block:

    * a ``[Task name]`` header line — preferred, since it starts the
      block and gives the fullest context; OR
    * an interactive-marker line (``Press Enter``, ``(yes/no)``, …) —
      the fallback that keeps detection working when the header has
      scrolled out of the window above a long preview block.

    Return the block from the chosen anchor to the end, joined with
    newlines, so the caller can hand it to
    :func:`looks_like_interactive_prompt`. Else None.

    The last line must be the terminator itself (no skipping trailing
    blanks): once the prompt is answered the PTY echoes a newline, which
    becomes a blank last line — refusing to walk past it is what stops a
    just-answered block from being re-surfaced and re-fired.
    """
    if not plaintext_lines:
        return None
    tail_idx = len(plaintext_lines) - 1
    tail = _strip_ansi(plaintext_lines[tail_idx]).rstrip()
    if not tail or tail[-1] not in (":", "?"):
        return None
    lo = max(0, tail_idx - max_lookback)
    marker_idx: int | None = None
    for i in range(tail_idx, lo - 1, -1):
        clean = _strip_ansi(plaintext_lines[i]).strip()
        # A header starts the block — best anchor; stop and use it.
        if _BRACKETED_HEADER_RE.fullmatch(clean):
            return "\n".join(plaintext_lines[i : tail_idx + 1])
        # Remember the nearest marker line as a fallback anchor; keep
        # scanning in case a header sits further back (fuller context).
        if marker_idx is None and any(m in clean for m in INTERACTIVE_PROMPT_MARKERS):
            marker_idx = i
    if marker_idx is not None:
        return "\n".join(plaintext_lines[marker_idx : tail_idx + 1])
    return None
