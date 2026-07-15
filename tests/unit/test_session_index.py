"""Unit tests for the derived per-session sqlite index (session/index.py).

events.jsonl stays the source of truth; index.db is a disposable,
rebuildable acceleration structure. These tests pin:

- freshness tracking against events.jsonl size+mtime
- structural parity with the in-memory builders
- byte-exact event resolution through EventRef seeks
- verbose-line parity with build_verbose_lines
"""

from __future__ import annotations

import json
from pathlib import Path

from ansible_aom.core.inspect_model import (
    build_run_summary,
    build_task_tree,
    build_verbose_lines,
)
from ansible_aom.session.index import (
    build_index,
    ensure_index,
    index_is_fresh,
    index_path,
    load_structure,
    load_summary,
    load_tree,
    query_verbose,
    read_event,
)
from ansible_aom.session.store import load_session


def _events() -> list[dict]:
    return [
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-07-01T10:00:00Z",
            "play": {"id": "play-1", "name": "Play Ünïcode"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-07-01T10:00:01Z",
            "task": {"id": "task-1", "name": "Install päckages", "path": "site.yml:3"},
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
            "line": "run-level warning",
            "source": "run_level",
            "connection_id": None,
            "attribution_confidence": "unique",
        },
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-07-01T10:00:02Z",
            "line": "ssh chatter für task-1",
            "source": "connection",
            "connection_id": "conn-1",
            "attribution_confidence": "ambiguous",
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-07-01T10:00:03Z",
            "task": {"id": "task-1", "name": "Install päckages", "path": "site.yml:3"},
            "hosts": {"web1": {"changed": True, "stdout": "größe installed"}},
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-07-01T10:00:04Z",
            "task": {"id": "task-1", "name": "Install päckages", "path": "site.yml:3"},
            "hosts": {"web2": {"changed": False, "msg": "boom"}},
        },
    ]


def _write_session(tmp_path: Path, *, malformed: bool = False) -> Path:
    session_path = tmp_path / "0198cccc-0000-7000-8000-000000000001"
    session_path.mkdir(parents=True)
    meta = {
        "session_id": session_path.name,
        "playbook": "site.yml",
        "status": "failed",
        "start_time": "2026-07-01T10:00:00Z",
        "end_time": "2026-07-01T10:00:10Z",
        "duration_seconds": 10.0,
        "_schema_version": 2,
    }
    (session_path / "meta.json").write_text(json.dumps(meta))
    with open(session_path / "events.jsonl", "w", encoding="utf-8") as f:
        for i, event in enumerate(_events()):
            if malformed and i == 3:
                f.write("{this is not json\n")
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return session_path


