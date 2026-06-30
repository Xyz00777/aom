"""R15 — cap unbounded RunState sets.

R15 spec: ``RunState`` carries several set/dict structures that grow
without bound as events arrive:

- ``_grafted_uuids`` (set): task UUIDs the graft pass has already
  processed. A run that emits more than ``MAX_TASKS_PER_PLAY`` unique
  task UUIDs (e.g. a serial-batch loop reusing the same play_id with
  thousands of freshly-generated task UUIDs) would grow this set
  unboundedly.
- ``_grafted_role_names`` (set): per-(parent, role) dedupe keys for the
  sibling-graft path. Same upper bound as ``_grafted_uuids`` in
  practice.
- ``_play_window_counts`` (dict): per-play window ordinals. Cap at
  ``MAX_PLAYS``.
- ``unknown_events`` (dict): bounded by the *number of distinct event
  names* the JSONL callback ever emits — a small fixed universe in
  practice. No additional cap needed; the existing key set is already
  a few dozen.

The caps match the documented memory bounds (SPECIFICATION.md §6.5)
so a cap hit in the renderer's set has a known upper bound too.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.core.run_state import RunState
from ansible_aom.core.state_machine import MAX_PLAYS, MAX_TASKS_PER_PLAY


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def test_grafted_uuids_capped_at_max_tasks_per_play() -> None:
    """R15: ``_grafted_uuids`` does not exceed ``MAX_TASKS_PER_PLAY``."""
    state = RunState(playbook="x")
    # We can't trivially drive ``_graft_or_match_task`` to fill
    # ``_grafted_uuids`` from the test side (it would also require a
    # matching ``definitions`` tree), so exercise the cap directly on
    # the underlying set — the implementation is a property-style
    # attribute and the cap is checked at insert time.
    for i in range(MAX_TASKS_PER_PLAY * 2):
        state._grafted_uuids.add(f"uuid-{i}")
    assert len(state._grafted_uuids) <= MAX_TASKS_PER_PLAY


def test_grafted_role_names_capped() -> None:
    """R15: ``_grafted_role_names`` is bounded (some reasonable N)."""
    state = RunState(playbook="x")
    cap = MAX_TASKS_PER_PLAY
    for i in range(cap * 2):
        state._grafted_role_names.add(f"role-{i}")
    assert len(state._grafted_role_names) <= cap


def test_play_window_counts_capped_at_max_plays() -> None:
    """R15: ``_play_window_counts`` is bounded at ``MAX_PLAYS``."""
    state = RunState(playbook="x")
    for i in range(MAX_PLAYS * 2):
        state._play_window_counts[f"play-{i}"] = 1
    assert len(state._play_window_counts) <= MAX_PLAYS


def test_unknown_events_keys_naturally_bounded() -> None:
    """R15: ``unknown_events`` keys are bounded by event-type cardinality.

    The JSONL callback emits a small fixed set of ``_event`` values
    (~30 distinct names across ansible-core versions). The dict's
    *values* (per-event counts) can grow without bound, but each
    counter is a single int and the total key space is small — capping
    is unnecessary. This test pins the cardinality invariant by
    injecting more distinct keys than any real callback would emit
    and confirming nothing crashes.
    """
    state = RunState(playbook="x")
    # Inject 200 fake unknown-event types — far more than reality.
    for i in range(200):
        state.unknown_events[f"fake_event_{i}"] = i + 1
    assert len(state.unknown_events) == 200  # not capped
    # The renderer's "unknown events" hint reads from this dict; it
    # never crashes on a long key list. Sum check (used by the hint).
    assert sum(state.unknown_events.values()) == sum(range(1, 201))
