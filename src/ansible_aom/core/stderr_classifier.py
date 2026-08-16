"""V1 stderr classifier — maps raw ansible-playbook stderr lines to typed events.

ansible-core writes a wide variety of lines to stderr: always-emitted
warnings and errors, connection-lifecycle messages at various verbosity
levels, vault debug at ``-vvvvv``, and a long tail of run-level
diagnostics (config file, play count, retry file, etc.). The classifier
turns a raw line into a :class:`StderrEvent` carrying:

- a stable :class:`StderrSource` enum value (12 named sources + UNKNOWN),
- an extracted host (when the line is ``<hostname>``-prefixed) or ``None``,
- a numeric level (0 = always, 1-4 = caplevel bands),
- the original line text (ANSI-stripped by the caller — see parser.py).

Source-of-truth: ``.sisyphus/notepads/2026-06-30-verbosity-pre-impl-interview/
stderr-classification-taxonomy.md`` (the upstream ansible-core 2.20.4
research that enumerates all 36 line categories and maps them onto 12
v1 source values). Order of rules in :data:`CLASSIFIER_RULES` matters:
first match wins. The taxonomy document Section 4 specifies the order;
any change here must update the doc and re-run the parametrised sample
tests in ``tests/unit/test_stderr_classifier.py``.

Architecture rules:
- Lives in ``core/`` because both infrastructure (compact, tui, formats)
  and other ``core/`` modules import it. It must not import from
  ``compact/``, ``tui/``, ``formats/``, or ``renderer/``.
- Pure-Python; no I/O. Reused by ``core/parser.py:_handle_plaintext``
  (Phase 4 wiring) and by ``session/store.py:record_stderr`` to emit
  ``aom_stderr_line`` synthetic events.
- First-match-wins semantics; no fuzzy matching. The classifier is on
  the PTY hot path so all regexes are pre-compiled at import time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, IntEnum


class StderrSource(str, Enum):
    """Stable enum of stderr line sources (v1 contract — 12 named values).

    Plus an :attr:`UNKNOWN` catch-all for lines that match no rule.
    Used as the ``source`` field on emitted ``aom_stderr_line`` events.
    """

    WARNING = "warning"
    DEPRECATION = "deprecation"
    ERROR = "error"
    SSH_DEBUG = "ssh_debug"
    SSH_INFO = "ssh_info"
    CONNECTION = "connection"
    CONNECTION_LIFECYCLE = "connection_lifecycle"
    PLUGIN_LOADING = "plugin_loading"
    INVENTORY = "inventory"
    VAULT = "vault"
    PROMPT = "prompt"
    RUN_LEVEL = "run_level"
    UNKNOWN = "unknown"


class StderrLevel(IntEnum):
    """Numeric verbosity caplevel for an ``aom_stderr_line`` event.

    Mirrors ansible-core's ``display.v*`` caplevel bands. A line is
    emitted when ``Display.verbosity >= caplevel``. ``ALWAYS`` (0) is
    used for warnings/errors/prompts that are never gated by verbosity.
    """

    ALWAYS = 0
    V = 1
    VV = 2
    VVV = 3
    VVVVV = 4


# Mapping from source to the caplevel at which the line first appears.
# The level is informational only — AOM does not filter on it for
# recording, since ``--capture-verbose`` is a single on/off switch. But
# the field is part of the event schema and the TUI uses it for display
# (greying out sub-vvvvv lines by default).
LEVEL_MAP: dict[StderrSource, StderrLevel] = {
    StderrSource.WARNING: StderrLevel.ALWAYS,
    StderrSource.DEPRECATION: StderrLevel.ALWAYS,
    StderrSource.ERROR: StderrLevel.ALWAYS,
    StderrSource.SSH_DEBUG: StderrLevel.VVVVV,
    StderrSource.SSH_INFO: StderrLevel.VV,
    StderrSource.CONNECTION: StderrLevel.VVV,
    StderrSource.CONNECTION_LIFECYCLE: StderrLevel.VVV,
    StderrSource.PLUGIN_LOADING: StderrLevel.VVV,
    StderrSource.INVENTORY: StderrLevel.VV,
    StderrSource.VAULT: StderrLevel.VVVVV,
    StderrSource.PROMPT: StderrLevel.ALWAYS,
    StderrSource.RUN_LEVEL: StderrLevel.V,
    StderrSource.UNKNOWN: StderrLevel.V,
}


@dataclass(frozen=True)
class StderrEvent:
    """A classified stderr line.

    Carries the full info needed to emit a synthetic ``aom_stderr_line``
    JSONL event. ``host`` is ``None`` for run-level lines. ``level`` is
    the ansible-core caplevel band (0-4).
    """

    source: StderrSource
    host: str | None
    level: StderrLevel
    line: str


# Ansible profiling callback banner regex (e.g. profile_tasks / timer).
_PROFILE_TASKS_BANNER_RE = re.compile(
    r".*\((?:\d+:)?\d{2}:\d{2}\.\d{3}\)\s+(?:\d+:)?\d{2}:\d{2}\.\d{3}\s+\*{3,}\s*$"
)


def is_profiling_banner(line: str) -> bool:
    """True if ``line`` is an external callback profiling banner (e.g. profile_tasks)."""
    return bool(_PROFILE_TASKS_BANNER_RE.match(line))


# -----------------------------------------------------------------------------
# CLASSIFIER_RULES
# -----------------------------------------------------------------------------
# Each rule: ``(StderrSource, compiled regex, has_host)``.
#
# - Rules are tried in order; first match wins.
# - ``has_host`` is a hint that the regex carries a ``<hostname>`` prefix.
#   When the prefix is absent, host is None even if has_host is True.
# - The 30 entries below map the 36 upstream categories from
#   stderr-classification-taxonomy.md onto the 12 v1 source values.
#
# When updating these rules, also update the taxonomy doc and re-run
# ``tests/unit/test_stderr_classifier.py::TestRealWorldSamples`` to
# confirm the sample lines still classify as expected.
# -----------------------------------------------------------------------------

CLASSIFIER_RULES: list[tuple[StderrSource, re.Pattern[str], bool]] = [
    # 1. Warnings (most common, check first).
    (StderrSource.WARNING, re.compile(r"^\[WARNING\]: "), False),
    # 2. Deprecation warnings.
    (StderrSource.DEPRECATION, re.compile(r"^\[DEPRECATION WARNING\]: "), False),
    # 3. Errors (bracketed).
    (StderrSource.ERROR, re.compile(r"^\[ERROR\]: "), False),
    # 4. Preflight errors (unbracketed ERROR: from cli/__init__.py).
    (StderrSource.ERROR, re.compile(r"^ERROR: "), False),
    # 5. SSH agent operations — must come BEFORE the generic SSH: rule
    #    because both match the same prefix.
    (StderrSource.SSH_INFO, re.compile(r"^(?:<([^>]+)> )?SSH: SSH_AGENT "), True),
    # 6. SSH connection errors.
    (
        StderrSource.SSH_INFO,
        re.compile(r"^(?:<([^>]+)> )?Failed to connect to the host via ssh:"),
        True,
    ),
    # 7. SSH retry messages.
    (StderrSource.SSH_INFO, re.compile(r"^(?:<([^>]+)> )?ssh_retry: attempt:"), True),
    # 8. SSH return code (censored-output form).
    (StderrSource.SSH_INFO, re.compile(r"^(?:<([^>]+)> )?rc="), True),
    # 8b. SSH return tuple (verbose form, when no_log is False).
    (StderrSource.SSH_INFO, re.compile(r"^(?:<([^>]+)> )?\(\d+, b'"), True),
    # 9. ControlPersist broken pipe (no host).
    (StderrSource.SSH_INFO, re.compile(r"^RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE"), False),
    # 10. Generic SSH: (vvvvv) — anything starting with "SSH: " that
    #     didn't match the more specific rules above. Host-prefixed.
    (StderrSource.SSH_DEBUG, re.compile(r"^(?:<([^>]+)> )?SSH: "), True),
    # 11. Connection lock messages.
    (
        StderrSource.CONNECTION,
        re.compile(
            r"^(?:<([^>]+)> )?CONNECTION: pid \d+ (?:waiting for|acquired|released) lock on \d+"
        ),
        True,
    ),
    # 12. Local connection establishment.
    (
        StderrSource.CONNECTION,
        re.compile(r"^(?:<([^>]+)> )?ESTABLISH LOCAL CONNECTION FOR USER:"),
        True,
    ),
    # 13. Local EXEC / PUT / FETCH.
    (
        StderrSource.CONNECTION,
        re.compile(r"^(?:<([^>]+)> )?(?:EXEC |PUT .* TO |FETCH .* TO )"),
        True,
    ),
    # 14. Persistent connection reset (host is NOT in text).
    (
        StderrSource.CONNECTION_LIFECYCLE,
        re.compile(r"^resetting persistent connection for socket_path"),
        False,
    ),
    (StderrSource.CONNECTION_LIFECYCLE, re.compile(r"^reset call on connection instance"), False),
    # 15. Callback plugin loading.
    (StderrSource.PLUGIN_LOADING, re.compile(r"^Loading callback plugin "), False),
    # 16. Inventory plugin setup.
    (StderrSource.PLUGIN_LOADING, re.compile(r"^setting up inventory plugins"), False),
    # 17. Inventory parsed.
    (StderrSource.INVENTORY, re.compile(r"^Parsed .* inventory source with .* plugin"), False),
    # 18. Inventory declined.
    (
        StderrSource.INVENTORY,
        re.compile(r"^.* declined parsing .* as it did not pass its verify_file"),
        False,
    ),
    # 19. Vault password prompts (interactive).
    (StderrSource.VAULT, re.compile(r"^Vault password"), False),
    (StderrSource.VAULT, re.compile(r"^New vault password"), False),
    # 20. Vault debug at vvvvv.
    (StderrSource.VAULT, re.compile(r"^Trying to use vault secret"), False),
    (StderrSource.VAULT, re.compile(r"^Encrypting with vault_id"), False),
    (StderrSource.VAULT, re.compile(r"^Decrypt.* successful with secret"), False),
    (StderrSource.VAULT, re.compile(r"^encrypt_vault_id="), False),
    (StderrSource.VAULT, re.compile(r"^Reading vault password file:"), False),
    (StderrSource.VAULT, re.compile(r"^The vault password file .* is a"), False),
    (StderrSource.VAULT, re.compile(r"^The password file .* is a script"), False),
    # 21. Become/SSH/sudo password prompts (interactive, distinct from vault).
    (StderrSource.PROMPT, re.compile(r"^(?:SSH|BECOME|sudo) password"), False),
    # 22. WorkerProcess warnings (host embedded in message body).
    (StderrSource.WARNING, re.compile(r"^\[WARNING\]: WorkerProcess for \["), False),
    # 23. Config file.
    (StderrSource.RUN_LEVEL, re.compile(r"^Using .* as config file"), False),
    (StderrSource.RUN_LEVEL, re.compile(r"^No config file found"), False),
    # 24. Play count.
    (StderrSource.RUN_LEVEL, re.compile(r"^\d+ plays in "), False),
    # 25. Collection playbook.
    (StderrSource.RUN_LEVEL, re.compile(r"^running playbook inside collection "), False),
    # 26. Retry file.
    (StderrSource.RUN_LEVEL, re.compile(r"^\tto retry, use:"), False),
    # 27. Syntax check OK.
    (StderrSource.RUN_LEVEL, re.compile(r"^No issues encountered"), False),
    # 28. Host pattern mismatch.
    (StderrSource.RUN_LEVEL, re.compile(r"^Could not match supplied host pattern"), False),
    # 29. Local current user detection.
    (StderrSource.RUN_LEVEL, re.compile(r"^Current user \(uid="), False),
    # 30. Plugin loading debug.
    (StderrSource.RUN_LEVEL, re.compile(r"^trying "), False),
    # 31. ansible.posix.profile_tasks callback banner. The timestamp prefix
    #     is locale-dependent (any day/month language), so anchor on the
    #     structurally-stable trailing portion: two ``(H:MM:SS.mmm)``-style
    #     durations followed by the ``*``-padded tail. ``.*`` tolerates the
    #     variable date prefix (classify uses ``re.match``, start-anchored).
    (
        StderrSource.RUN_LEVEL,
        _PROFILE_TASKS_BANNER_RE,
        False,
    ),
]


# Pattern that matches an empty line — no rule can match, but we want
# UNKNOWN, not to call into the regex engine for nothing.
_IS_BLANK = re.compile(r"^\s*$")


def classify(line: str) -> StderrEvent:
    """Classify a single stderr line into a :class:`StderrEvent`.

    Tries each rule in :data:`CLASSIFIER_RULES` order; first match wins.
    Host is extracted from a ``<hostname>`` prefix when the rule
    captures one (and the prefix is present). Lines that match no rule
    produce an :attr:`StderrSource.UNKNOWN` event with the original
    text preserved.

    The function is on the PTY hot path. It must never raise: any
    unexpected input produces an UNKNOWN event with host=None.

    Args:
        line: A single line from ansible-playbook's stderr. Caller is
            expected to have stripped ANSI SGR sequences already
            (see ``core.parser._ANSI_SGR_RE``).

    Returns:
        A :class:`StderrEvent` with the resolved source, optional host,
        level, and the original line text.
    """
    if not line or _IS_BLANK.match(line):
        return StderrEvent(
            source=StderrSource.UNKNOWN,
            host=None,
            level=LEVEL_MAP[StderrSource.UNKNOWN],
            line=line,
        )

    for source, regex, _has_host in CLASSIFIER_RULES:
        match = regex.match(line)
        if match is None:
            continue
        host: str | None = match.group(1) if match.lastindex else None
        return StderrEvent(
            source=source,
            host=host,
            level=LEVEL_MAP[source],
            line=line,
        )

    return StderrEvent(
        source=StderrSource.UNKNOWN,
        host=None,
        level=LEVEL_MAP[StderrSource.UNKNOWN],
        line=line,
    )
