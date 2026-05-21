"""Pure post-mortem projections of a loaded session.

These functions take a session dict (as returned by
:func:`ansible_aom.session.store.load_session`) and project it into the
shapes the CLI tools (``aom inspect`` summary, ``aom rerun`` host
filters) need. No I/O — given the same input, they always produce the
same output.

Layered above :mod:`ansible_aom.session.store` so that any other
consumer of recorded sessions (HTTP API, batch analytics, …) can call
these without dragging in the storage layer.
"""

from __future__ import annotations

from typing import Any


def create_session_summary(session: dict[str, Any]) -> dict[str, Any]:
    """Create a human-readable summary of a session.

    Args:
        session: Session dictionary from ``load_session``

    Returns:
        Summary dictionary with key session information.
    """
    summary = {
        "session_id": session.get("session_id", ""),
        "playbook": session.get("playbook", ""),
        "status": session.get("status", ""),
        "start_time": session.get("start_time", ""),
        "end_time": session.get("end_time"),
        "duration_seconds": session.get("duration_seconds"),
        "malformed_lines": session.get("malformed_lines", 0),
        "event_count": len(session.get("events", [])),
    }

    if summary.get("malformed_lines", 0) > 0:
        summary["summary_note"] = f"{summary['malformed_lines']} malformed lines"

    return summary


def collect_failed_hosts(session: dict[str, Any]) -> set[str]:
    """Return the set of hostnames that hit ``v2_runner_on_failed`` in this session.

    Pure: takes a session dict (as returned by ``load_session``) and
    returns the deduplicated set of failed hostnames. No I/O. Used by
    ``aom rerun --failed`` to build the ``--limit`` argument for the
    re-invoked ansible-playbook.

    Multi-host failure events are flattened: a single
    ``v2_runner_on_failed`` carrying ``{"web2": ..., "web3": ...}`` adds
    both names. A host that fails in multiple tasks contributes one
    entry only.

    Args:
        session: Session dict from ``load_session`` (or any dict with an
            ``events`` list of JSONL event dicts). Sessions without an
            ``events`` key return an empty set.

    Returns:
        Set of hostname strings.
    """
    failed: set[str] = set()
    for event in session.get("events", []):
        if event.get("_event") != "v2_runner_on_failed":
            continue
        hosts = event.get("hosts") or {}
        for hostname in hosts.keys():
            failed.add(hostname)
    return failed


def collect_unreachable_hosts(session: dict[str, Any]) -> set[str]:
    """Return the set of hostnames that hit ``v2_runner_on_unreachable``.

    Pure: same shape as ``collect_failed_hosts`` but watches a different
    event type. Used by ``aom rerun --unreachable`` to build the
    ``--limit`` argument; the CLI composes
    ``collect_failed_hosts() | collect_unreachable_hosts()`` because
    "things to retry" is the union, never just unreachable.

    Args:
        session: Session dict from ``load_session``. Sessions without an
            ``events`` key return an empty set.

    Returns:
        Set of hostname strings.
    """
    unreachable: set[str] = set()
    for event in session.get("events", []):
        if event.get("_event") != "v2_runner_on_unreachable":
            continue
        hosts = event.get("hosts") or {}
        for hostname in hosts.keys():
            unreachable.add(hostname)
    return unreachable


def collect_changed_hosts(session: dict[str, Any]) -> set[str]:
    """Return the set of hostnames that had at least one changed task.

    Pure: scans ``v2_runner_on_ok`` events and selects host entries
    whose per-host result dict has ``changed`` truthy. Powers
    ``aom rerun --changes-only`` for idempotency verification.

    Args:
        session: Session dict from ``load_session``. Sessions without an
            ``events`` key return an empty set.

    Returns:
        Set of hostname strings.
    """
    changed: set[str] = set()
    for event in session.get("events", []):
        if event.get("_event") != "v2_runner_on_ok":
            continue
        hosts = event.get("hosts") or {}
        for hostname, result in hosts.items():
            if isinstance(result, dict) and result.get("changed"):
                changed.add(hostname)
    return changed
