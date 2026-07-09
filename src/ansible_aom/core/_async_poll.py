"""Async-poll payload detection — shared between compact renderer and inspect model.

Ansible-core sometimes delivers an async-poll result via
``v2_runner_item_on_failed`` or ``v2_runner_item_on_ok`` when the
connection drops during polling. The payload has ``ansible_job_id``/
``started``/``attempts``/``finished`` but no ``_ansible_item_label``
and no ``item`` field — it is NOT a real loop item.

This module lives in ``core/`` so both ``compact/`` and ``core/``
modules can import it without violating the layering rule (``core/``
must never import from ``compact/``, ``tui/``, or ``renderer/``).
"""


def is_async_poll_payload(raw: dict) -> bool:
    """Detect an async-poll bookkeeping payload (not a real loop item).

    Returns ``True`` when the dict looks like async bookkeeping.
    """
    return "ansible_job_id" in raw and "_ansible_item_label" not in raw and "item" not in raw
