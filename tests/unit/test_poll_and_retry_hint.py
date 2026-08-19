"""Unit tests for live polling and retry progress hint rendering."""

from __future__ import annotations

from ansible_aom.core.models import HostRunState, RunState, Status
from ansible_aom.core.parser import PtyStreamParser
from ansible_aom.core.tree_projection import TreeProjection, _host_leaf_label


def test_host_leaf_label_renders_poll_hint() -> None:
    hs = HostRunState(
        hostname="ds5",
        status=Status.RUNNING,
        poll_hint="18 retries left",
    )
    assert _host_leaf_label("ds5", hs, None) == "ds5  (18 retries left)"


def test_run_state_handles_v2_runner_retry_event() -> None:
    state = RunState("site.yml")
    state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
    state.handle_event(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-22T10:00:01Z",
            "play": {"id": "p1", "name": "Deploy"},
        }
    )
    state.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-22T10:00:02Z",
            "play": {"id": "p1"},
            "task": {"id": "t1", "name": "Wait for service to settle"},
        }
    )
    state.handle_event(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-05-22T10:00:03Z",
            "task": {"id": "t1", "name": "Wait for service to settle"},
            "host": "localhost",
        }
    )

    # Fire retry event
    state.handle_event(
        {
            "_event": "v2_runner_retry",
            "_timestamp": "2026-05-22T10:00:05Z",
            "task": {"id": "t1", "name": "Wait for service to settle"},
            "host": "localhost",
            "retries": 30,
            "attempts": 5,
            "retries_left": 25,
        }
    )

    host_state = state.plays["p1"].tasks["t1"].hosts["localhost"]
    assert host_state.poll_hint == "25 retries left"

    p = TreeProjection.from_run_state(state)
    lines = p.tree_lines(budget=20)
    host_lines = [ln for ln in lines if ln.kind == "host"]
    assert len(host_lines) == 1
    assert "localhost  (25 retries left)" in host_lines[0].label


def test_run_state_handles_v2_runner_on_async_poll_event() -> None:
    state = RunState("site.yml")
    state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-22T10:00:00Z"})
    state.handle_event(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-22T10:00:01Z",
            "play": {"id": "p1", "name": "Deploy"},
        }
    )
    state.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-22T10:00:02Z",
            "play": {"id": "p1"},
            "task": {"id": "t1", "name": "Async job"},
        }
    )
    state.handle_event(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-05-22T10:00:03Z",
            "task": {"id": "t1", "name": "Async job"},
            "host": "web1",
        }
    )

    # Fire async poll event
    state.handle_event(
        {
            "_event": "v2_runner_on_async_poll",
            "_timestamp": "2026-05-22T10:00:05Z",
            "task": {"id": "t1", "name": "Async job"},
            "host": "web1",
            "attempts": 3,
            "remaining": 45,
            "ansible_job_id": "12345.6789",
        }
    )

    host_state = state.plays["p1"].tasks["t1"].hosts["web1"]
    assert host_state.poll_hint == "45s remaining"


def test_pty_parser_parses_plaintext_retrying_line() -> None:
    parser = PtyStreamParser()
    parser.phase = parser.phase.EXECUTION

    line = "FAILED - RETRYING: [localhost]: Wait for service to settle (12 retries left)."
    events = parser.feed_line(line)

    assert len(events) == 1
    assert events[0]["_event"] == "v2_runner_retry"
    assert events[0]["host"] == "localhost"
    assert events[0]["retries_left"] == 12
    assert events[0]["task"]["name"] == "Wait for service to settle"
