"""Snapshot-ish tests for the prior-run line in the preflight summary."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ansible_aom.compact.format import format_preflight_summary
from ansible_aom.core.models import PlayDefinition, TaskDefinition
from ansible_aom.session.history import PriorRun


def _play(name: str, hosts: list[str], tasks: int) -> PlayDefinition:
    return PlayDefinition(
        id="1",
        name=name,
        hosts=",".join(hosts) or "all",
        resolved_hosts=hosts,
        tasks=[
            TaskDefinition(
                name=f"task-{i}",
                role=None,
                tags=[],
                play_id="1",
                play_order=1,
                task_order=i,
            )
            for i in range(tasks)
        ],
    )


def test_prior_run_line_is_omitted_when_none() -> None:
    defs = [_play("Setup", ["web1", "web2"], 3)]
    out = format_preflight_summary(defs, prior_run=None)
    assert out is not None
    assert "Last run" not in out


def test_prior_run_line_shown_when_prior_exists() -> None:
    defs = [_play("Setup", ["web1", "web2"], 3)]
    prior = PriorRun(
        session_id="abc",
        duration_seconds=83.0,
        task_count=3,
        host_count=2,
        end_time=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    out = format_preflight_summary(defs, prior_run=prior)
    assert out is not None
    assert "Last run:" in out
    # 83 seconds → "1m23s"
    assert "1m23s" in out
    # 3 tasks
    assert "3 tasks" in out
    # Relative age — "2h ago"
    assert "2h ago" in out


def test_prior_run_line_seconds_only_under_a_minute() -> None:
    defs = [_play("Setup", ["web1"], 1)]
    prior = PriorRun(
        session_id="abc",
        duration_seconds=42.0,
        task_count=1,
        host_count=1,
        end_time=datetime.now(timezone.utc) - timedelta(days=3),
    )
    out = format_preflight_summary(defs, prior_run=prior)
    assert out is not None
    assert "42s" in out
    assert "3d ago" in out
    assert "1 task" in out  # singular


def test_prior_run_line_hours_format() -> None:
    defs = [_play("Setup", ["web1"], 1)]
    prior = PriorRun(
        session_id="abc",
        duration_seconds=3725.0,  # 1h02m05s
        task_count=200,
        host_count=1,
        end_time=datetime.now(timezone.utc) - timedelta(minutes=30),
    )
    out = format_preflight_summary(defs, prior_run=prior)
    assert out is not None
    # 3725s → "1h02m"
    assert "1h02m" in out
    assert "30m ago" in out
