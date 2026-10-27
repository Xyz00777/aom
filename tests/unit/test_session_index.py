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
    EventRef,
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


def test_load_structure_failed_hosts_only(tmp_path: Path) -> None:
    """--text renders header (summary table), failures, and verbose — none
    of which need host rows for passing tasks. The filtered load returns
    hosts only for tasks with failures plus explicitly included tasks."""
    session_path = _write_session(tmp_path)
    build_index(session_path)

    index = load_structure(session_path, failed_hosts_only=True)

    assert index is not None
    task = index.tasks[0]
    # task-1 has web1 (ok) and web2 (failed): the failing task keeps ALL
    # its host rows so failure context stays complete.
    assert {h.host for h in task.hosts} == {"web1", "web2"}
    # Aggregates are unaffected by host filtering.
    assert task.counts.failed == 1
    assert index.host_counts["web1"].changed == 1


def test_load_structure_failed_hosts_only_skips_passing_tasks(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    # Append a fully-ok second task, then rebuild.
    with open(session_path / "events.jsonl", "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "_event": "v2_runner_on_ok",
                    "_timestamp": "2026-07-01T10:00:06Z",
                    "task": {"id": "task-2", "name": "Verify", "path": "site.yml:9"},
                    "hosts": {"web1": {"changed": False}},
                }
            )
            + "\n"
        )
    build_index(session_path)

    index = load_structure(session_path, failed_hosts_only=True)
    assert index is not None
    ok_task = next(t for t in index.tasks if t.task_id == "task-2")
    assert ok_task.hosts == ()  # host rows skipped
    assert ok_task.counts.ok == 1  # aggregates intact

    # ...unless explicitly included (the --task <name> scope needs them).
    index = load_structure(
        session_path, failed_hosts_only=True, include_task_ids=frozenset({"task-2"})
    )
    assert index is not None
    ok_task = next(t for t in index.tasks if t.task_id == "task-2")
    assert [h.host for h in ok_task.hosts] == ["web1"]


def test_find_task_id_by_name(tmp_path: Path) -> None:
    from ansible_aom.session.index import find_task_id_by_name

    session_path = _write_session(tmp_path)
    build_index(session_path)

    assert find_task_id_by_name(session_path, "Install päckages") == "task-1"
    assert find_task_id_by_name(session_path, "no such task") is None


def test_build_index_returns_false_without_events(tmp_path: Path) -> None:
    session_path = tmp_path / "empty-session"
    session_path.mkdir()
    assert build_index(session_path) is False
    assert not index_is_fresh(session_path)


def test_build_index_rejects_log_that_changes_during_build(tmp_path: Path, monkeypatch) -> None:
    session_path = _write_session(tmp_path)
    import ansible_aom.session.index as index_mod

    original_events_stat = index_mod.events_stat
    calls = 0

    def changing_events_stat(path: Path) -> tuple[int, int] | None:
        nonlocal calls
        calls += 1
        stat = original_events_stat(path)
        if calls == 1 or stat is None:
            return stat
        return (stat[0] + 1, stat[1])

    monkeypatch.setattr(index_mod, "events_stat", changing_events_stat)

    assert build_index(session_path) is False
    assert not index_path(session_path).exists()
    assert list(session_path.glob("index.tmp-*.db")) == []


