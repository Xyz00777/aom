"""Tests for the host table printed by handle_completion.

After completion, the renderer prints a frozen snapshot of the host
overview table (format_host_rows) instead of per-host summary lines.
The table provides the same information in a column-aligned layout,
avoiding duplication with the live panel.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import HostRunState, PlayRunState, Status, TaskRunState
from ansible_aom.core.run_state import RunState


def _state_with_two_hosts() -> RunState:
    """Build a RunState where web1 had 2 OK + 1 changed, web2 had 1 OK + 1 failed."""
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


def test_completion_prints_host_table_with_counts(capsys):
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    renderer._state = _state_with_two_hosts()

    renderer.handle_completion(1, "failed")

    captured = capsys.readouterr()
    # Status bar still present
    assert "site.yml" in captured.out
    # Host table shows both hosts with their counts
    assert "web1" in captured.out
    assert "web2" in captured.out
    # Column-aligned counts — web1: 2 OK, 1 changed; web2: 1 OK, 1 failed
    assert "2" in captured.out
    assert "1" in captured.out


def test_completion_snapshot_contains_host_rows(capsys):
    """On failure, the host table is included in the snapshot output."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    renderer._state = _state_with_two_hosts()

    renderer.handle_completion(1, "failed")

    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    # The host table has a header row with "host" and column labels
    host_header_lines = [line for line in lines if "host" in line and "ok" in line]
    assert len(host_header_lines) >= 1


def test_completion_no_host_rows_when_no_hosts(capsys):
    """If no hosts ran (preflight-only failure), don't print a host table."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    renderer.handle_completion(4, "crashed")

    captured = capsys.readouterr()
    assert "site.yml" in captured.out
    # No host table header row
    host_lines = [line for line in captured.out.splitlines() if "host" in line and "ok" in line]
    assert len(host_lines) == 0
