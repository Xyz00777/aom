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


def test_fallback_loose_match_when_config_differs(tmp_path: Path) -> None:
    """Different tags still match via the loose fallback (same playbook + host count)."""
    pb = tmp_path / "site.yml"
    pb.write_text("")
    sessions = tmp_path / "sessions"
    _write_session(
        sessions,
        sid="aaa",
        playbook=str(pb),
        ansible_args=["--tags", "web", "-i", "inv.ini"],
        status="completed",
        start="2026-05-18T10:00:00Z",
        end="2026-05-18T10:01:23Z",
        duration=83.0,
        task_count=47,
        host_count=2,
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=["--tags", "db"])
    prior = find_previous_run(sessions, key, host_count=2)
    assert prior is not None
    assert prior.session_id == "aaa"
    assert prior.task_count == 47


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


def test_strict_match_takes_precedence_over_loose(tmp_path: Path) -> None:
    """When both an exact and a loose match exist, the exact (most recent) is chosen."""
    pb = tmp_path / "site.yml"
    pb.write_text("")
    sessions = tmp_path / "sessions"
    # Older session with exact match (same tags)
    _write_session(
        sessions,
        sid="exact_older",
        playbook=str(pb),
        ansible_args=["--tags", "deploy"],
        status="completed",
        start="2026-05-17T10:00:00Z",
        end="2026-05-17T10:05:00Z",
        duration=300.0,
        task_count=40,
        host_count=2,
    )
    # Newer session with loose match only (different tags)
    _write_session(
        sessions,
        sid="loose_newer",
        playbook=str(pb),
        ansible_args=["--tags", "web"],
        status="completed",
        start="2026-05-19T10:00:00Z",
        end="2026-05-19T10:02:00Z",
        duration=120.0,
        task_count=20,
        host_count=2,
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=["--tags", "deploy"])
    prior = find_previous_run(sessions, key, host_count=2)
    assert prior is not None
    # Should return the exact (older) match, not the loose (newer) one
    assert prior.session_id == "exact_older"
    assert prior.duration_seconds == 300.0
    assert prior.task_count == 40


def test_loose_match_filters_mismatched_host_count(tmp_path: Path) -> None:
    """Loose fallback still requires host count to match."""
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
        host_count=5,
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=["--tags", "db"])
    assert find_previous_run(sessions, key, host_count=2) is None


def test_loose_match_works_with_any_flag_variation(tmp_path: Path) -> None:
    """Loose fallback ignores tags, limit, extra_vars, diff, check, step."""
    pb = tmp_path / "site.yml"
    pb.write_text("")
    sessions = tmp_path / "sessions"
    _write_session(
        sessions,
        sid="prev",
        playbook=str(pb),
        ansible_args=[
            "--tags",
            "web",
            "--limit",
            "web1",
            "-e",
            "env=prod",
            "--diff",
            "--check",
            "--step",
        ],
        status="completed",
        start="2026-05-18T10:00:00Z",
        end="2026-05-18T10:01:23Z",
        duration=83.0,
        task_count=47,
        host_count=2,
    )
    # Current run: completely different flags, same playbook + host count
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    prior = find_previous_run(sessions, key, host_count=2)
    assert prior is not None
    assert prior.session_id == "prev"


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


def test_relative_playbook_resolves_against_recorded_cwd_not_current_cwd(
    tmp_path: Path, monkeypatch
) -> None:
    """A relative playbook in meta.json resolves against its recorded cwd, not the caller's cwd."""
    from ansible_aom.session.store import SessionManager

    project_a = tmp_path / "project-a"
    project_b = tmp_path / "project-b"
    project_a.mkdir()
    project_b.mkdir()
    (project_a / "site.yml").write_text("")
    (project_b / "site.yml").write_text("")
    sessions = tmp_path / "sessions"

    monkeypatch.chdir(project_a)
    mgr = SessionManager(session_dir=sessions)
    sid_a = mgr.start_session("site.yml", ansible_args=["-i", "inv.ini"])
    mgr.end_session(sid_a, "completed", preflight_task_count=15, resolved_host_count=2)

    # Running in project_b with identically named site.yml + inv.ini must NOT
    # match project_a's prior run (neither strict nor loose).
    monkeypatch.chdir(project_b)
    key_b_strict = build_run_config_key(playbook="site.yml", ansible_args=["-i", "inv.ini"])
    assert find_previous_run(sessions, key_b_strict, host_count=2) is None

    key_b_loose = build_run_config_key(playbook="site.yml", ansible_args=["--tags", "db"])
    assert find_previous_run(sessions, key_b_loose, host_count=2) is None

    # Running project_a's playbook (while process cwd is project_b) DOES match
    # project_a's session.
    key_a_strict = build_run_config_key(
        playbook=str(project_a / "site.yml"), ansible_args=["-i", "inv.ini"]
    )
    prior_strict = find_previous_run(sessions, key_a_strict, host_count=2)
    assert prior_strict is not None
    assert prior_strict.session_id == sid_a
    assert prior_strict.exact_match is True

    key_a_loose = build_run_config_key(
        playbook=str(project_a / "site.yml"), ansible_args=["--tags", "db"]
    )
    prior_loose = find_previous_run(sessions, key_a_loose, host_count=2)
    assert prior_loose is not None
    assert prior_loose.session_id == sid_a
    assert prior_loose.exact_match is False


def test_legacy_relative_playbook_without_cwd_does_not_match_current_cwd(
    tmp_path: Path, monkeypatch
) -> None:
    """A legacy session with a relative playbook and no cwd must not guess the current cwd."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "site.yml").write_text("")
    sessions = tmp_path / "sessions"

    _write_session(
        sessions,
        sid="legacy_rel",
        playbook="site.yml",
        ansible_args=[],
        status="completed",
        start="2026-05-20T10:00:00Z",
        end="2026-05-20T10:01:00Z",
        duration=60.0,
        task_count=10,
        host_count=2,
    )

    monkeypatch.chdir(project)
    key = build_run_config_key(playbook="site.yml", ansible_args=[])
    assert find_previous_run(sessions, key, host_count=2) is None
