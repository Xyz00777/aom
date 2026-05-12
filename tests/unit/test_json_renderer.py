"""Unit tests for the JSON output renderer (F6)."""

from __future__ import annotations


def test_run_summary_model_has_pinned_schema():
    """RunSummary captures every field the schema spec requires."""
    from ansible_aom.json_renderer import HostCounts, RunSummary, TaskFailure

    summary = RunSummary(
        schema_version=1,
        playbook="site.yml",
        exit_code=0,
        started_at="2026-05-12T10:30:00+00:00",
        ended_at="2026-05-12T10:30:42+00:00",
        duration_s=42.3,
        hosts={"web1": HostCounts(ok=1, changed=0, failed=0, unreachable=0)},
        tasks_failed=[TaskFailure(host="web2", task="install nginx", msg="boom")],
    )

    dumped = summary.model_dump()
    assert dumped["schema_version"] == 1
    assert dumped["playbook"] == "site.yml"
    assert dumped["exit_code"] == 0
    assert dumped["duration_s"] == 42.3
    assert dumped["hosts"] == {"web1": {"ok": 1, "changed": 0, "failed": 0, "unreachable": 0}}
    assert dumped["tasks_failed"] == [{"host": "web2", "task": "install nginx", "msg": "boom"}]


def test_run_summary_schema_version_is_literal_one():
    """schema_version refuses any value other than 1 — guards against accidental drift."""
    from pydantic import ValidationError

    from ansible_aom.json_renderer import RunSummary

    try:
        RunSummary.model_validate(
            {
                "schema_version": 2,
                "playbook": "site.yml",
                "exit_code": 0,
                "started_at": "2026-05-12T10:30:00+00:00",
                "ended_at": "2026-05-12T10:30:00+00:00",
                "duration_s": 0.0,
                "hosts": {},
                "tasks_failed": [],
            }
        )
    except ValidationError:
        return
    raise AssertionError("schema_version should be a Literal[1]")
