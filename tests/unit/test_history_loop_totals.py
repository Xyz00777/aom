"""Mining per-host loop totals from a prior session's recorded events.

The live run never learns a loop's total item count up front. But a
matching prior session recorded its aggregate ``v2_runner_on_*`` events,
each carrying ``len(hosts[host].results)`` — the loop length. ``find_previous_run``
mines these into ``PriorRun.loop_totals`` keyed by ``task.path`` so the
TUI can show ``N/total`` live on a re-run.
"""

from __future__ import annotations

import json
from pathlib import Path

from ansible_aom.core.run_config import build_run_config_key
from ansible_aom.session.history import find_previous_run


def _write_session_with_events(
    sessions_dir: Path,
    *,
    sid: str,
    playbook: str,
    events: list[dict],
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
        "preflight_task_count": 1,
        "resolved_host_count": 1,
        "version": "1.2",
        "status": "completed",
    }
    (d / "meta.json").write_text(json.dumps(meta))
    (d / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events))


def _loop_aggregate(task_path: str, host: str, n_items: int) -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-06-01T10:00:30Z",
        "task": {"id": "t1", "name": "Echo each", "path": task_path},
        "hosts": {host: {"changed": True, "results": [{"item": i} for i in range(n_items)]}},
    }


def _prior(tmp_path: Path, playbook: Path) -> object:
    key = build_run_config_key(playbook=str(playbook), ansible_args=[])
    return find_previous_run(tmp_path / "sessions", key, host_count=1)


def test_mines_loop_total_per_task_path_and_host(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    _write_session_with_events(
        tmp_path / "sessions",
        sid="aaa",
        playbook=str(pb),
        events=[_loop_aggregate("site.yml:5", "web1", 12)],
    )
    prior = _prior(tmp_path, pb)
    assert prior is not None
    assert prior.loop_totals == {"site.yml:5": {"web1": 12}}


def test_non_loop_events_are_excluded(tmp_path: Path) -> None:
    pb = tmp_path / "site.yml"
    pb.write_text("")
    non_loop = {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-06-01T10:00:30Z",
        "task": {"id": "t2", "name": "Plain", "path": "site.yml:9"},
        "hosts": {"web1": {"changed": False}},  # no results[] → not a loop
    }
    _write_session_with_events(
        tmp_path / "sessions",
        sid="aaa",
        playbook=str(pb),
        events=[non_loop],
    )
    prior = _prior(tmp_path, pb)
    assert prior is not None
    assert prior.loop_totals == {}


def test_loop_totals_default_empty_without_events_file(tmp_path: Path) -> None:
    # A prior session that predates event recording (meta.json only) must
    # still match — loop_totals just comes back empty.
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
    assert prior.loop_totals == {}
