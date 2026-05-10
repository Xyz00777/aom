"""Tests for format_preflight_summary — startup tree preview."""

from __future__ import annotations

from ansible_aom.core.models import PlayDefinition, RoleGroupDefinition, TaskDefinition


def _td(name: str, role: str | None = None) -> TaskDefinition:
    return TaskDefinition(
        name=name, role=role, tags=[], play_id="1", play_order=1, task_order=0
    )


def test_format_preflight_summary_empty_returns_none():
    from ansible_aom.compact.renderer import format_preflight_summary

    assert format_preflight_summary([]) is None


def test_format_preflight_summary_single_play():
    from ansible_aom.compact.renderer import format_preflight_summary

    defs = [
        PlayDefinition(
            id="1",
            name="Setup web servers",
            hosts="webservers",
            resolved_hosts=["web1", "web2"],
            tasks=[_td("install nginx"), _td("configure nginx"), _td("deploy site")],
        )
    ]

    summary = format_preflight_summary(defs)

    assert summary is not None
    assert "PLAY [Setup web servers]" in summary
    # 2 hosts, 3 tasks should be reflected somehow
    assert "2 host" in summary
    assert "3 task" in summary


def test_format_preflight_summary_multi_play():
    from ansible_aom.compact.renderer import format_preflight_summary

    defs = [
        PlayDefinition(
            id="1",
            name="Setup web",
            hosts="webservers",
            resolved_hosts=["w1"],
            tasks=[_td("a"), _td("b")],
        ),
        PlayDefinition(
            id="2",
            name="Setup db",
            hosts="dbservers",
            resolved_hosts=["d1", "d2"],
            tasks=[_td("c")],
        ),
    ]

    summary = format_preflight_summary(defs)

    assert summary is not None
    # Both plays appear, in order
    assert summary.index("Setup web") < summary.index("Setup db")
    assert "1 host" in summary
    assert "2 hosts" in summary


def test_format_preflight_summary_pluralization():
    """1 host vs N hosts; 1 task vs N tasks."""
    from ansible_aom.compact.renderer import format_preflight_summary

    defs = [
        PlayDefinition(
            id="1",
            name="Solo",
            hosts="x",
            resolved_hosts=["one"],
            tasks=[_td("only one")],
        )
    ]

    summary = format_preflight_summary(defs)

    assert summary is not None
    assert "1 host" in summary
    assert "1 task" in summary
    # Make sure we don't accidentally say "1 hosts" or "1 tasks"
    assert "1 hosts" not in summary
    assert "1 tasks" not in summary


def test_format_preflight_summary_counts_role_grouped_tasks():
    """RoleGroupDefinition should contribute its inner task count."""
    from ansible_aom.compact.renderer import format_preflight_summary

    inner_tasks = [_td(f"step {i}", role="bigrole") for i in range(6)]
    defs = [
        PlayDefinition(
            id="1",
            name="Bulk",
            hosts="all",
            resolved_hosts=["x"],
            tasks=[RoleGroupDefinition(role="bigrole", tasks=inner_tasks)],
        )
    ]

    summary = format_preflight_summary(defs)

    assert summary is not None
    # The role group contains 6 tasks — the summary should report 6, not 1
    assert "6 tasks" in summary


def test_format_preflight_summary_handles_no_resolved_hosts():
    """When --list-hosts failed for a play, resolved_hosts is empty."""
    from ansible_aom.compact.renderer import format_preflight_summary

    defs = [
        PlayDefinition(
            id="1",
            name="Mystery",
            hosts="unknown",
            resolved_hosts=[],
            tasks=[_td("a")],
        )
    ]

    summary = format_preflight_summary(defs)

    assert summary is not None
    # Falls back to showing the host pattern
    assert "unknown" in summary or "0 hosts" in summary
