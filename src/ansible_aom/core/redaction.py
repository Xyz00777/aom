"""4-layer secret redaction system for Ansible output.

This module implements the redaction system defined in SPECIFICATION.md Section 5.9.

Layers:
1. _ansible_no_log flag: Replace entire result dict with {"censored": "(no_log)"}
2. Password field redaction: Recursively redact password-like keys in dicts/lists
3. String sanitization: Strip credentials from cmd, stdout, stderr, msg fields
4. invocation.module_args: Recursive redaction of module arguments
"""

import re
from copy import deepcopy
from typing import Any

from ansible_aom.core.config import RedactionConfig

# =============================================================================
# Constants (from SPECIFICATION.md Section 5.9)
# =============================================================================

PASSWORD_MATCH = re.compile(
    r"^(?:.+[-_\s])?pass(?:[-_\s]?(?:word|phrase|wrd|wd))?(?:[-_\s].+)?$",
    re.IGNORECASE,
)

ANSIBLE_PASSWORD_FIELDS = frozenset(
    {
        "ansible_ssh_pass",
        "ansible_password",
        "ansible_become_pass",
        "ansible_become_password",
        "ansible_vault_password",
    }
)

GENERIC_SECRET_FIELDS = frozenset(
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

PASSWORD_WHITELIST = frozenset(
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

URL_CRED_PATTERN = re.compile(r"([a-zA-Z]+://[^:]+:)([^@]+)(@)")

CLI_CRED_PATTERN = re.compile(
    r"(--(?:password|pass|pwd|token|secret|key|api-key)\s*[=: ]+)\S+",
    re.IGNORECASE,
)

REDACTED = "********"
_MAX_DEPTH = 10


# =============================================================================
# Functions
# =============================================================================


def should_redact(key: str, config: RedactionConfig) -> bool:
    """Return True if field should be redacted.

    A field should be redacted if:
    - key.lower() is in ANSIBLE_PASSWORD_FIELDS
    - key.lower() is in GENERIC_SECRET_FIELDS
    - key.lower() is in config.custom_fields (lowercased)
    - PASSWORD_MATCH matches key.lower() AND key is not in whitelist

    Args:
        key: The field name to check
        config: RedactionConfig with whitelist and custom_fields

    Returns:
        True if the field should be redacted, False otherwise
    """
    key_lower = key.lower()

    # Check if in ansible password fields
    if key_lower in ANSIBLE_PASSWORD_FIELDS:
        return True

    # Check if in generic secret fields
    if key_lower in GENERIC_SECRET_FIELDS:
        return True

    # Check if in custom fields (case-insensitive)
    custom_fields_lower = {f.lower() for f in config.custom_fields}
    if key_lower in custom_fields_lower:
        return True

    # Check PASSWORD_MATCH pattern, but exclude whitelist
    if PASSWORD_MATCH.match(key_lower):
        # Build combined whitelist (default + config)
        whitelist_lower = {w.lower() for w in PASSWORD_WHITELIST}
        config_whitelist_lower = {w.lower() for w in config.whitelist}
        combined_whitelist = whitelist_lower | config_whitelist_lower

        if key_lower not in combined_whitelist:
            return True

    return False


def sanitize_string(s: str, config: RedactionConfig) -> str:
    """Sanitize credentials in a single string using Layer 3 patterns.

    Applies patterns in order:
    1. URL_CRED_PATTERN: redacts user:pass@ in URLs
    2. CLI_CRED_PATTERN: redacts --password=xxx style args
    3. config.custom_patterns: custom regex patterns

    Args:
        s: String to sanitize
        config: RedactionConfig with custom_patterns

    Returns:
        Sanitized string with credentials replaced by REDACTED
    """
    if not isinstance(s, str):
        return s

    # Apply URL credential pattern
    result = URL_CRED_PATTERN.sub(r"\1********\3", s)

    # Apply CLI credential pattern
    result = CLI_CRED_PATTERN.sub(r"\1********", result)

    # Apply custom patterns
    for pattern_dict in config.custom_patterns:
        regex_str = pattern_dict.get("regex", "")
        replacement = pattern_dict.get("replacement", REDACTED)
        if regex_str:
            try:
                custom_pattern = re.compile(regex_str)
                result = custom_pattern.sub(replacement, result)
            except re.error:
                # Invalid regex, skip this pattern
                pass

    return result


def redact_dict(data: dict, config: RedactionConfig, depth: int = 0) -> dict:
    """Recursively redact a dict (Layer 2). Returns a new dict.

    Args:
        data: Dict to redact
        config: RedactionConfig with whitelist and custom_fields
        depth: Current recursion depth (stops at _MAX_DEPTH)

    Returns:
        Deep copy of data with password values redacted
    """
    if depth >= _MAX_DEPTH:
        return deepcopy(data)

    result = deepcopy(data)

    for key, value in result.items():
        if should_redact(key, config):
            result[key] = REDACTED
        elif isinstance(value, dict):
            result[key] = redact_dict(value, config, depth + 1)
        elif isinstance(value, list):
            result[key] = _redact_list(value, config, depth + 1)
        # Non-dict/list values are left alone if key doesn't match

    return result


def _redact_list(lst: list, config: RedactionConfig, depth: int) -> list:
    """Redact items within a list, recursing on dict items.

    Args:
        lst: List to process
        config: RedactionConfig
        depth: Current recursion depth

    Returns:
        New list with redacted dict items and sanitized strings
    """
    result: list[Any] = []
    for item in lst:
        if isinstance(item, dict):
            result.append(redact_dict(item, config, depth))
        elif isinstance(item, list):
            result.append(_redact_list(item, config, depth + 1))
        elif isinstance(item, str):
            # Sanitize strings in lists
            result.append(sanitize_string(item, config))
        else:
            result.append(item)
    return result


def redact_event(event: dict, config: RedactionConfig) -> dict:
    """Apply all 4 redaction layers to an event dict. Returns a new event.

    Layer order:
    1. _ansible_no_log: Replace entire result dict if flag is True
    2. Password field redaction: Redact matching keys in event["res"]
    3. String sanitization: Sanitize cmd, stdout, stderr, msg fields
    4. invocation.module_args: Recursive redaction of module arguments

    Args:
        event: Ansible event dict
        config: RedactionConfig

    Returns:
        Deep copy of event with all layers applied
    """
    result = deepcopy(event)

    # Ensure "res" exists
    if "res" not in result:
        result["res"] = {}

    res = result["res"]

    # Layer 1: _ansible_no_log flag handling
    if res.get("_ansible_no_log") is True:
        result["res"] = {"censored": "(no_log)"}
        return result

    # Handle loop results (items with individual _ansible_no_log flags)
    if "results" in res and isinstance(res["results"], list):
        for i, item in enumerate(res["results"]):
            if isinstance(item, dict) and item.get("_ansible_no_log") is True:
                res["results"][i] = {"censored": "(no_log)"}

    # Layer 2: Password field redaction (recursive)
    result["res"] = redact_dict(res, config)

    # Layer 3: String sanitization for specific fields
    res = result["res"]  # Re-fetch after Layer 2

    # cmd field (may be list of strings or single string)
    if "cmd" in res:
        if isinstance(res["cmd"], list):
            res["cmd"] = [
                sanitize_string(item, config) if isinstance(item, str) else item
                for item in res["cmd"]
            ]
        elif isinstance(res["cmd"], str):
            res["cmd"] = sanitize_string(res["cmd"], config)

    # stdout field
    if "stdout" in res and isinstance(res["stdout"], str):
        res["stdout"] = sanitize_string(res["stdout"], config)

    # stderr field
    if "stderr" in res and isinstance(res["stderr"], str):
        res["stderr"] = sanitize_string(res["stderr"], config)

    # msg field
    if "msg" in res and isinstance(res["msg"], str):
        res["msg"] = sanitize_string(res["msg"], config)

    # Layer 4: invocation.module_args redaction
    if "invocation" in res and isinstance(res["invocation"], dict):
        invocation = res["invocation"]
        if "module_args" in invocation and isinstance(invocation["module_args"], dict):
            invocation["module_args"] = redact_dict(invocation["module_args"], config)

    return result
