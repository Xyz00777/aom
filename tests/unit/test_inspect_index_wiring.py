"""Wiring tests: inspect --text and end_session use the sqlite index.

Pins the three integration points of the derived index:

- ``load_session_meta`` reads meta/diagnostics without touching events
- ``SessionManager.end_session`` leaves a fresh index behind
- ``inspect_text`` renders from the index (no full-log parse) and its
  output is byte-identical to the legacy full-parse path
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ansible_aom.inspect.cli import inspect_text
from ansible_aom.session.index import index_is_fresh
from ansible_aom.session.store import SessionManager, load_session, load_session_meta


def _write_session(state_dir: Path) -> str:
    session_id = "0198dddd-0000-7000-8000-000000000001"
    session_path = state_dir / session_id
    session_path.mkdir(parents=True)
    meta = {
        "session_id": session_id,
        "playbook": "site.yml",
        "status": "failed",
        "start_time": "2026-07-01T10:00:00Z",
        "end_time": "2026-07-01T10:00:10Z",
        "duration_seconds": 10.0,
        "_schema_version": 2,
    }
    (session_path / "meta.json").write_text(json.dumps(meta))
    events = [
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
            "_event": "aom_stderr_line",
            "_timestamp": "2026-07-01T10:00:02Z",
            "line": "run-level warning",
            "source": "run_level",
            "connection_id": None,
            "attribution_confidence": "unique",
        },
        {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-07-01T10:00:04Z",
            "task": {"id": "task-1", "name": "Install", "path": "site.yml:3"},
            "hosts": {"web2": {"changed": False, "msg": "boom", "stderr": "kaputt"}},
        },
    ]
    with open(session_path / "events.jsonl", "w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
    return session_id


def test_load_session_meta_reads_no_events(tmp_path: Path) -> None:
    session_id = _write_session(tmp_path)

    meta = load_session_meta(session_id, tmp_path)

    assert meta is not None
    assert meta["playbook"] == "site.yml"
    assert meta["session_id"] == session_id
    assert meta["_schema_version"] == 2
    assert meta["diagnostics"] is None
    assert "events" not in meta


def test_load_session_meta_missing_session(tmp_path: Path) -> None:
    assert load_session_meta("nope", tmp_path) is None


def test_end_session_builds_fresh_index(tmp_path: Path) -> None:
    manager = SessionManager(session_dir=tmp_path)
    session_id = manager.start_session("site.yml")
    manager.record_event(
        session_id,
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-07-01T10:00:03Z",
            "task": {"id": "t1", "name": "ok task"},
            "hosts": {"web1": {"changed": False}},
        },
    )

    manager.end_session(session_id, "completed")

    assert index_is_fresh(tmp_path / session_id)


def test_inspect_text_renders_from_index_without_full_parse(
    tmp_path: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_session(tmp_path)

    # Legacy full-parse output first, for the parity assertion below.
    inspect_text(tmp_path)
    legacy_out = capsys.readouterr().out
    assert "Install" in legacy_out
    assert "boom" in legacy_out

    # The first inspect_text call backfilled the index; a second call must
    # not go anywhere near the full-log loader.
    import ansible_aom.inspect.cli as cli_mod

    def _no_full_parse(*args: object, **kwargs: object) -> None:
        raise AssertionError("full-log load_session must not run when the index is fresh")

    monkeypatch.setattr(cli_mod, "load_session", _no_full_parse)

    assert inspect_text(tmp_path) == 0
    indexed_out = capsys.readouterr().out

    assert indexed_out == legacy_out


def test_inspect_text_falls_back_without_events_file(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    session_id = "0198dddd-0000-7000-8000-000000000002"
    session_path = tmp_path / session_id
    session_path.mkdir(parents=True)
    (session_path / "meta.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "playbook": "site.yml",
                "status": "completed",
                "start_time": "2026-07-01T10:00:00Z",
            }
        )
    )

    assert inspect_text(tmp_path) == 0
    out = capsys.readouterr().out
    assert "site.yml" in out


def test_index_and_legacy_sessions_agree(tmp_path: Path) -> None:
    """load_session (legacy) still works on a session that has an index."""
    session_id = _write_session(tmp_path)
    manager = SessionManager(session_dir=tmp_path)
    del manager

    session = load_session(session_id, tmp_path)
    assert session is not None
    assert len(session["events"]) == 4
