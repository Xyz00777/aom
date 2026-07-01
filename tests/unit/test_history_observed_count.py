"""Prior-run observed task count + match-confidence flag.

``preflight_task_count`` in ``meta.json`` only reflects what
``--list-tasks`` saw statically (e.g. 4), which badly under-counts a
playbook driven by dynamic ``include_tasks``. The *observed* task count
— how many ``v2_playbook_on_task_start`` events the prior run actually
produced — is the realistic total, mined from the events. ``exact_match``
records whether the prior was a strict RunConfigKey match (trustworthy)
or the loose playbook+host-count fallback (an estimate).
"""

from __future__ import annotations

import json
from pathlib import Path

from ansible_aom.core.run_config import build_run_config_key
from ansible_aom.session.history import find_previous_run


def _write_session(
    sessions_dir: Path,
    *,
    sid: str,
    playbook: str,
    ansible_args: list[str],
    events: list[dict],
) -> None:
    d = sessions_dir / sid
    d.mkdir(parents=True)
    meta = {
        "session_id": sid,
        "playbook": playbook,
        "ansible_args": ansible_args,
        "start_time": "2026-06-01T10:00:00+00:00",
        "end_time": "2026-06-01T10:01:00+00:00",
        "duration_seconds": 60.0,
        "preflight_task_count": 4,
        "resolved_host_count": 1,
        "version": "1.2",
        "status": "completed",
    }
    (d / "meta.json").write_text(json.dumps(meta))
    (d / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events))


def _task_start(path: str, ts: str) -> dict:
    return {"_event": "v2_playbook_on_task_start", "_timestamp": ts, "task": {"path": path}}


def _stats(ts: str) -> dict:
    return {"_event": "v2_playbook_on_stats", "_timestamp": ts}


def test_observed_task_count_counts_task_starts(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    _write_session(
        tmp_path / "sessions",
        sid="aaa",
        playbook=str(pb),
        ansible_args=[],
        events=[
            _task_start("site.yml:1", "2026-06-01T10:00:00Z"),
            _task_start("site.yml:2", "2026-06-01T10:00:10Z"),
            _task_start("site.yml:3", "2026-06-01T10:00:40Z"),
            _stats("2026-06-01T10:00:45Z"),
        ],
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    prior = find_previous_run(tmp_path / "sessions", key, host_count=1)
    assert prior is not None
    # 3 task starts observed, even though preflight_task_count is 4.
    assert prior.observed_task_count == 3


def test_observed_count_includes_starts_with_bad_timestamps(tmp_path: Path) -> None:
    """A raw count of task-start events — not gated on a parseable delta."""
    pb = tmp_path / "site.yml"
    pb.write_text("")
    _write_session(
        tmp_path / "sessions",
        sid="aaa",
        playbook=str(pb),
        ansible_args=[],
        events=[
            _task_start("site.yml:1", "not-a-timestamp"),
            _task_start("site.yml:2", "2026-06-01T10:00:10Z"),
            _stats("2026-06-01T10:00:20Z"),
        ],
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    prior = find_previous_run(tmp_path / "sessions", key, host_count=1)
    assert prior is not None
    assert prior.observed_task_count == 2


def test_missing_events_yields_zero_observed(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    d = tmp_path / "sessions" / "aaa"
    d.mkdir(parents=True)
    (d / "meta.json").write_text(
        json.dumps(
            {
                "session_id": "aaa",
                "playbook": str(pb),
                "ansible_args": [],
                "start_time": "2026-06-01T10:00:00+00:00",
                "end_time": "2026-06-01T10:01:00+00:00",
                "duration_seconds": 60.0,
                "preflight_task_count": 4,
                "resolved_host_count": 1,
                "version": "1.2",
                "status": "completed",
            }
        )
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=[])
    prior = find_previous_run(tmp_path / "sessions", key, host_count=1)
    assert prior is not None
    assert prior.observed_task_count == 0


def test_strict_match_is_flagged_exact(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    _write_session(
        tmp_path / "sessions",
        sid="aaa",
        playbook=str(pb),
        ansible_args=["-l", "caeli"],
        events=[_task_start("site.yml:1", "2026-06-01T10:00:00Z"), _stats("2026-06-01T10:00:10Z")],
    )
    key = build_run_config_key(playbook=str(pb), ansible_args=["-l", "caeli"])
    prior = find_previous_run(tmp_path / "sessions", key, host_count=1)
    assert prior is not None
    assert prior.exact_match is True


def test_loose_match_is_flagged_inexact(tmp_path: Path) -> None:
    """Same playbook + host count but different args -> loose fallback."""
    pb = tmp_path / "site.yml"
    pb.write_text("")
    _write_session(
        tmp_path / "sessions",
        sid="aaa",
        playbook=str(pb),
        ansible_args=["-l", "caeli", "--tags", "web"],
        events=[_task_start("site.yml:1", "2026-06-01T10:00:00Z"), _stats("2026-06-01T10:00:10Z")],
    )
    # Query with different args — no strict match, but playbook+host match loosely.
    key = build_run_config_key(playbook=str(pb), ansible_args=["-l", "caeli"])
    prior = find_previous_run(tmp_path / "sessions", key, host_count=1)
    assert prior is not None
    assert prior.exact_match is False
