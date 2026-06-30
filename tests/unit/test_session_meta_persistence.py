"""Tests that end_session persists task_count / host_count for the history feature."""

from __future__ import annotations

import json
from pathlib import Path

from ansible_aom.session.store import SessionManager


def test_end_session_persists_task_and_host_counts(tmp_path: Path) -> None:
    mgr = SessionManager(session_dir=tmp_path / "sessions")
    sid = mgr.start_session("play.yml", ansible_args=[])
    mgr.end_session(sid, "completed", preflight_task_count=12, resolved_host_count=3)

    meta_path = tmp_path / "sessions" / sid / "meta.json"
    meta = json.loads(meta_path.read_text())
    assert meta["preflight_task_count"] == 12
    assert meta["resolved_host_count"] == 3
    assert meta["version"] == "1.2"


def test_end_session_without_counts_writes_nulls(tmp_path: Path) -> None:
    """Backwards-compatible — callers that don't pass counts still produce valid meta."""
    mgr = SessionManager(session_dir=tmp_path / "sessions")
    sid = mgr.start_session("play.yml", ansible_args=[])
    mgr.end_session(sid, "completed")

    meta_path = tmp_path / "sessions" / sid / "meta.json"
    meta = json.loads(meta_path.read_text())
    # Tightened: must be present as JSON null, not just absent.
    assert "preflight_task_count" in meta and meta["preflight_task_count"] is None
    assert "resolved_host_count" in meta and meta["resolved_host_count"] is None
