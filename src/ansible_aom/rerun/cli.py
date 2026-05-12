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


from ansible_aom.core.session import (  # noqa: E402
    collect_changed_hosts,
    collect_failed_hosts,
    collect_unreachable_hosts,
)


def _compose_host_set(
    session: dict,
    *,
    failed: bool,
    unreachable: bool,
    changes_only: bool,
) -> set[str]:
    """Combine the requested host categories into a single set.

    Semantics (from the F4 spec):
    - No flag → behave like ``--failed`` (the most common case).
    - ``--unreachable`` is a strict *superset* of ``--failed``: hosts
      that failed AND hosts that were unreachable. We never return only
      unreachable hosts on its own.
    - ``--changes-only`` adds hosts whose tasks reported ``changed: true``.
    - Multiple flags compose by union.

    Args:
        session: Loaded session dict (from ``load_session``).
        failed: Include hosts that hit ``v2_runner_on_failed``.
        unreachable: Include hosts from both failed AND unreachable.
        changes_only: Include hosts that had at least one changed task.

    Returns:
        Union of the requested host categories.
    """
    if not failed and not unreachable and not changes_only:
        # Default behaviour matches `--failed` so the bare command does
        # the most common thing.
        return collect_failed_hosts(session)

    hosts: set[str] = set()
    if failed:
        hosts |= collect_failed_hosts(session)
    if unreachable:
        # --unreachable means "everything to retry": failed ∪ unreachable.
        hosts |= collect_failed_hosts(session)
        hosts |= collect_unreachable_hosts(session)
    if changes_only:
        hosts |= collect_changed_hosts(session)
    return hosts
