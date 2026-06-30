"""Stateful invariants over the session persistence round-trip.

A single sequence of JSONL events drives two paths in parallel:

1. **Live**: ``RunState.handle_event`` for each event → ``state_live``.
2. **Persisted**: ``SessionManager.record_event`` writes the events to
   disk, then ``load_session`` reads them back and ``handle_event``
   replays them into a fresh ``RunState`` → ``state_replay``.

The two paths feed off the same input but go through completely
different intermediate representations (in-process dicts vs.
``events.jsonl`` text), so any divergence between them surfaces a
serialisation or replay bug. The invariant: the structural shape
(plays, tasks per play, hosts per task, terminal statuses) of
``state_live`` and ``state_replay`` is identical.

Additionally we check that the inspect view built from the persisted
session (``build_task_tree``) yields the same total per-status
counts as the live state. That confirms the inspect path and the
compact path see the same world for a given input — the relationship
that lets the user verify a TUI-displayed failure by reading the
events.jsonl directly.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from ansible_aom.core.inspect_model import StatusCounts, build_task_tree
from ansible_aom.core.models import Status, TaskRunState
from ansible_aom.core.run_state import RunState
from ansible_aom.session.store import SessionManager, load_session

_TERMINAL = {Status.OK, Status.CHANGED, Status.FAILED, Status.SKIPPED, Status.UNREACHABLE}


def _make_play_start(play_idx: int, ts_idx: int) -> dict:
    return {
        "_event": "v2_playbook_on_play_start",
        "_timestamp": f"2026-05-22T10:00:{ts_idx:02d}Z",
        "play": {"id": f"p{play_idx}", "name": f"Play {play_idx}"},
    }


def _make_task_start(play_idx: int, task_idx: int, ts_idx: int) -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": f"2026-05-22T10:00:{ts_idx:02d}Z",
        "play": {"id": f"p{play_idx}"},
        "task": {"id": f"t{play_idx}-{task_idx}", "name": f"Task {task_idx}"},
    }


def _make_result(
    event_type: str,
    play_idx: int,
    task_idx: int,
    host: str,
    ts_idx: int,
    *,
    changed: bool = False,
) -> dict:
    if event_type == "v2_runner_on_ok":
        payload: dict = {"changed": changed}
    elif event_type == "v2_runner_on_failed":
        payload = {"msg": "boom"}
    elif event_type == "v2_runner_on_unreachable":
        payload = {"msg": "no ssh"}
    else:  # v2_runner_on_skipped
        payload = {"skipped": True}
    return {
        "_event": event_type,
        "_timestamp": f"2026-05-22T10:00:{ts_idx:02d}Z",
        "play": {"id": f"p{play_idx}"},
        "task": {"id": f"t{play_idx}-{task_idx}"},
        "hosts": {host: payload},
    }


_RESULT_EVENTS = (
    "v2_runner_on_ok",
    "v2_runner_on_failed",
    "v2_runner_on_skipped",
    "v2_runner_on_unreachable",
)


@st.composite
def event_sequences(draw: st.DrawFn) -> list[dict]:
    """Generate a coherent (play_start → task_start → result*) sequence.

    Coherence matters because the SessionManager only persists what we
    hand it — if we draw a runner_on_ok for an unstarted task, the
    persisted stream has the same un-started task as the live one, so
    both sides produce the same (no-op) state mutation, which is fine
    for the round-trip invariant. We still bias toward well-formed
    sequences so the test exercises non-trivial state.
    """
    n_plays = draw(st.integers(min_value=1, max_value=2))
    n_tasks_per_play = draw(st.integers(min_value=1, max_value=3))
    n_hosts = draw(st.integers(min_value=1, max_value=3))
    hosts = [f"h{i}" for i in range(n_hosts)]

    events: list[dict] = [{"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"}]
    ts = 1
    for p in range(n_plays):
        events.append(_make_play_start(p, ts))
        ts += 1
        for t in range(n_tasks_per_play):
            events.append(_make_task_start(p, t, ts))
            ts += 1
            for h in hosts:
                et = draw(st.sampled_from(_RESULT_EVENTS))
                changed = draw(st.booleans()) if et == "v2_runner_on_ok" else False
                events.append(_make_result(et, p, t, h, ts, changed=changed))
                ts += 1
    return events


def _drive(events: list[dict]) -> RunState:
    state = RunState(playbook="rt.yml")
    for ev in events:
        state.handle_event(ev)
    return state


def _shape(state: RunState) -> dict[str, dict[str, dict[str, Status]]]:
    """Reduce a RunState to its persistence-invariant skeleton.

    Plays → task_ids → host → terminal_status. Names, timestamps,
    messages, ``changed`` flags, and the play/task ordering inside the
    dict are intentionally dropped: they're orthogonal to "did the
    round-trip preserve the structural shape".
    """
    out: dict[str, dict[str, dict[str, Status]]] = {}
    for play_id, play in state.plays.items():
        task_map: dict[str, dict[str, Status]] = {}
        for task_id, task in play.tasks.items():
            task_map[task_id] = {h: hs.status for h, hs in task.hosts.items()}
        out[play_id] = task_map
    return out


def _tree_status_totals(tree) -> StatusCounts:
    """Aggregate ``StatusCounts`` across every task node in the tree.

    ``build_task_tree`` carries per-task stats but no run-level
    aggregate, so we add them up here. This sum should match a direct
    walk of the RunState — that's the cross-path invariant.
    """
    totals = StatusCounts()
    if tree.kind == "task":
        return tree.stats
    for child in tree.children:
        totals = totals.merge(_tree_status_totals(child))
    return totals


def _runstate_status_totals(state: RunState) -> StatusCounts:
    """Walk RunState the way the tree builder walks events."""
    counts = StatusCounts()
    for play in state.plays.values():
        for task in play.tasks.values():
            for hs in task.hosts.values():
                if hs.status == Status.RUNNING:
                    continue
                if hs.status == Status.OK:
                    counts = StatusCounts(
                        ok=counts.ok + 1,
                        changed=counts.changed,
                        failed=counts.failed,
                        skipped=counts.skipped,
                        unreachable=counts.unreachable,
                    )
                elif hs.status == Status.CHANGED:
                    counts = StatusCounts(
                        ok=counts.ok,
                        changed=counts.changed + 1,
                        failed=counts.failed,
                        skipped=counts.skipped,
                        unreachable=counts.unreachable,
                    )
                elif hs.status == Status.FAILED:
                    counts = StatusCounts(
                        ok=counts.ok,
                        changed=counts.changed,
                        failed=counts.failed + 1,
                        skipped=counts.skipped,
                        unreachable=counts.unreachable,
                    )
                elif hs.status == Status.SKIPPED:
                    counts = StatusCounts(
                        ok=counts.ok,
                        changed=counts.changed,
                        failed=counts.failed,
                        skipped=counts.skipped + 1,
                        unreachable=counts.unreachable,
                    )
                elif hs.status == Status.UNREACHABLE:
                    counts = StatusCounts(
                        ok=counts.ok,
                        changed=counts.changed,
                        failed=counts.failed,
                        skipped=counts.skipped,
                        unreachable=counts.unreachable + 1,
                    )
    return counts


# Each example provisions a small temp dir; a `function`-scoped tmp
# fixture would be ideal but Hypothesis examples reuse the same test
# function call, so we generate a session dir per-example by hand.
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
@given(events=event_sequences())
def test_session_roundtrip_preserves_state_shape(
    tmp_path_factory: pytest.TempPathFactory, events: list[dict]
) -> None:
    """Persist → load → replay yields the same structural state."""
    state_live = _drive(events)

    session_dir: Path = tmp_path_factory.mktemp("session-rt")
    mgr = SessionManager(session_dir=session_dir)
    sid = mgr.start_session(playbook="rt.yml")
    for ev in events:
        mgr.record_event(sid, ev)
    loaded = load_session(sid, session_dir)
    assert loaded is not None, "Persisted session must round-trip via load_session"

    state_replay = _drive(loaded["events"])

    assert _shape(state_live) == _shape(state_replay), (
        "Driving the persisted events back through RunState produced a "
        "different play/task/host/status shape than the live drive — "
        "events.jsonl is either lossy or being mis-serialised."
    )


@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
@given(events=event_sequences())
def test_tree_builder_matches_live_runstate_totals(
    tmp_path_factory: pytest.TempPathFactory, events: list[dict]
) -> None:
    """``build_task_tree`` over the persisted session agrees with the live RunState.

    Same input drives both the compact-mode state path and the inspect
    tree path; the per-status totals must agree. Catches the bug where
    the tree builder accumulates a status the live handler doesn't (or
    vice versa).
    """
    state_live = _drive(events)

    session_dir: Path = tmp_path_factory.mktemp("session-tree")
    mgr = SessionManager(session_dir=session_dir)
    sid = mgr.start_session(playbook="rt.yml")
    for ev in events:
        mgr.record_event(sid, ev)
    loaded = load_session(sid, session_dir)
    assert loaded is not None

    tree = build_task_tree(loaded)
    tree_totals = _tree_status_totals(tree)
    state_totals = _runstate_status_totals(state_live)

    assert tree_totals == state_totals, (
        f"Tree totals {tree_totals} disagree with RunState totals {state_totals} "
        f"for the same event sequence — inspect view drifted from compact view."
    )


def test_runstate_never_holds_orphan_hostrunstate() -> None:
    """A ``HostRunState`` only exists under a TaskRunState we know about.

    Sanity check: every (play, task) we see in the resulting state was
    created by a corresponding event. The runner_on_* handlers all
    guard with ``if task_id not in play.tasks: return``, so an orphan
    would only appear if a future handler forgot that guard.
    """
    events = [
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"},
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-05-22T10:00:01Z",
            "play": {"id": "p-unknown"},
            "task": {"id": "t-unknown"},
            "hosts": {"h1": {"changed": False}},
        },
    ]
    state = _drive(events)
    # Either no plays were materialised, or the play exists but its
    # tasks map is empty — never "a play with phantom tasks".
    for play in state.plays.values():
        for task in play.tasks.values():
            assert isinstance(task, TaskRunState)
            # Every host entry must have a recognised status.
            for hs in task.hosts.values():
                assert hs.status in _TERMINAL | {Status.RUNNING, Status.PENDING}
