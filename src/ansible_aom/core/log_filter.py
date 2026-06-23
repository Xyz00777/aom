"""Pure helpers for the compact-mode --hide-state filter."""

from __future__ import annotations

from collections.abc import Iterable

VALID_STATES: frozenset[str] = frozenset({"ok", "changed", "failed", "skipped", "unreachable"})

# Maps JSONL event type strings to the set of user-visible state names they
# represent.  ``v2_runner_on_ok`` and ``v2_runner_item_on_ok`` cover both
# "ok" and "changed" because ansible emits the same event type for both —
# the distinction lives inside the host result dict's ``changed`` field.
_EVENT_STATE_MAP: dict[str, frozenset[str]] = {
    "v2_runner_on_ok": frozenset({"ok", "changed"}),
    "v2_runner_on_failed": frozenset({"failed"}),
    "v2_runner_on_unreachable": frozenset({"unreachable"}),
    "v2_runner_on_skipped": frozenset({"skipped"}),
    "v2_runner_item_on_ok": frozenset({"ok", "changed"}),
    "v2_runner_item_on_failed": frozenset({"failed"}),
    "v2_runner_item_on_skipped": frozenset({"skipped"}),
}


def normalize_hide_states(values: Iterable[str]) -> tuple[frozenset[str], list[str]]:
    """Lowercase, deduplicate, validate, and separate unknown inputs.

    Args:
        values: Raw user-supplied state names (e.g. ``["ok", "OK", "Skipped"]``).

    Returns:
        ``(valid_set, unknown_list)`` — both always returned.
        ``valid_set``: frozenset of lowercase known state names.
        ``unknown_list``: list of values that did not match any ``VALID_STATES`` entry,
        in the order they were first encountered.
    """
    seen_valid: set[str] = set()
    unknown: list[str] = []
    seen_unknown: set[str] = set()

    for raw in values:
        lowered = raw.lower()
        if lowered in VALID_STATES:
            seen_valid.add(lowered)
        elif lowered not in seen_unknown:
            seen_unknown.add(lowered)
            unknown.append(raw)

    return frozenset(seen_valid), unknown


def should_hide_event(event_type: str, hide_states: frozenset[str]) -> bool:
    """True iff the given JSONL event type should be suppressed from the live log.

    Maps JSONL event type strings to their user-visible state names:

    * ``v2_runner_on_ok`` → ``ok`` / ``changed``
    * ``v2_runner_on_failed`` → ``failed``
    * ``v2_runner_on_unreachable`` → ``unreachable``
    * ``v2_runner_on_skipped`` → ``skipped``
    * ``v2_runner_item_on_ok`` → ``ok`` / ``changed``
    * ``v2_runner_item_on_failed`` → ``failed``
    * ``v2_runner_item_on_skipped`` → ``skipped``

    Non-runner event types (``v2_playbook_on_*``, ``v2_playbook_on_stats``, etc.)
    always return ``False`` — they are never hidden.

    .. warning::

       For ``v2_runner_on_ok`` and ``v2_runner_item_on_ok``, this function
       returns ``True`` if **any** of the event's possible states (ok or
       changed) is hidden. This is too coarse for per-host filtering because
       a single event may contain hosts with ``changed=True`` alongside hosts
       with ``changed=False``. Use :func:`should_hide_host_result` for
       per-host granularity on those event types.

    Args:
        event_type: The ``_event`` field value from a JSONL event dict.
        hide_states: A frozenset of lowercase state names to suppress.

    Returns:
        ``True`` if a per-host result line for this event should be suppressed.
    """
    states = _EVENT_STATE_MAP.get(event_type)
    if states is None:
        return False
    return not states.isdisjoint(hide_states)


def should_hide_host_result(
    result: dict, event_type: str, hide_states: frozenset[str]
) -> bool:
    """True iff a single host's result should be suppressed from the live log.

    Unlike :func:`should_hide_event` which operates at the event level and
    conflates ``ok`` and ``changed`` (because ``v2_runner_on_ok`` covers
    both), this function inspects the per-host ``result`` dict to determine
    the specific state for that host:

    * ``v2_runner_on_ok`` / ``v2_runner_item_on_ok``:
      ``result.get("changed", False)`` is the authoritative signal.
      ``True`` → ``"changed"``, ``False`` → ``"ok"``.
    * ``v2_runner_on_failed`` / ``v2_runner_item_on_failed`` → ``"failed"``
    * ``v2_runner_on_unreachable`` → ``"unreachable"``
    * ``v2_runner_on_skipped`` / ``v2_runner_item_on_skipped`` → ``"skipped"``
    * Any other event type → ``False`` (never hidden).

    Args:
        result: The per-host result dict from the JSONL ``hosts`` mapping.
        event_type: The ``_event`` field value from the JSONL event.
        hide_states: A frozenset of lowercase state names to suppress.

    Returns:
        ``True`` if this host's result line should be suppressed.
    """
    if event_type in ("v2_runner_on_ok", "v2_runner_item_on_ok"):
        state = "changed" if result.get("changed", False) else "ok"
        return state in hide_states
    if event_type in ("v2_runner_on_failed", "v2_runner_item_on_failed"):
        return "failed" in hide_states
    if event_type == "v2_runner_on_unreachable":
        return "unreachable" in hide_states
    if event_type in ("v2_runner_on_skipped", "v2_runner_item_on_skipped"):
        return "skipped" in hide_states
    return False
