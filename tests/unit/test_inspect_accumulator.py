"""Unit tests for the streaming SessionIndex accumulator (core).

The accumulator is the single aggregation implementation behind
``build_task_tree`` / ``build_run_summary`` (in-memory path) and the
sqlite session index (streaming path). Fed with byte refs it must not
retain raw event dicts; fed without, it preserves the legacy behavior
of carrying the last raw event for the detail pane.
"""

from __future__ import annotations

import json

from ansible_aom.core.inspect_model import (
    EventRef,
    SessionIndexAccumulator,
    build_run_summary,
    build_task_tree,
    summary_from_index,
    tree_from_index,
)


def _events() -> list[dict]:
    return [
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-07-01T10:00:00Z",
            "play": {"id": "play-1", "name": "Play One"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-07-01T10:00:01Z",
            "task": {"id": "task-1", "name": "Install", "path": "site.yml:3"},
        },
        {
            "_event": "aom_connection_acquired",
            "_timestamp": "2026-07-01T10:00:01Z",
            "connection_id": "conn-1",
            "task_id": "task-1",
            "host": "web1",
        },
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-07-01T10:00:02Z",
            "line": "ssh chatter",
            "source": "connection",
            "connection_id": "conn-1",
            "attribution_confidence": "unique",
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-07-01T10:00:03Z",
            "task": {"id": "task-1", "name": "Install", "path": "site.yml:3"},
            "hosts": {"web1": {"changed": True, "stdout": "installed"}},
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-07-01T10:00:04Z",
            "task": {"id": "task-1", "name": "Install", "path": "site.yml:3"},
            "hosts": {"web2": {"changed": False, "msg": "boom"}},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-07-01T10:00:05Z",
            "task": {"id": "task-2", "name": "Verify", "path": "site.yml:9"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-07-01T10:00:06Z",
            "task": {"id": "task-2", "name": "Verify", "path": "site.yml:9"},
            "hosts": {"web1": {"changed": False}},
        },
    ]


def _session() -> dict:
    return {
        "session_id": "0198aaaa-0000-7000-8000-000000000001",
        "playbook": "site.yml",
        "status": "failed",
        "start_time": "2026-07-01T10:00:00Z",
        "end_time": "2026-07-01T10:00:10Z",
        "duration_seconds": 10.0,
        "events": _events(),
    }


def _feed_with_refs(acc: SessionIndexAccumulator, events: list[dict]) -> list[EventRef]:
    """Feed events with synthetic byte refs, as the store's streamer would."""
    refs = []
    offset = 0
    for event in events:
        length = len(json.dumps(event).encode())
        ref = EventRef(offset=offset, length=length)
        acc.feed(event, ref=ref)
        refs.append(ref)
        offset += length + 1
    return refs


def test_accumulator_aggregates_counts_and_failed_tasks() -> None:
    acc = SessionIndexAccumulator()
    for event in _events():
        acc.feed(event)
    index = acc.finish()

    assert [p.name for p in index.plays] == ["Play One"]
    assert [t.task_id for t in index.tasks] == ["task-1", "task-2"]
    assert index.host_counts["web1"].changed == 1
    assert index.host_counts["web1"].ok == 1
    assert index.host_counts["web2"].failed == 1
    assert index.failed_task_count == 1


def test_accumulator_collects_verbose_rows() -> None:
    acc = SessionIndexAccumulator()
    for event in _events():
        acc.feed(event)
    index = acc.finish()

    assert index.connections["conn-1"] == ("task-1", "web1")
    assert len(index.stderr) == 1
    assert index.stderr[0].line == "ssh chatter"
    assert index.stderr[0].connection_id == "conn-1"


def test_accumulator_can_skip_stderr_collection() -> None:
    """The sqlite builder streams stderr rows straight to disk; the
    accumulator must not also pile them up in memory."""
    acc = SessionIndexAccumulator(collect_stderr=False)
    for event in _events():
        acc.feed(event)
    index = acc.finish()

    assert index.stderr == ()
    # Everything else is unaffected.
    assert index.connections["conn-1"] == ("task-1", "web1")
    assert [t.task_id for t in index.tasks] == ["task-1", "task-2"]


def test_stderr_row_from_event_extracts_scoping_fields() -> None:
    from ansible_aom.core.inspect_model import stderr_row_from_event

    row = stderr_row_from_event(
        {
            "_event": "aom_stderr_line",
            "line": "boom",
            "source": "connection",
            "connection_id": "conn-9",
            "attribution_confidence": "ambiguous",
        }
    )
    assert row.line == "boom"
    assert row.source == "connection"
    assert row.connection_id == "conn-9"
    assert row.ambiguous is True


def test_streaming_refs_replace_raw_events() -> None:
    events = _events()
    acc = SessionIndexAccumulator()
    refs = _feed_with_refs(acc, events)
    index = acc.finish()

    tree = tree_from_index(index, playbook="site.yml")
    play = tree.children[0]
    task1 = play.children[0]
    web2 = next(h for h in task1.children if h.label == "web2")
    # No dict retained; the ref points at the v2_runner_on_failed line.
    assert web2.raw_event is None
    assert web2.raw_ref == refs[5]
    assert task1.raw_ref == refs[5]


def test_tree_from_index_matches_build_task_tree() -> None:
    session = _session()
    acc = SessionIndexAccumulator()
    for event in session["events"]:
        acc.feed(event)

    streamed = tree_from_index(acc.finish(), playbook=session["playbook"])

    assert streamed == build_task_tree(session)


def test_summary_from_index_matches_build_run_summary() -> None:
    session = _session()
    acc = SessionIndexAccumulator()
    for event in session["events"]:
        acc.feed(event)

    streamed = summary_from_index(acc.finish(), session)

    assert streamed == build_run_summary(session)
