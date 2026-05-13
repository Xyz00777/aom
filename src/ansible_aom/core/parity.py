"""Reduce a ``RunState`` into a renderer-agnostic dict.

This is the canonical "what should every renderer agree on?" view of
a finished run: per-host status counts, totals, the exit code the
state implies, and the play/task tallies the renderers used to
populate their headers.

Used by parity tests (compact vs JSON vs TUI must produce identical
reduced state for the same event stream) but kept in ``core/`` because
the reduction is pure logic over the dataclass — no I/O, no imports
from any renderer — and the same shape is useful for any future
non-test consumer that needs a structural summary (e.g. a hypothetical
``aom inspect summary --json`` view).
"""

from __future__ import annotations

from typing import Any

from ansible_aom.core.models import RunState, Status

_PER_HOST_KEYS: tuple[str, ...] = (
    "ok",
    "changed",
    "failed",
    "unreachable",
    "skipped",
    "rescued",
    "ignored",
)


def _empty_host_counts() -> dict[str, int]:
    return dict.fromkeys(_PER_HOST_KEYS, 0)


def reduce_state_for_parity(state: RunState) -> dict[str, Any]:
    """Project ``state`` into a renderer-agnostic dict.

    Shape::

        {
          "hosts": {
            "<host>": {ok, changed, failed, unreachable, skipped,
                       rescued, ignored},
            ...
          },
          "totals": {ok, changed, failed, unreachable, skipped,
                     rescued, ignored},
          "exit_code": int,
          "n_plays": int,
          "n_tasks": int,
        }

    Counter semantics — each (host, task) result contributes exactly
    one increment to the host's bucket and the matching totals bucket:

    * ``Status.OK`` → ``ok``
    * ``Status.CHANGED`` → ``changed`` (NOT also ``ok``; CHANGED
      already implies the task ran cleanly, so double-counting would
      diverge from ansible's own ``v2_playbook_on_stats`` semantics
      which set ``ok`` and ``changed`` independently)
    * ``Status.FAILED`` → ``failed``
    * ``Status.UNREACHABLE`` → ``unreachable``
    * ``Status.SKIPPED`` → ``skipped``

    The ``rescued`` and ``ignored`` keys are part of the shape for
    forward-compatibility with ansible's stats schema — RunState
    doesn't yet track them, so they're always 0.

    ``exit_code`` is computed from the state directly (rather than
    taken from the renderer) so a renderer that mishandles the
    completion callback can't hide a state-vs-exit disagreement.
    Mirrors ``determine_exit_code`` in ``compact/renderer.py``: a
    duplicate is acceptable here because ``core/`` is forbidden from
    importing from ``compact/``, and the logic is two short scans.
    """
    hosts: dict[str, dict[str, int]] = {}
    totals: dict[str, int] = _empty_host_counts()
    n_tasks = 0

    for play in state.plays.values():
        for task in play.tasks.values():
            n_tasks += 1
            for hostname, host_state in task.hosts.items():
                bucket = hosts.setdefault(hostname, _empty_host_counts())
                key: str | None = None
                if host_state.status == Status.OK:
                    key = "ok"
                elif host_state.status == Status.CHANGED:
                    key = "changed"
                elif host_state.status == Status.FAILED:
                    key = "failed"
                elif host_state.status == Status.UNREACHABLE:
                    key = "unreachable"
                elif host_state.status == Status.SKIPPED:
                    key = "skipped"
                if key is not None:
                    bucket[key] += 1
                    totals[key] += 1

    exit_code = 0
    any_failed = False
    any_unreachable = False
    for play in state.plays.values():
        for task in play.tasks.values():
            for host_state in task.hosts.values():
                if host_state.status == Status.FAILED:
                    any_failed = True
                elif host_state.status == Status.UNREACHABLE:
                    any_unreachable = True
    if any_failed:
        exit_code = 1
    elif any_unreachable:
        exit_code = 2

    return {
        "hosts": hosts,
        "totals": totals,
        "exit_code": exit_code,
        "n_plays": len(state.plays),
        "n_tasks": n_tasks,
    }
