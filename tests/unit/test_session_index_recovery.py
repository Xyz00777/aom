"""A disposable index must recover instead of crashing inspect on bad metadata.

SQLite accepts non-numeric text in meta.value. Previously a fresh-looking
index with such a failed-task count crashed both loaders during int().
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ansible_aom.inspect.cli import inspect_text
from ansible_aom.session.index import (
    build_index,
    index_is_fresh,
    index_path,
    load_structure,
    load_summary,
)


@pytest.fixture
def session_path(tmp_path: Path) -> Path:
    path = tmp_path / "0198dddd-0000-7000-8000-000000000003"
    path.mkdir()
    (path / "meta.json").write_text(
        json.dumps(
            {
                "session_id": path.name,
                "playbook": "recover.yml",
                "status": "failed",
                "start_time": "2026-07-01T10:00:00Z",
                "end_time": "2026-07-01T10:00:09Z",
                "duration_seconds": 9.0,
            }
        )
    )
    events = [
        {"_event": "v2_playbook_on_play_start", "play": {"id": "p", "name": "Recovery"}},
        {
            "_event": "v2_playbook_on_task_start",
            "task": {"id": "t", "name": "Repair database"},
        },
        {
            "_event": "v2_runner_on_failed",
            "task": {"id": "t", "name": "Repair database"},
            "hosts": {"database-2": {"changed": False, "msg": "permission denied"}},
        },
        {
            "_event": "v2_runner_on_ok",
            "task": {"id": "t", "name": "Repair database"},
            "hosts": {"database-1": {"changed": True}},
        },
    ]
    (path / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    assert build_index(path)
    return path


def _damage_failed_count(path: Path, value: str | None) -> None:
    with sqlite3.connect(index_path(path)) as conn:
        conn.execute("UPDATE meta SET value = ? WHERE key = 'failed_task_count'", (value,))


@pytest.mark.parametrize("value", ["broken", None, "-1"])
def test_loaders_reject_invalid_failed_task_count(session_path: Path, value: str | None) -> None:
    _damage_failed_count(session_path, value)

    assert load_structure(session_path) is None
    assert load_summary(session_path, {"playbook": "recover.yml"}) is None
    assert not index_is_fresh(session_path)


def test_inspect_rebuilds_damaged_index_from_unchanged_events(
    session_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events_path = session_path / "events.jsonl"
    source_bytes = events_path.read_bytes()
    source_stat = events_path.stat()
    assert inspect_text(session_path.parent) == 0
    expected = capsys.readouterr().out
    assert "Repair database" in expected
    assert "database-2" in expected
    assert "permission denied" in expected
    _damage_failed_count(session_path, "broken")

    # A repaired index must serve the request; a silent full-parse fallback
    # would leave every subsequent inspect paying for the same bad index.
    import ansible_aom.inspect.cli as cli

    def no_full_parse(*args: object, **kwargs: object) -> None:
        raise AssertionError("inspect must rebuild and use the index")

    monkeypatch.setattr(cli, "load_session", no_full_parse)
    assert inspect_text(session_path.parent) == 0
    assert capsys.readouterr().out == expected
    assert index_is_fresh(session_path)
    structure = load_structure(session_path)
    assert structure is not None
    assert structure.failed_task_count == 1
    assert events_path.read_bytes() == source_bytes
    assert events_path.stat().st_mtime_ns == source_stat.st_mtime_ns
