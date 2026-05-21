"""End-to-end: write a v1.2 meta.json via SessionManager, look it up via find_previous_run.

This is the contract test that ties Task 2 (persistence) and Task 3
(lookup) together. If either side ever drifts on field names, format,
or semantics, this test fails first — before any user-facing surface
notices.
"""

from __future__ import annotations

from pathlib import Path

from ansible_aom.core.run_config import build_run_config_key
from ansible_aom.session.history import find_previous_run
from ansible_aom.session.store import SessionManager


def test_session_then_history_roundtrip(tmp_path: Path) -> None:
    pb = tmp_path / "play.yml"
    pb.write_text("")

    sessions_dir = tmp_path / "sessions"
    mgr = SessionManager(session_dir=sessions_dir)
    sid = mgr.start_session(str(pb), ansible_args=["--tags", "web"])
    mgr.end_session(sid, "completed", preflight_task_count=12, resolved_host_count=2)

    key = build_run_config_key(playbook=str(pb), ansible_args=["--tags", "web"])
    prior = find_previous_run(sessions_dir, key, host_count=2)
    assert prior is not None
    assert prior.session_id == sid
    assert prior.task_count == 12
    assert prior.host_count == 2
    assert prior.duration_seconds >= 0.0


def test_different_tags_do_not_match(tmp_path: Path) -> None:
    pb = tmp_path / "play.yml"
    pb.write_text("")

    sessions_dir = tmp_path / "sessions"
    mgr = SessionManager(session_dir=sessions_dir)
    sid = mgr.start_session(str(pb), ansible_args=["--tags", "web"])
    mgr.end_session(sid, "completed", preflight_task_count=12, resolved_host_count=2)

    key = build_run_config_key(playbook=str(pb), ansible_args=["--tags", "db"])
    assert find_previous_run(sessions_dir, key, host_count=2) is None


def test_different_host_count_does_not_match(tmp_path: Path) -> None:
    pb = tmp_path / "play.yml"
    pb.write_text("")

    sessions_dir = tmp_path / "sessions"
    mgr = SessionManager(session_dir=sessions_dir)
    sid = mgr.start_session(str(pb), ansible_args=[])
    mgr.end_session(sid, "completed", preflight_task_count=5, resolved_host_count=1)

    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    assert find_previous_run(sessions_dir, key, host_count=3) is None


def test_failed_session_is_not_returned(tmp_path: Path) -> None:
    """End-of-run status==failed sessions are unreliable — skip them."""
    pb = tmp_path / "play.yml"
    pb.write_text("")

    sessions_dir = tmp_path / "sessions"
    mgr = SessionManager(session_dir=sessions_dir)
    sid = mgr.start_session(str(pb), ansible_args=[])
    mgr.end_session(sid, "failed", preflight_task_count=5, resolved_host_count=1)

    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    assert find_previous_run(sessions_dir, key, host_count=1) is None


def test_most_recent_completed_wins(tmp_path: Path) -> None:
    pb = tmp_path / "play.yml"
    pb.write_text("")

    sessions_dir = tmp_path / "sessions"
    mgr = SessionManager(session_dir=sessions_dir)

    sid_old = mgr.start_session(str(pb), ansible_args=[])
    mgr.end_session(sid_old, "completed", preflight_task_count=5, resolved_host_count=1)

    sid_new = mgr.start_session(str(pb), ansible_args=[])
    mgr.end_session(sid_new, "completed", preflight_task_count=7, resolved_host_count=1)

    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    prior = find_previous_run(sessions_dir, key, host_count=1)
    assert prior is not None
    assert prior.session_id == sid_new
    assert prior.task_count == 7