def test_load_session_skips_non_object_json_records(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    with open(session_path / "events.jsonl", "a", encoding="utf-8") as events_file:
        events_file.write("[1, 2, 3]\n")
        events_file.write('"not an event"\n')

    session = load_session(session_path.name, tmp_path)

    assert session is not None
    assert session["malformed_lines"] == 2
    assert all(isinstance(event, dict) for event in session["events"])


def test_load_session_skips_invalid_utf8_record(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    with open(session_path / "events.jsonl", "ab") as events_file:
        events_file.write(b'"\xff"\n')

    session = load_session(session_path.name, tmp_path)

    assert session is not None
    assert session["malformed_lines"] == 1
    assert all(isinstance(event, dict) for event in session["events"])


def test_build_index_skips_invalid_utf8_record(tmp_path: Path) -> None:
    session_path = _write_session(tmp_path)
    with open(session_path / "events.jsonl", "ab") as events_file:
        events_file.write(b'"\xff"\n')

    assert build_index(session_path) is True
    assert index_is_fresh(session_path)


def test_read_event_returns_none_for_invalid_utf8(tmp_path: Path) -> None:
    session_path = tmp_path / "invalid-utf8"
    session_path.mkdir()
    payload = b'"\xff"\n'
    (session_path / "events.jsonl").write_bytes(payload)

    assert read_event(session_path, EventRef(offset=0, length=len(payload))) is None


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


def test_sessions_needing_index_newest_first(tmp_path: Path) -> None:
    """Backfill order follows interest: the most recent runs index first.

    Session ids are UUIDv7 (time-sortable), so newest-first is a reverse
    name sort."""
    from ansible_aom.session.index import sessions_needing_index

    first = _write_session(tmp_path)  # ...0001 (older)
    second = _write_second_session(first)  # ...0002 (newer)

    assert sessions_needing_index(tmp_path) == [second, first]


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


def test_build_indexes_falls_back_when_pool_unavailable(tmp_path: Path, monkeypatch) -> None:
    """When the process pool can't be constructed (e.g. the Textual
    stderr-redirect ``bad value(s) in fds_to_keep`` crash), build_indexes
    must degrade to a sequential build, not propagate the error."""
    import ansible_aom.session.index as index_mod

    first = _write_session(tmp_path)
    second = _write_second_session(first)

    def _boom(*args, **kwargs):
        raise ValueError("bad value(s) in fds_to_keep")

    monkeypatch.setattr(index_mod, "ProcessPoolExecutor", _boom)

    results = dict(index_mod.build_indexes([first, second], max_workers=2, parallel_min_bytes=0))

    assert results == {first: True, second: True}
    assert index_is_fresh(first)
    assert index_is_fresh(second)


# --- Issue #19: lone surrogates (PTY output decoded with surrogateescape) ---
#
# The runner decodes the PTY with ``codec_errors="surrogateescape"``, so
# invalid UTF-8 becomes lone-surrogate codepoints. events.jsonl preserves
# them as ``\udcXX`` escapes (byte-exact round-trip); sqlite TEXT cannot
# bind them. The index must sanitise every bound TEXT value, and an index
# failure must never escape session finalisation.

_BAD = b"\xff".decode("utf-8", "surrogateescape")  # "\udcff"


def _surrogate_events() -> list[dict]:
    task = {"id": f"task-{_BAD}", "name": f"Install {_BAD}", "path": f"site{_BAD}.yml:3"}
    return [
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-07-01T10:00:00Z",
            "play": {"id": f"play-{_BAD}", "name": f"Play {_BAD}"},
        },
        {"_event": "v2_playbook_on_task_start", "_timestamp": "2026-07-01T10:00:01Z", "task": task},
        {
            "_event": "aom_connection_acquired",
            "_timestamp": "2026-07-01T10:00:01Z",
            "connection_id": f"conn-{_BAD}",
            "task_id": task["id"],
            "host": f"web{_BAD}",
        },
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-07-01T10:00:02Z",
            "line": f"SSH error: {_BAD}",
            "source": "run_level",
            "connection_id": None,
            "attribution_confidence": "unique",
        },
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-07-01T10:00:02Z",
            "line": f"chatter {_BAD}",
            "source": "connection",
            "connection_id": f"conn-{_BAD}",
            "attribution_confidence": "unique",
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-07-01T10:00:03Z",
            "task": task,
            "hosts": {f"web{_BAD}": {"changed": False, "msg": f"boom {_BAD}"}},
        },
    ]


def _write_surrogate_session(tmp_path: Path) -> Path:
    session_path = tmp_path / "0198cccc-0000-7000-8000-000000000019"
    session_path.mkdir(parents=True)
    with open(session_path / "events.jsonl", "w", encoding="utf-8") as f:
        for event in _surrogate_events():
            # Default ensure_ascii=True: how the session writer persists
            # surrogates — as \udcXX escapes, which json.loads restores.
            f.write(json.dumps(event) + "\n")
    return session_path


def test_build_index_sanitises_surrogates_in_every_text_field(tmp_path: Path) -> None:
    session_path = _write_surrogate_session(tmp_path)
    events_before = (session_path / "events.jsonl").read_bytes()

    assert build_index(session_path) is True
    assert index_is_fresh(session_path)
    # events.jsonl is the immutable source of truth: untouched.
    assert (session_path / "events.jsonl").read_bytes() == events_before

    index = load_structure(session_path)
    assert index is not None
    assert [p.name for p in index.plays] == ["Play ?"]
    assert [(t.task_id, t.name, t.path) for t in index.tasks] == [
        ("task-?", "Install ?", "site?.yml:3")
    ]
    assert [h.host for h in index.tasks[0].hosts] == ["web?"]
    assert list(index.host_counts) == ["web?"]


def test_index_lookups_accept_surrogate_bearing_params(tmp_path: Path) -> None:
    """Surrogate-bearing lookup params match their sanitised rows."""
    from ansible_aom.session.index import find_task_id_by_name

    session_path = _write_surrogate_session(tmp_path)
    assert build_index(session_path) is True
    tree = load_tree(session_path, playbook="site.yml")
    assert tree is not None

    assert find_task_id_by_name(session_path, f"Install {_BAD}") == "task-?"
    assert query_verbose(session_path, tree=tree, level="run") == ("SSH error: ?",)
    assert query_verbose(
        session_path, tree=tree, level="task", task_id=f"task-{_BAD}", host=f"web{_BAD}"
    ) == ("SSH error: ?", "chatter ?")
    assert query_verbose(session_path, tree=tree, level="play", play_name=f"Play {_BAD}") == (
        "SSH error: ?",
        "chatter ?",
    )


