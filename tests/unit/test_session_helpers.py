"""Unit tests for core.session helper functions."""

import json
from pathlib import Path

import pytest

from ansible_aom.core.inspect_model import is_valid_session_id
from ansible_aom.session.store import find_latest_session, load_session, load_session_meta


@pytest.mark.parametrize("metadata", [b"[]", b"null", b"1", b'"text"', b"true", b"\xff"])
def test_malformed_metadata_does_not_break_session_readers(tmp_path: Path, metadata: bytes) -> None:
    # Invalid UTF-8 and valid JSON with the wrong shape need the same fallback.
    from ansible_aom.session.store import cleanup_old_sessions, list_sessions

    _write_session(tmp_path, "healthy", "2026-05-20T11:24:09Z")
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "meta.json").write_bytes(metadata)
    event = {"_event": "v2_playbook_on_start"}
    (broken / "events.jsonl").write_text(json.dumps(event) + "\n")

    assert [s["session_id"] for s in list_sessions(tmp_path)] == ["healthy"]
    assert load_session_meta("broken", tmp_path) == {
        "playbook": "",
        "status": "",
        "_schema_version": 1,
        "diagnostics": None,
        "session_id": "broken",
    }
    loaded = load_session("broken", tmp_path)
    assert loaded is not None
    assert loaded["events"] == [event]
    assert cleanup_old_sessions(tmp_path, keep_days=100000) == 0


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


@pytest.mark.parametrize(
    "session_id",
    [
        "019e4000-0000-7000-8000-000000000001",
        "clean_run",
        "v1-legacy",
    ],
)
def test_is_valid_session_id_accepts_single_safe_segment(session_id: str) -> None:
    assert is_valid_session_id(session_id) is True


@pytest.mark.parametrize(
    "bad_id",
    [
        "",
        "   ",
        ".",
        "..",
        "../other",
        "sub/dir",
        "/abs/path",
        "back\\slash",
        "null\x00byte",
        None,
        123,
    ],
)
def test_is_valid_session_id_rejects_unsafe_values(bad_id: object) -> None:
    assert is_valid_session_id(bad_id) is False


def test_load_session_meta_rejects_traversal_and_non_directory(tmp_path: Path) -> None:
    state = tmp_path / "sessions"
    state.mkdir()
    _write_session(state, "valid-session", "2026-05-19T18:02:00.000Z")
    (state / "plain_file").write_text("not a session dir\n")

    for bad_id in (
        "",
        "   ",
        ".",
        "..",
        "../sessions",
        str(state),
        "valid-session/meta.json",
        "plain_file",
    ):
        assert load_session_meta(bad_id, state) is None, f"expected None for {bad_id!r}"
        assert load_session(bad_id, state) is None, f"expected None for {bad_id!r}"
