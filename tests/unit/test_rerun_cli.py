"""Unit tests for the aom rerun subcommand."""

import json
from pathlib import Path

import pytest

from ansible_aom.rerun.cli import _resolve_session_id


def _make_session(state_dir: Path, session_id: str, start_time: str) -> Path:
    """Helper: create a session directory with a minimal meta.json."""
    session_path = state_dir / session_id
    session_path.mkdir(parents=True)
    meta = {
        "playbook": "site.yml",
        "ansible_args": ["-i", "inv.ini"],
        "start_time": start_time,
        "session_id": session_id,
        "status": "failed",
        "version": "1.1",
    }
    (session_path / "meta.json").write_text(json.dumps(meta))
    return session_path


class TestResolveSessionId:
    def test_explicit_full_id_returned_as_is(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        _make_session(state_dir, sid, "2026-05-12T10:00:00Z")
        assert _resolve_session_id(state_dir, sid) == sid

    def test_explicit_short_id_resolved_to_full(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        _make_session(state_dir, sid, "2026-05-12T10:00:00Z")
        assert _resolve_session_id(state_dir, "01971111") == sid

    def test_omitted_returns_most_recent(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        older = "01971111-1111-7000-8000-000000000001"
        newer = "01971112-2222-7000-8000-000000000002"
        _make_session(state_dir, older, "2026-05-10T10:00:00Z")
        _make_session(state_dir, newer, "2026-05-12T10:00:00Z")
        assert _resolve_session_id(state_dir, None) == newer

    def test_unknown_id_raises(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid = "01971111-1111-7000-8000-000000000001"
        _make_session(state_dir, sid, "2026-05-12T10:00:00Z")
        with pytest.raises(LookupError, match="No session matching"):
            _resolve_session_id(state_dir, "deadbeef")

    def test_no_sessions_at_all_raises(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        state_dir.mkdir()
        with pytest.raises(LookupError, match="No sessions"):
            _resolve_session_id(state_dir, None)

    def test_ambiguous_short_id_raises(self, tmp_path: Path):
        state_dir = tmp_path / "sessions"
        sid_a = "01971111-1111-7000-8000-000000000001"
        sid_b = "01971111-2222-7000-8000-000000000002"
        _make_session(state_dir, sid_a, "2026-05-10T10:00:00Z")
        _make_session(state_dir, sid_b, "2026-05-12T10:00:00Z")
        with pytest.raises(LookupError, match="ambiguous"):
            _resolve_session_id(state_dir, "01971111")