def test_end_session_with_surrogate_stderr_builds_index(tmp_path: Path) -> None:
    """Issue #19 reproduction: finalisation must not raise."""
    from ansible_aom.session.store import SessionManager

    mgr = SessionManager(session_dir=tmp_path)
    sid = mgr.start_session("site.yml")
    mgr.record_stderr(sid, b"SSH error: \xff".decode("utf-8", "surrogateescape"))
    mgr.end_session(sid, "completed")

    session_path = tmp_path / sid
    assert json.loads((session_path / "meta.json").read_text())["status"] == "completed"
    assert b"\\udcff" in (session_path / "events.jsonl").read_bytes()
    assert index_is_fresh(session_path)


def test_end_session_survives_unexpected_index_failure(tmp_path: Path, monkeypatch) -> None:
    """Any index-build failure must not escape finalisation."""
    import ansible_aom.session.index as index_mod
    from ansible_aom.session.store import SessionManager

    def explode(*args: object, **kwargs: object) -> None:
        raise TypeError("unexpected index-writer bug")

    monkeypatch.setattr(index_mod, "_write_index_db", explode)

    mgr = SessionManager(session_dir=tmp_path)
    sid = mgr.start_session("site.yml")
    mgr.end_session(sid, "completed")

    session_path = tmp_path / sid
    assert json.loads((session_path / "meta.json").read_text())["status"] == "completed"
    assert not index_path(session_path).exists()
    assert list(session_path.glob("index.tmp-*.db")) == []


def test_build_index_returns_false_when_temp_cleanup_fails(tmp_path: Path, monkeypatch) -> None:
    session_path = _write_session(tmp_path)

    def deny(self: Path, missing_ok: bool = False) -> None:
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "unlink", deny)

    assert build_index(session_path) is False


def test_build_index_handles_colliding_surrogate_hosts_and_connections(tmp_path: Path) -> None:
    """Two hosts or connection ids that differ only in invalid UTF-8 bytes
    both sanitise to the same key; indexing and _write_index_db must merge
    host_counts and keep first-wins for connections without IntegrityError."""
    import sqlite3

    from ansible_aom.core.inspect_model import SessionIndex, StatusCounts
    from ansible_aom.session.index import _SCHEMA, _write_index_db

    bad_fe = b"\xfe".decode("utf-8", "surrogateescape")
    bad_ff = b"\xff".decode("utf-8", "surrogateescape")
    task = {"id": "task-1", "name": "Check host", "path": "site.yml:3"}
    events = [
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-07-01T10:00:00Z",
            "play": {"id": "play-1", "name": "Play 1"},
        },
        {"_event": "v2_playbook_on_task_start", "_timestamp": "2026-07-01T10:00:01Z", "task": task},
        {
            "_event": "aom_connection_acquired",
            "_timestamp": "2026-07-01T10:00:01Z",
            "connection_id": f"conn-{bad_fe}",
            "task_id": "task-1",
            "host": f"web{bad_fe}",
        },
        {
            "_event": "aom_connection_acquired",
            "_timestamp": "2026-07-01T10:00:01Z",
            "connection_id": f"conn-{bad_ff}",
            "task_id": "task-2",
            "host": f"web{bad_ff}",
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-07-01T10:00:02Z",
            "task": task,
            "hosts": {f"web{bad_fe}": {"changed": False}},
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-07-01T10:00:03Z",
            "task": task,
            "hosts": {f"web{bad_ff}": {"changed": False, "msg": "failed"}},
        },
    ]
    session_path = tmp_path / "0198cccc-0000-7000-8000-000000000020"
    session_path.mkdir(parents=True)
    with open(session_path / "events.jsonl", "w", encoding="utf-8") as f:
        for evt in events:
            f.write(json.dumps(evt) + "\n")

    assert build_index(session_path) is True
    loaded = load_structure(session_path)
    assert loaded is not None
    assert loaded.host_counts == {"web?": StatusCounts(ok=1, failed=1)}

    # Also verify _write_index_db directly when handed unsanitised colliding keys.
    raw_index = SessionIndex(
        plays=(),
        tasks=(),
        host_counts={
            f"web{bad_fe}": StatusCounts(ok=2),
            f"web{bad_ff}": StatusCounts(failed=1),
        },
        failed_task_count=1,
        stderr=(),
        connections={
            f"conn-{bad_fe}": ("task-1", f"web{bad_fe}"),
            f"conn-{bad_ff}": ("task-2", f"web{bad_ff}"),
        },
        fallback_play_name="",
    )
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA)
    _write_index_db(conn, raw_index, events_stat=(10, 20), malformed=0)
    assert conn.execute("SELECT host, ok, failed FROM host_counts").fetchall() == [("web?", 2, 1)]
    assert conn.execute("SELECT connection_id, task_id, host FROM connections").fetchall() == [
        ("conn-?", "task-1", "web?")
    ]
    conn.close()