def test_build_index_creates_fresh_index(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    assert not index_is_fresh(session_path)

    assert build_index(session_path) is True

    assert index_path(session_path).exists()
    assert index_is_fresh(session_path)


def test_index_goes_stale_when_events_grow(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    build_index(session_path)

    with open(session_path / "events.jsonl", "a") as f:
        f.write(json.dumps({"_event": "v2_playbook_on_stats", "stats": {}}) + "\n")

    assert not index_is_fresh(session_path)


def test_ensure_index_builds_once(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    assert ensure_index(session_path) is True
    first_mtime = index_path(session_path).stat().st_mtime_ns

    assert ensure_index(session_path) is True
    assert index_path(session_path).stat().st_mtime_ns == first_mtime


def test_tree_structure_matches_in_memory_builder(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    build_index(session_path)
    session = load_session(session_path.name, tmp_path)
    assert session is not None

    expected = build_task_tree(session)
    tree = load_tree(session_path, playbook="site.yml")

    assert tree.label == expected.label
    assert tree.stats == expected.stats
    assert tree.per_host == expected.per_host
    play = tree.children[0]
    assert play.label == "Play Ünïcode"
    task = play.children[0]
    expected_task = expected.children[0].children[0]
    assert task.label == expected_task.label
    assert task.stats == expected_task.stats
    assert task.duration == expected_task.duration
    assert [h.label for h in task.children] == [h.label for h in expected_task.children]


def test_event_refs_resolve_to_exact_events(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    build_index(session_path)

    tree = load_tree(session_path, playbook="site.yml")
    task = tree.children[0].children[0]
    web2 = next(h for h in task.children if h.label == "web2")

    assert web2.raw_event is None
    assert web2.raw_ref is not None
    resolved = read_event(session_path, web2.raw_ref)
    assert resolved is not None
    assert resolved["_event"] == "v2_runner_on_failed"
    assert resolved["hosts"]["web2"]["msg"] == "boom"


def test_refs_survive_malformed_lines(tmp_path: Path) -> None:
    """A malformed line shifts byte offsets; refs must still be exact."""
    session_path = _write_session(tmp_path, malformed=True)
    build_index(session_path)

    tree = load_tree(session_path, playbook="site.yml")
    task = tree.children[0].children[0]
    web1 = next(h for h in task.children if h.label == "web1")
    assert web1.raw_ref is not None
    resolved = read_event(session_path, web1.raw_ref)
    assert resolved is not None
    assert resolved["hosts"]["web1"]["stdout"] == "größe installed"


def test_summary_matches_in_memory_builder(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    build_index(session_path)
    session = load_session(session_path.name, tmp_path)
    assert session is not None

    meta = {k: v for k, v in session.items() if k != "events"}
    assert load_summary(session_path, meta) == build_run_summary(session)


def test_query_verbose_matches_in_memory_builder(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    build_index(session_path)
    session = load_session(session_path.name, tmp_path)
    assert session is not None

    for kwargs in (
        {"level": "run"},
        {"level": "play", "play_name": "Play Ünïcode"},
        {"level": "task", "task_id": "task-1", "host": "web1"},
    ):
        expected = build_verbose_lines(session, **kwargs)
        tree = load_tree(session_path, playbook="site.yml")
        assert query_verbose(session_path, tree=tree, **kwargs) == expected

    tree = load_tree(session_path, playbook="site.yml")
    assert tree is not None
    assert query_verbose(session_path, tree=tree, level="run") == ("run-level warning",)


def test_load_structure_returns_index_without_stderr(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    build_index(session_path)

    index = load_structure(session_path)

    assert index is not None
    assert [t.task_id for t in index.tasks] == ["task-1"]
    assert index.failed_task_count == 1
    assert index.stderr == ()  # verbose rows load on demand, not with the structure


def test_build_index_returns_false_without_events(tmp_path: Path) -> None:
    session_path = tmp_path / "empty-session"
    session_path.mkdir()
    assert build_index(session_path) is False
    assert not index_is_fresh(session_path)


def _write_second_session(first: Path) -> Path:
    other = first.parent / "0198cccc-0000-7000-8000-000000000002"
    other.mkdir()
    (other / "meta.json").write_text((first / "meta.json").read_text())
    (other / "events.jsonl").write_text((first / "events.jsonl").read_text())
    return other


def test_sessions_needing_index_lists_only_stale(tmp_path: Path) -> None:
    from ansible_aom.session.index import sessions_needing_index

    first = _write_session(tmp_path)
    second = _write_second_session(first)
    (tmp_path / "not-a-session").mkdir()
    (tmp_path / "stray-file").write_text("x")
    build_index(first)

    assert sessions_needing_index(tmp_path) == [second]


def test_build_indexes_sequential_small_backlog(tmp_path: Path) -> None:
    from ansible_aom.session.index import build_indexes

    first = _write_session(tmp_path)
    second = _write_second_session(first)

    results = dict(build_indexes([first, second]))

    assert results == {first: True, second: True}
    assert index_is_fresh(first)
    assert index_is_fresh(second)


def test_build_indexes_process_pool(tmp_path: Path) -> None:
    """Force the pool path (threshold 0) — results identical to sequential."""
    from ansible_aom.session.index import build_indexes

    first = _write_session(tmp_path)
    second = _write_second_session(first)

    results = dict(build_indexes([first, second], max_workers=2, parallel_min_bytes=0))

    assert results == {first: True, second: True}
    assert index_is_fresh(first)
    assert index_is_fresh(second)
