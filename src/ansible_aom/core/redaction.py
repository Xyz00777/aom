"""Layered secret redaction system (QC-002 rewrite, Phase 2 / Task 2.1).

This module is the QC-002 hardened redaction. Layers (in order of priority):

- **Layer 0 (upstream contract):** ``res._ansible_no_log`` → entire result
  replaced with ``{"censored": "(no_log)"}``. Not an AOM layer — it is the
  ansible-core contract that we honor.
- **Layer 1 (AOM hard-coded, exact-match keys):** a frozen set of exact
  lowercased key names. Recurses into dicts/lists by KEY, never by value
  substring. Default set:
  ``password``, ``vault_password``, ``api_key``, ``private_key``, ``token``,
  ``secret``, ``passwd``, ``ssh_pass``.
- **Layer 2 (user-config, additive to Layer 1):**
  ``RedactionConfig.custom_fields`` (exact, case-insensitive) and
  ``RedactionConfig.custom_key_patterns`` (regex over lowercased keys).
- **Layer 3 (string sanitization, independent of key match):** URL
  credentials, CLI ``--password=xxx``-style args, and user-config regex
  patterns applied to string values in ``cmd``/``stdout``/``stderr``/``msg``.
- **Layer 4 (verbose-mode redaction):** ``res.invocation.module_args`` is
  passed through ``redact_dict`` (Layers 1+2).

The QC-002 bypass class fix: redaction recurses by **KEY**, not by value
substring. The previous PASSWORD_MATCH regex (kept here only as a backward-
compat constant) is no longer used for key matching; it was the bypass class
because it caught ``passenger_version`` (false positive) while missing cases
where the secret value sits in a field whose key does not contain
"password". The new model is exact-match + user-config regex, layered.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from ansible_aom.core.config import RedactionConfig

# =============================================================================
# Constants
# =============================================================================

# Layer 1: hard-coded exact-match keys. Frozen — this is a public contract
# (see ``tests/unit/test_redaction_layer4.py::test_qc002_exact_match_keys_frozenset_contents``).
EXACT_MATCH_SECRET_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "vault_password",
        "api_key",
        "private_key",
        "token",
        "secret",
        "passwd",
        "ssh_pass",
    }
)

# Default passphrase-style whitelist. These keys historically matched the
# old PASSWORD_MATCH regex and were common false positives. They are
# unconditionally NOT redacted by Layer 1.
DEFAULT_PASSPHRASE_WHITELIST: frozenset[str] = frozenset(
    {
        "passenger_version",
        "passenger_pool",
        "bypass",
        "overpass",
        "compass",
        "underpass",
        "passport_number",
    }
)

# Backward-compat aliases (frozen exports; no longer used by the core
# redaction logic). Kept so existing test modules and downstream callers
# that imported these by name still resolve. See
# ``tests/unit/test_redaction.py``.
PASSWORD_WHITELIST: frozenset[str] = DEFAULT_PASSPHRASE_WHITELIST
PASSWORD_MATCH: re.Pattern[str] = re.compile(
    r"^(?:.+[-_\s])?pass(?:[-_\s]?(?:word|phrase|wrd|wd))?(?:[-_\s].+)?$",
    re.IGNORECASE,
)
ANSIBLE_PASSWORD_FIELDS: frozenset[str] = frozenset(
    {
        "ansible_ssh_pass",
        "ansible_password",
        "ansible_become_pass",
        "ansible_become_password",
        "ansible_vault_password",
    }
)
GENERIC_SECRET_FIELDS: frozenset[str] = frozenset(
    {
        "api_key",
        "api_token",
        "secret",
        "secret_key",
        "token",
        "auth_token",
        "access_token",
        "private_key",
        "credential",
        "credentials",
    }
)

URL_CRED_PATTERN: re.Pattern[str] = re.compile(r"([a-zA-Z]+://[^:]+:)([^@]+)(@)")
CLI_CRED_PATTERN: re.Pattern[str] = re.compile(
    r"(--(?:password|pass|pwd|token|secret|key|api-key)\s*[=: ]+)\S+",
    re.IGNORECASE,
)

REDACTED: str = "********"
_MAX_DEPTH: int = 10


# =============================================================================
# Layer 1 + Layer 2: KEY matching
# =============================================================================


def _lower_set(items: list[str]) -> frozenset[str]:
    return frozenset(item.lower() for item in items)


def should_redact(key: str, config: RedactionConfig) -> bool:
    """Decide whether a dict KEY should be redacted by Layers 1+2.

    Order of checks (whitelist first — short-circuits the rest):

    1. ``key.lower()`` in :data:`DEFAULT_PASSPHRASE_WHITELIST` → ``False``.
    2. ``key.lower()`` in ``config.whitelist`` (lowercased) → ``False``.
    3. ``key.lower()`` in :data:`EXACT_MATCH_SECRET_KEYS` → ``True``
       (Layer 1).
    4. ``key.lower()`` in ``config.custom_fields`` (lowercased) → ``True``
       (Layer 2).
    5. Any ``config.custom_key_patterns`` regex matches ``key.lower()``
       → ``True`` (Layer 2). Invalid regexes are silently skipped.
    6. Otherwise → ``False``.

    The old PASSWORD_MATCH regex is **not** consulted here. The bypass class
    QC-002 closed was a PASSWORD_MATCH false-positive on ``passenger_version``
    coupled with value-substring matching in nested structures.
    """
    key_lower = key.lower()

    if key_lower in DEFAULT_PASSPHRASE_WHITELIST:
        return False
    if key_lower in _lower_set(config.whitelist):
        return False

    if key_lower in EXACT_MATCH_SECRET_KEYS:
        return True
    if key_lower in _lower_set(config.custom_fields):
        return True

    for pattern_str in config.custom_key_patterns:
        try:
            if re.search(pattern_str, key_lower):
                return True
        except re.error:
            continue

    return False


# =============================================================================
# Layer 3: string sanitization
# =============================================================================


def sanitize_string(s: str, config: RedactionConfig) -> str:
    """Sanitize credentials in a single string (Layer 3).

    Applies in order:
    1. :data:`URL_CRED_PATTERN` — redacts ``user:pass@`` in URLs.
    2. :data:`CLI_CRED_PATTERN` — redacts ``--password=xxx`` style args.
    3. ``config.custom_patterns`` — user regex on values.

    Layer 3 is independent of Layers 1+2: it inspects *string content* and
    is not bypassed by key look-alikes. It is the only layer that touches
    values.
    """
    if not isinstance(s, str):
        return s

    result = URL_CRED_PATTERN.sub(rf"\g<1>{REDACTED}\g<3>", s)
    result = CLI_CRED_PATTERN.sub(rf"\g<1>{REDACTED}", result)

    for pattern_dict in config.custom_patterns:
        regex_str = pattern_dict.get("regex", "")
        replacement = pattern_dict.get("replacement", REDACTED)
        if not regex_str:
            continue
        try:
            custom_pattern = re.compile(regex_str)
        except re.error:
            continue
        result = custom_pattern.sub(replacement, result)

    return result


# =============================================================================
# Recursive dict/list redaction (Layers 1+2 by KEY)
# =============================================================================


def redact_dict(data: dict, config: RedactionConfig, depth: int = 0) -> dict:
    """Recursively redact by KEY (Layers 1+2). Returns a new dict.

    The recursion is bounded at :data:`_MAX_DEPTH` to defend against
    adversarial deeply-nested input. The bypass class fix means values are
    never inspected for substring matches here; only keys.
    """
    if depth >= _MAX_DEPTH:
        return deepcopy(data)

    result: dict = deepcopy(data)
    for key, value in result.items():
        if should_redact(key, config):
            result[key] = REDACTED
        elif isinstance(value, dict):
            result[key] = redact_dict(value, config, depth + 1)
        elif isinstance(value, list):
            result[key] = _redact_list(value, config, depth + 1)

    return result


def _redact_list(lst: list, config: RedactionConfig, depth: int) -> list:
    """Redact items within a list, recursing on dict items and sanitizing strings.

    Note: only the dict-items branch triggers Layer 1+2 redaction. Strings in
    a list are *not* automatically sanitized — that is Layer 3's job and
    happens in :func:`redact_event` on the well-known ``cmd``/``stdout``/
    ``stderr``/``msg`` fields. List-of-strings without a key context is not
    a redaction target (you cannot tell which "key" a bare string belongs
    to).
    """
    result: list[Any] = []
    for item in lst:
        if isinstance(item, dict):
            result.append(redact_dict(item, config, depth))
        elif isinstance(item, list):
            result.append(_redact_list(item, config, depth + 1))
        else:
            result.append(item)
    return result


# =============================================================================
# Layer 0 + 1+2 + 3 + 4: full event redaction
# =============================================================================


def redact_event(event: dict, config: RedactionConfig) -> dict:
    """Apply all redaction layers to an event dict. Returns a new event.

    Layer order:

    - **Layer 0** — ``res._ansible_no_log`` flag: replace whole result with
      ``{"censored": "(no_log)"}`` (also applied per-loop-item).
    - **Layer 1+2** — :func:`redact_dict` over ``res`` and (separately) over
      ``res.invocation.module_args`` (Layer 4). Recurses by KEY.
    - **Layer 3** — :func:`sanitize_string` on the well-known string fields
      ``cmd``, ``stdout``, ``stderr``, ``msg`` in ``res``.

    The wired-in call site is the responsibility of Task 2.2 (event pipeline
    integration). This function is the pure transformation; nothing in
    ``core/`` calls it yet.
    """
    result = deepcopy(event)
    if "res" not in result:
        result["res"] = {}
    res = result["res"]

    # Layer 0: _ansible_no_log flag.
    if res.get("_ansible_no_log") is True:
        result["res"] = {"censored": "(no_log)"}
        return result

    if "results" in res and isinstance(res["results"], list):
        for i, item in enumerate(res["results"]):
            if isinstance(item, dict) and item.get("_ansible_no_log") is True:
                res["results"][i] = {"censored": "(no_log)"}

    # Layer 1+2: recursive key-based redaction.
    result["res"] = redact_dict(res, config)
    res = result["res"]

    # Layer 3: string sanitization on well-known string fields.
    if "cmd" in res:
        if isinstance(res["cmd"], list):
            res["cmd"] = [
                sanitize_string(item, config) if isinstance(item, str) else item
                for item in res["cmd"]
            ]
        elif isinstance(res["cmd"], str):
            res["cmd"] = sanitize_string(res["cmd"], config)

    for field in ("stdout", "stderr", "msg"):
        if field in res and isinstance(res[field], str):
            res[field] = sanitize_string(res[field], config)

    # Layer 4: invocation.module_args (verbose mode).
    if "invocation" in res and isinstance(res["invocation"], dict):
        invocation = res["invocation"]
        if "module_args" in invocation and isinstance(invocation["module_args"], dict):
            invocation["module_args"] = redact_dict(invocation["module_args"], config)

    return result
