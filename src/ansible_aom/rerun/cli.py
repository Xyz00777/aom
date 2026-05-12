"""CLI entry point for ``aom rerun``.

Reads a recorded session, derives a host list from failures /
unreachable / changes, and re-invokes ``ansible-playbook`` with the
original args plus a ``--limit`` matching the derived hosts.

The only piece in this file that's not pure-CLI plumbing is host-set
composition; the actual set computation lives in ``core.session``
(``collect_failed_hosts`` etc.) so it stays testable in isolation
and ``core/`` keeps its no-renderer rule.
"""

from __future__ import annotations

from pathlib import Path

from ansible_aom.core.session import list_sessions


def _resolve_session_id(state_dir: Path, session_id_or_short: str | None) -> str:
    """Resolve an explicit session ID, short prefix, or "most recent" intent.

    Mirrors the inspect command's resolution semantics: full UUID wins
    over prefix match, prefix match must be unique, "no argument" picks
    the most recent session by start_time.

    Args:
        state_dir: Directory containing session sub-directories.
        session_id_or_short: Either a full 36-char UUID, an 8-char (or
            longer) prefix, or ``None`` to pick the latest session.

    Returns:
        The resolved full session ID.

    Raises:
        LookupError: When no session matches, no sessions exist at all,
            or a short prefix matches more than one session.
    """
    sessions = list_sessions(state_dir)
    if not sessions:
        raise LookupError(f"No sessions found in {state_dir}")

    if session_id_or_short is None:
        # list_sessions returns newest-first.
        return sessions[0]["session_id"]

    # Exact full-id match wins.
    for s in sessions:
        if s["session_id"] == session_id_or_short:
            return session_id_or_short

    # Otherwise treat as prefix.
    matches = [s for s in sessions if s["session_id"].startswith(session_id_or_short)]
    if not matches:
        raise LookupError(f"No session matching {session_id_or_short!r} in {state_dir}")
    if len(matches) > 1:
        ids = ", ".join(s["session_id"] for s in matches)
        raise LookupError(f"Prefix {session_id_or_short!r} is ambiguous: matches {ids}")
    return matches[0]["session_id"]
