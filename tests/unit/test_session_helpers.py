"""Unit tests for core.session helper functions."""

import json
from pathlib import Path

from ansible_aom.session.store import find_latest_session


def _write_session(root: Path, session_id: str, start_time: str) -> None:
    d = root / session_id
    d.mkdir(parents=True)
    (d / "meta.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "playbook": "p.yml",
                "start_time": start_time,
                "version": "1.1",
            }
        )
    )


def test_find_latest_returns_newest(tmp_path: Path):
    state = tmp_path / "sessions"
    state.mkdir()
    _write_session(state, "019e4000-0000-7000-8000-000000000001", "2026-05-19T18:02:00.000Z")
    _write_session(state, "019e4520-0000-7000-8000-000000000002", "2026-05-20T11:24:09.000Z")
    _write_session(state, "019e4100-0000-7000-8000-000000000003", "2026-05-19T15:00:00.000Z")

    latest = find_latest_session(state)
    assert latest == "019e4520-0000-7000-8000-000000000002"


def test_find_latest_returns_none_when_empty(tmp_path: Path):
    state = tmp_path / "sessions"
    state.mkdir()
    assert find_latest_session(state) is None


def test_find_latest_returns_none_when_dir_missing(tmp_path: Path):
    assert find_latest_session(tmp_path / "nope") is None
