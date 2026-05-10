"""Tests for the per-host summary printed by handle_completion.

Bug context: format_host_summary() exists in compact/renderer.py with
its own unit tests, but no caller. The final completion path prints
only the aggregate `1/1 hosts │ 0:00:00 ●`. With multiple hosts that
hides who succeeded vs who failed. This adds the per-host breakdown
underneath the status line.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import HostRunState, PlayRunState, RunState, Status, TaskRunState


def _state_with_two_hosts() -> RunState:
    """Build a RunState where web1 had 2 OK + 1 changed, web2 had 1 ok + 1 failed."""
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="p1", status=Status.RUNNING)

    t1 = TaskRunState(task_id="t1", name="t1")
    t1.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    t1.hosts["web2"] = HostRunState(hostname="web2", status=Status.OK)
    play.tasks["t1"] = t1

    t2 = TaskRunState(task_id="t2", name="t2")
    t2.hosts["web1"] = HostRunState(hostname="web1", status=Status.CHANGED, changed=True)
    t2.hosts["web2"] = HostRunState(hostname="web2", status=Status.FAILED)
    play.tasks["t2"] = t2

    t3 = TaskRunState(task_id="t3", name="t3")
    t3.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    play.tasks["t3"] = t3

    state.plays["1"] = play
    state.start_time = datetime.now(timezone.utc)
    return state


def test_completion_prints_per_host_breakdown(capsys):
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    renderer._state = _state_with_two_hosts()

    renderer.handle_completion(1, "failed")

    captured = capsys.readouterr()
    # Existing aggregate line is still there
    assert "site.yml" in captured.out
    # New per-host lines
    assert "web1:" in captured.out
    assert "web2:" in captured.out
    # web1: 2 ok + 1 changed
    assert "2 ok" in captured.out
    assert "1 changed" in captured.out
    # web2: 1 ok + 1 failed
    assert "1 failed" in captured.out


def test_completion_per_host_lines_indented(capsys):
    """Per-host lines should be visually subordinate to the status line."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    renderer._state = _state_with_two_hosts()

    renderer.handle_completion(1, "failed")

    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    host_lines = [line for line in lines if "web1:" in line or "web2:" in line]
    assert len(host_lines) == 2
    for line in host_lines:
        assert line.startswith("  "), f"expected leading indent, got {line!r}"


def test_completion_no_per_host_lines_when_no_hosts(capsys):
    """If no hosts ran (preflight-only failure), don't print an empty hosts block."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    # _state stays as fresh empty RunState

    renderer.handle_completion(4, "crashed")

    captured = capsys.readouterr()
    assert "site.yml" in captured.out
    # No host lines
    for line in captured.out.splitlines():
        assert not line.startswith("  ")
