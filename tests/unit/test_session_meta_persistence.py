"""Tests that end_session persists task_count / host_count for the history feature."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from ansible_aom.session.index import build_index
from ansible_aom.session.store import SessionManager


def test_new_session_files_are_private_under_permissive_umask(tmp_path: Path) -> None:
    parent = tmp_path / "sessions"
    parent.mkdir(mode=0o755)
    manager = SessionManager(session_dir=parent)

    previous_umask = os.umask(0)
    try:
        session_id = manager.start_session("play.yml", ansible_args=[])
        manager.record_event(session_id, {"_event": "sample"})
        manager.end_session(session_id, "completed")
    finally:
        os.umask(previous_umask)

    session_path = parent / session_id
    assert stat.S_IMODE(session_path.stat().st_mode) == 0o700
    for name in ("events.jsonl", "meta.json", "diagnostics.json", "index.db"):
        assert stat.S_IMODE((session_path / name).stat().st_mode) == 0o600
    assert stat.S_IMODE(parent.stat().st_mode) == 0o755


def test_new_session_path_components_are_private_under_restrictive_umask(
    tmp_path: Path,
) -> None:
    parent = tmp_path / "state" / "aom" / "sessions"
    manager = SessionManager(session_dir=parent)
    existing_parent_mode = stat.S_IMODE(tmp_path.stat().st_mode)

    previous_umask = os.umask(0o777)
    try:
        session_id = manager.start_session("play.yml", ansible_args=[])
        manager.end_session(session_id, "completed")
    finally:
        os.umask(previous_umask)

    created_directories = (tmp_path / "state", tmp_path / "state" / "aom", parent)
    for directory in (*created_directories, parent / session_id):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE(tmp_path.stat().st_mode) == existing_parent_mode


def test_existing_session_parent_modes_are_preserved(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir(mode=0o750)
    parent = state / "sessions"
    parent.mkdir(mode=0o710)
    manager = SessionManager(session_dir=parent)

    previous_umask = os.umask(0o777)
    try:
        session_id = manager.start_session("play.yml", ansible_args=[])
        manager.end_session(session_id, "completed")
    finally:
        os.umask(previous_umask)

    assert stat.S_IMODE(state.stat().st_mode) == 0o750
    assert stat.S_IMODE(parent.stat().st_mode) == 0o710
    assert stat.S_IMODE((parent / session_id).stat().st_mode) == 0o700


def test_legacy_index_rebuild_succeeds_under_restrictive_umask(tmp_path: Path) -> None:
    session_path = tmp_path / "legacy-session"
    session_path.mkdir()
    (session_path / "events.jsonl").write_text('{"_event":"sample"}\n')

    previous_umask = os.umask(0o777)
    try:
        assert build_index(session_path)
    finally:
        os.umask(previous_umask)

    assert stat.S_IMODE((session_path / "index.db").stat().st_mode) == 0o600


def test_artifact_is_private_before_first_write(tmp_path: Path, monkeypatch) -> None:
    import ansible_aom.session.store as store

    manager = SessionManager(
        session_dir=tmp_path / "sessions",
        artifacts_dir=tmp_path / "artifacts",
    )
    session_id = manager.start_session("play.yml", ansible_args=[])
    manager.end_session(session_id, "completed")
    original_fdopen = store.os.fdopen
    modes_at_open: list[int] = []

    def observe_fdopen(fd: int, mode: str):
        modes_at_open.append(stat.S_IMODE(os.fstat(fd).st_mode))
        return original_fdopen(fd, mode)

    monkeypatch.setattr(store.os, "fdopen", observe_fdopen)
    manager.create_artifact(session_id)

    assert modes_at_open == [0o600]


def test_new_artifact_parent_components_are_private_under_restrictive_umask(
    tmp_path: Path,
) -> None:
    artifacts_dir = tmp_path / "state" / "aom" / "artifacts"
    manager = SessionManager(
        session_dir=tmp_path / "sessions",
        artifacts_dir=artifacts_dir,
    )
    session_id = manager.start_session("play.yml", ansible_args=[])
    manager.end_session(session_id, "completed")

    previous_umask = os.umask(0o777)
    try:
        artifact_path = manager.create_artifact(session_id)
    finally:
        os.umask(previous_umask)

    for directory in (tmp_path / "state", tmp_path / "state" / "aom", artifacts_dir):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE(artifact_path.stat().st_mode) == 0o600


def test_existing_artifact_parent_mode_is_preserved(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(mode=0o750)
    manager = SessionManager(
        session_dir=tmp_path / "sessions",
        artifacts_dir=artifacts_dir,
    )
    session_id = manager.start_session("play.yml", ansible_args=[])
    manager.end_session(session_id, "completed")

    previous_umask = os.umask(0o777)
    try:
        artifact_path = manager.create_artifact(session_id)
    finally:
        os.umask(previous_umask)

    assert stat.S_IMODE(artifacts_dir.stat().st_mode) == 0o750
    assert stat.S_IMODE(artifact_path.stat().st_mode) == 0o600


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
