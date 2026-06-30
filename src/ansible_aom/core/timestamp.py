"""Canonical ISO 8601 timestamp parsing for ansible-playbook JSONL events.

AOM reads timestamps emitted by ``ansible.posix.jsonl`` which uses the
ISO 8601 ``Z`` suffix to denote UTC (``2025-01-15T12:34:56.789012Z``).
Python's :func:`datetime.fromisoformat` accepts ``Z`` natively from
3.11 onward, but the canonical AOM parser normalises the suffix
explicitly to ``+00:00`` so it works against older CPython and remains
defensive against future parser changes.

All timestamp-parsing call sites in AOM funnel through
:func:`parse_iso_timestamp` so the normalisation lives in exactly one
place. See ARCHITECTURE.md §7 (consolidation of the 9C series of
duplications).
"""

from __future__ import annotations

from datetime import datetime


def parse_iso_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 timestamp string, tolerating the ``Z`` UTC suffix.

    Args:
        value: ISO 8601 timestamp. The trailing ``Z`` is replaced with
            ``+00:00`` before parsing, so the returned ``datetime`` is
            timezone-aware (UTC) for any ``Z``-terminated input.

    Returns:
        A timezone-aware :class:`datetime` when ``value`` includes a
        timezone designator (or the ``Z`` shorthand). A naive
        ``datetime`` is returned when ``value`` has no offset.

    Raises:
        ValueError: ``value`` is not a valid ISO 8601 timestamp.
        TypeError: ``value`` is not coercible to ``str`` (defensive
            guard against the ``datetime.fromisoformat`` behaviour when
            passed ``None`` or other non-string types).
    """
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
