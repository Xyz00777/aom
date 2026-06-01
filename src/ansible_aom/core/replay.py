"""Deterministic replay helpers for frame-by-frame tree capture.

These helpers stay pure: they mutate only the supplied ``RunState`` and
derive tree frames from it with a persistent ``TreeProjection`` so
projection-local state (like sticky play selection) survives across
successive events.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import datetime
from typing import Any

from ansible_aom.core.models import RunState
from ansible_aom.core.tree import TreeLine, TreeProjection


def _event_timestamp(event: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(event["_timestamp"].replace("Z", "+00:00"))


def iter_tree_frames(
    playbook: str,
    events: Iterable[dict[str, Any]],
    *,
    budget: int = 999,
) -> Iterator[list[TreeLine]]:
    """Yield a tree frame after each JSONL event.

    The same ``TreeProjection`` instance is reused for the whole replay so
    projection-local continuity state is preserved exactly as the renderer
    would see it.
    """

    state = RunState(playbook=playbook)
    projection = TreeProjection.from_run_state(state)
    for event in events:
        state.handle_event(event)
        yield projection.tree_lines(budget=budget, now=_event_timestamp(event))
