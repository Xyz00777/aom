"""Mining per-task wall durations from a prior session's recorded events.

The live run learns each task's wall time as it goes, but to *project* a
remaining time it needs the prior run's per-task profile.
``find_previous_run`` mines ``{task.path: per_occurrence_avg_seconds}`` and
``prior_wall_total_s`` from the matching session's ``events.jsonl`` —
per-task wall = the delta between consecutive ``v2_playbook_on_task_start``
timestamps, with the final task closed at ``v2_playbook_on_stats``.
"""

from __future__ import annotations

import json
from pathlib import Path

from ansible_aom.core.run_config import build_run_config_key
from ansible_aom.session.history import find_previous_run


def _write_session_with_events(
    sessions_dir: Path, *, sid: str, playbook: str, events: list[dict]
) -> None:
    d = sessions_dir / sid
    d.mkdir(parents=True)
    meta = {
        "session_id": sid,
        "playbook": playbook,
        "ansible_args": [],
        "start_time": "2026-06-01T10:00:00+00:00",
        "end_time": "2026-06-01T10:01:00+00:00",
        "duration_seconds": 60.0,
        "preflight_task_count": 3,
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


def _prior(tmp_path: Path, playbook: Path) -> object:
    key = build_run_config_key(playbook=str(playbook), ansible_args=[])
    return find_previous_run(tmp_path / "sessions", key, host_count=1)


def test_mines_per_task_wall_from_inter_start_deltas(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    _write_session_with_events(
        tmp_path / "sessions",
        sid="aaa",
        playbook=str(pb),
        events=[
            _task_start("site.yml:1", "2026-06-01T10:00:00Z"),
            _task_start("site.yml:2", "2026-06-01T10:00:10Z"),  # task:1 took 10s
            _task_start("site.yml:3", "2026-06-01T10:00:40Z"),  # task:2 took 30s
            _stats("2026-06-01T10:00:45Z"),  # task:3 took 5s
        ],
    )
    prior = _prior(tmp_path, pb)
    assert prior is not None
    assert prior.task_wall_s == {"site.yml:1": 10.0, "site.yml:2": 30.0, "site.yml:3": 5.0}
    assert prior.prior_wall_total_s == 45.0


def test_recurring_path_stores_per_occurrence_average(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    _write_session_with_events(
        tmp_path / "sessions",
        sid="aaa",
        playbook=str(pb),
        events=[
            _task_start("role.yml:1", "2026-06-01T10:00:00Z"),
            _task_start("role.yml:1", "2026-06-01T10:00:10Z"),  # 1st occ: 10s
            _stats("2026-06-01T10:00:40Z"),  # 2nd occ: 30s → avg 20s
        ],
    )
    prior = _prior(tmp_path, pb)
    assert prior is not None
    assert prior.task_wall_s == {"role.yml:1": 20.0}  # (10 + 30) / 2
    assert prior.prior_wall_total_s == 40.0  # full sum, not the average


def test_missing_events_file_yields_empty_profile(tmp_path: Path) -> None:
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
                "preflight_task_count": 1,
                "resolved_host_count": 1,
                "version": "1.2",
                "status": "completed",
            }
        )
    )
    prior = _prior(tmp_path, pb)
    assert prior is not None
    assert prior.task_wall_s == {}
    assert prior.prior_wall_total_s == 0.0


def test_malformed_timestamp_skips_that_delta(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    _write_session_with_events(
        tmp_path / "sessions",
        sid="aaa",
        playbook=str(pb),
        events=[
            _task_start("site.yml:1", "not-a-timestamp"),
            _task_start("site.yml:2", "2026-06-01T10:00:10Z"),
            _stats("2026-06-01T10:00:20Z"),  # task:2 took 10s
        ],
    )
    prior = _prior(tmp_path, pb)
    assert prior is not None
    # task:1 has no parseable start → its delta is dropped; task:2 survives.
    assert prior.task_wall_s == {"site.yml:2": 10.0}
    assert prior.prior_wall_total_s == 10.0