def test_render_session_from_index_and_in_memory_parity_with_surrogates(tmp_path: Path) -> None:
    """Index-backed and in-memory text rendering must preserve failure details
    for surrogate-bearing hosts, resolve surrogate-bearing --task/--play scopes,
    and produce identical UTF-8-encodable text."""
    from ansible_aom.inspect.text import render_session, render_session_from_index
    from ansible_aom.session.store import load_session

    session_path = _write_surrogate_session(tmp_path)
    meta = {
        "session_id": session_path.name,
        "playbook": f"site{_BAD}.yml",
        "status": "failed",
        "start_time": "2026-07-01T10:00:00Z",
        "end_time": "2026-07-01T10:00:03Z",
        "duration_seconds": 3.0,
    }
    (session_path / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    assert build_index(session_path) is True

    session = load_session(session_path.name, tmp_path)
    assert session is not None

    for kwargs in (
        {},
        {"play_name": f"Play {_BAD}"},
        {"task_name": f"Install {_BAD}"},
    ):
        from_idx = render_session_from_index(session_path, meta, **kwargs)
        assert from_idx is not None
        from_mem = render_session(session, **kwargs)
        # Must be valid UTF-8 (no lone surrogates left).
        from_idx.encode("utf-8")
        from_mem.encode("utf-8")
        # Failure detail payload must not be lost when host label was sanitised.
        assert "msg: boom ?" in from_idx
        assert from_idx == from_mem

    task_scoped = render_session_from_index(session_path, meta, task_name=f"Install {_BAD}")
    assert task_scoped is not None
    assert "chatter ?" in task_scoped


def test_inspect_cli_outputs_with_surrogates_do_not_raise_on_strict_utf8_stdout(
    tmp_path: Path, monkeypatch
) -> None:
    """inspect_text, inspect_changes, and inspect_warnings must never raise
    UnicodeEncodeError when writing to a strict UTF-8 stdout stream."""
    import io

    from ansible_aom.inspect.cli import inspect_changes, inspect_text, inspect_warnings

    session_path = tmp_path / "0198cccc-0000-7000-8000-000000000021"
    session_path.mkdir(parents=True)
    meta = {
        "session_id": session_path.name,
        "playbook": f"site{_BAD}.yml",
        "status": "failed",
    }
    (session_path / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    events = _surrogate_events() + [
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-07-01T10:00:04Z",
            "task": {
                "id": f"task-chg-{_BAD}",
                "name": f"Change {_BAD}",
                "path": f"site{_BAD}.yml:9",
            },
            "hosts": {
                f"web{_BAD}": {
                    "changed": True,
                    "cmd": f"echo {_BAD}",
                    "msg": f"changed {_BAD}",
                    "stdout": f"out {_BAD}",
                    "stderr": f"err {_BAD}",
                    "diff": {"before": f"old {_BAD}\n", "after": f"new {_BAD}\n"},
                    "dest": f"/etc/{_BAD}.conf",
                    "warnings": [f"warn {_BAD}"],
                    "deprecations": [{"msg": f"depr {_BAD}"}],
                }
            },
        },
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-07-01T10:00:05Z",
            "line": f"[WARNING]: stderr warn {_BAD}",
            "source": "run_level",
            "connection_id": None,
            "attribution_confidence": "unique",
        },
    ]
    with open(session_path / "events.jsonl", "w", encoding="utf-8") as f:
        for evt in events:
            f.write(json.dumps(evt) + "\n")

    buf = io.BytesIO()
    strict_stdout = io.TextIOWrapper(buf, encoding="utf-8", errors="strict")
    monkeypatch.setattr("sys.stdout", strict_stdout)

    assert inspect_text(tmp_path, session_path.name, task_name=f"Install {_BAD}") == 0
    assert (
        inspect_changes(
            tmp_path,
            session_path.name,
            host=f"web{_BAD}",
            play_name=f"Play {_BAD}",
            task_name=f"Change {_BAD}",
            show_diff=True,
        )
        == 0
    )
    assert (
        inspect_warnings(
            tmp_path,
            session_path.name,
            host=f"web{_BAD}",
            play_name=f"Play {_BAD}",
            task_name=f"Change {_BAD}",
        )
        == 0
    )
    strict_stdout.flush()
    rendered = buf.getvalue().decode("utf-8")
    assert "msg: boom ?" in rendered
    assert "Command:  echo ?" in rendered
    assert "Message:  warn ?" in rendered
