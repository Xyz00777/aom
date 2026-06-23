"""Tests for the failure recap printed when a run ends in failure.

The per-host summary tells you "web2: 1 ok + 1 failed" but not WHICH
task failed. On a non-zero exit the renderer should additionally print
a recap section that names each failed/unreachable host along with the
task name(s) that caused it. This is the on-failure equivalent of
ansible-playbook's own PLAY RECAP — but pre-trimmed to the actionable
items.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.compact.renderer import CompactRenderer, format_failure_recap
from ansible_aom.core.models import HostRunState, PlayRunState, RunState, Status, TaskRunState


def _state_with_failure() -> RunState:
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="web", status=Status.RUNNING)

    t1 = TaskRunState(task_id="t1", name="gather facts")
    t1.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    t1.hosts["web2"] = HostRunState(hostname="web2", status=Status.OK)
    play.tasks["t1"] = t1

    t2 = TaskRunState(task_id="t2", name="install nginx")
    t2.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    t2.hosts["web2"] = HostRunState(hostname="web2", status=Status.FAILED)
    play.tasks["t2"] = t2

    state.plays["1"] = play
    state.start_time = datetime.now(timezone.utc)
    return state


def _state_with_unreachable() -> RunState:
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="web", status=Status.RUNNING)
    t1 = TaskRunState(task_id="t1", name="ping")
    t1.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    t1.hosts["web2"] = HostRunState(hostname="web2", status=Status.UNREACHABLE)
    play.tasks["t1"] = t1
    state.plays["1"] = play
    state.start_time = datetime.now(timezone.utc)
    return state


def _state_all_ok() -> RunState:
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="web", status=Status.RUNNING)
    t1 = TaskRunState(task_id="t1", name="ping")
    t1.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    play.tasks["t1"] = t1
    state.plays["1"] = play
    state.start_time = datetime.now(timezone.utc)
    return state


class TestFormatFailureRecap:
    def test_empty_state_returns_no_lines(self):
        state = RunState(playbook="site.yml")
        assert format_failure_recap(state) == []

    def test_no_failures_returns_no_lines(self):
        assert format_failure_recap(_state_all_ok()) == []

    def test_failure_recap_names_host_and_task(self):
        lines = format_failure_recap(_state_with_failure())
        assert len(lines) == 1
        line = lines[0]
        assert "web2" in line
        assert "install nginx" in line

    def test_unreachable_is_recapped_separately_from_failed(self):
        lines = format_failure_recap(_state_with_unreachable())
        assert any("web2" in line and "ping" in line for line in lines)
        assert any("unreachable" in line.lower() for line in lines)

    def test_failed_label_is_visible(self):
        lines = format_failure_recap(_state_with_failure())
        assert any("failed" in line.lower() for line in lines)

    def test_multiple_failed_tasks_on_one_host(self):
        state = RunState(playbook="site.yml")
        play = PlayRunState(play_id="1", name="p", status=Status.RUNNING)
        t1 = TaskRunState(task_id="t1", name="task A")
        t1.hosts["web1"] = HostRunState(hostname="web1", status=Status.FAILED)
        play.tasks["t1"] = t1
        t2 = TaskRunState(task_id="t2", name="task B")
        t2.hosts["web1"] = HostRunState(hostname="web1", status=Status.FAILED)
        play.tasks["t2"] = t2
        state.plays["1"] = play

        lines = format_failure_recap(state)
        joined = "\n".join(lines)
        assert "task A" in joined
        assert "task B" in joined


class TestHandleCompletionRecap:
    def test_failure_completion_prints_recap(self, capsys):
        renderer = CompactRenderer(is_tty=False)
        renderer.start("site.yml", [])
        renderer._state = _state_with_failure()

        renderer.handle_completion(2, "failed")

        out = capsys.readouterr().out
        assert "install nginx" in out
        assert "web2" in out

    def test_successful_completion_does_not_print_recap(self, capsys):
        renderer = CompactRenderer(is_tty=False)
        renderer.start("site.yml", [])
        renderer._state = _state_all_ok()

        renderer.handle_completion(0, "completed")

        out = capsys.readouterr().out
        # No "FAILED" recap header should appear on a clean run.
        assert "FAILED:" not in out

    def test_failure_recap_lines_indented(self, capsys):
        """Recap lines should align visually with the per-host summary block."""
        renderer = CompactRenderer(is_tty=False)
        renderer.start("site.yml", [])
        renderer._state = _state_with_failure()

        renderer.handle_completion(2, "failed")

        out = capsys.readouterr().out
        recap_lines = [
            line for line in out.splitlines() if "FAILED:" in line and "install nginx" in line
        ]
        assert len(recap_lines) == 1
        assert recap_lines[0].startswith("  "), f"expected leading indent, got {recap_lines[0]!r}"
