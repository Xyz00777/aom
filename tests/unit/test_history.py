"""Unit tests for session.history.find_previous_run."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ansible_aom.core.run_config import build_run_config_key
from ansible_aom.session.history import PriorRun, find_previous_run


def _write_session(
    sessions_dir: Path,
    *,
    sid: str,
    playbook: str,
    ansible_args: list[str],
    status: str,
    start: str,
    end: str | None,
    duration: float | None,
    task_count: int | None,
    host_count: int | None,
) -> None:
    d = sessions_dir / sid
    d.mkdir(parents=True)
    meta: dict = {
        "session_id": sid,
        "playbook": playbook,
        "ansible_args": ansible_args,
        "start_time": start,
        "version": "1.2",
        "status": status,
    }
    if end is not None:
        meta["end_time"] = end
    if duration is not None:
        meta["duration_seconds"] = duration
    if task_count is not None:
        meta["preflight_task_count"] = task_count
    if host_count is not None:
        meta["resolved_host_count"] = host_count
    (d / "meta.json").write_text(json.dumps(meta))


def test_returns_none_when_no_sessions(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    assert find_previous_run(tmp_path / "sessions", key, host_count=2) is None


def test_returns_most_recent_matching_completed_run(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    sessions = tmp_path / "sessions"
    _write_session(
        sessions,
        sid="aaa",
        playbook=str(pb),
        ansible_args=[],
        status="completed",
        start="2026-05-18T10:00:00Z",
        end="2026-05-18T10:01:23Z",
        duration=83.0,
        task_count=47,
        host_count=2,
    )
    _write_session(
        sessions,
        sid="bbb",
        playbook=str(pb),
        ansible_args=[],
        status="completed",
        start="2026-05-20T10:00:00Z",
        end="2026-05-20T10:01:45Z",
        duration=105.0,
        task_count=49,
        host_count=2,
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    prior = find_previous_run(sessions, key, host_count=2)
    assert prior is not None
    assert isinstance(prior, PriorRun)
    assert prior.session_id == "bbb"
    assert prior.duration_seconds == 105.0
    assert prior.task_count == 49


def test_filters_out_mismatched_host_count(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    sessions = tmp_path / "sessions"
    _write_session(
        sessions,
        sid="aaa",
        playbook=str(pb),
        ansible_args=[],
        status="completed",
        start="2026-05-18T10:00:00Z",
        end="2026-05-18T10:01:23Z",
        duration=83.0,
        task_count=47,
        host_count=5,
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    assert find_previous_run(sessions, key, host_count=2) is None


def test_filters_out_mismatched_run_config(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    sessions = tmp_path / "sessions"
    _write_session(
        sessions,
        sid="aaa",
        playbook=str(pb),
        ansible_args=["--tags", "web"],
        status="completed",
        start="2026-05-18T10:00:00Z",
        end="2026-05-18T10:01:23Z",
        duration=83.0,
        task_count=47,
        host_count=2,
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=["--tags", "db"])
    assert find_previous_run(sessions, key, host_count=2) is None


def test_skips_non_completed_status(tmp_path: Path) -> None:
    """Failed / crashed runs are unreliable as estimates."""
    pb = tmp_path / "site.yml"
    pb.write_text("")
    sessions = tmp_path / "sessions"
    _write_session(
        sessions,
        sid="aaa",
        playbook=str(pb),
        ansible_args=[],
        status="failed",
        start="2026-05-20T10:00:00Z",
        end="2026-05-20T10:00:30Z",
        duration=30.0,
        task_count=47,
        host_count=2,
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    assert find_previous_run(sessions, key, host_count=2) is None


def test_skips_sessions_missing_counts(tmp_path: Path) -> None:
    """Pre-v1.2 sessions don't have the fields — can't estimate from them."""
    pb = tmp_path / "site.yml"
    pb.write_text("")
    sessions = tmp_path / "sessions"
    _write_session(
        sessions,
        sid="aaa",
        playbook=str(pb),
        ansible_args=[],
        status="completed",
        start="2026-05-20T10:00:00Z",
        end="2026-05-20T10:01:00Z",
        duration=60.0,
        task_count=None,
        host_count=None,
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    assert find_previous_run(sessions, key, host_count=2) is None


def test_returns_none_when_session_dir_missing(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    assert find_previous_run(tmp_path / "nope", key, host_count=2) is None


def test_prior_run_end_time_parsed_to_datetime(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    sessions = tmp_path / "sessions"
    _write_session(
        sessions,
        sid="aaa",
        playbook=str(pb),
        ansible_args=[],
        status="completed",
        start="2026-05-20T10:00:00Z",
        end="2026-05-20T10:01:00Z",
        duration=60.0,
        task_count=10,
        host_count=2,
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    prior = find_previous_run(sessions, key, host_count=2)
    assert prior is not None
    assert prior.end_time == datetime(2026, 5, 20, 10, 1, 0, tzinfo=timezone.utc)


def test_corrupt_meta_is_skipped(tmp_path: Path) -> None:
    """A session dir whose meta.json fails to parse must not crash the lookup."""
    pb = tmp_path / "site.yml"
    pb.write_text("")
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    bad = sessions / "corrupt"
    bad.mkdir()
    (bad / "meta.json").write_text("{ this is not json")

    # Add one valid session so we know the lookup didn't bail early.
    _write_session(
        sessions,
        sid="good",
        playbook=str(pb),
        ansible_args=[],
        status="completed",
        start="2026-05-20T10:00:00Z",
        end="2026-05-20T10:01:00Z",
        duration=60.0,
        task_count=10,
        host_count=2,
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    prior = find_previous_run(sessions, key, host_count=2)
    assert prior is not None
    assert prior.session_id == "good"
