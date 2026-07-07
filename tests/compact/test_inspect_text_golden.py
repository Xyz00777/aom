"""Golden-frame tests for the text-mode inspect renderer."""

import json
from pathlib import Path

from ansible_aom.inspect.text import render_session

_ALIASES = {
    "clean_run": "019e4000-0000-7000-8000-000000000001",
    "failed_loop": "019e4520-fa64-7000-a627-000000000002",
    "multi_host": "019e4100-0000-7000-8000-000000000003",
    "unreachable": "019e4200-0000-7000-8000-000000000004",
    "running": "019e4300-0000-7000-8000-000000000005",
}


def _load(name: str) -> dict:
    sid = _ALIASES.get(name, name)
    src = Path(__file__).parent.parent / "fixtures" / "sessions" / sid
    meta = json.loads((src / "meta.json").read_text())
    events = [
        json.loads(line) for line in (src / "events.jsonl").read_text().splitlines() if line.strip()
    ]
    stderr_file = src / "stderr.log"
    stderr = stderr_file.read_text().splitlines() if stderr_file.exists() else []
    return {
        **meta,
        "events": events,
        "stderr": stderr,
        "session_id": meta["session_id"],
        "malformed_lines": 0,
    }


def test_render_clean_run_has_header_and_no_failure_block():
    output = render_session(_load("clean_run"))
    assert "Session  019e4000-0000-7000-8000-000000000001" in output
    assert "Playbook ansible/site.yml" in output
    assert "Status   completed" in output
    assert "Failures" not in output


def test_render_failed_loop_shows_msg_and_failed_items():
    output = render_session(_load("failed_loop"))
    assert "Status   failed" in output
    assert "os_macos : Install brew casks" in output
    assert "One or more items failed" in output
    assert "karabiner-elements" in output
    assert "rectangle" in output
    assert "404" in output
    # OK items are summarised as a count, not enumerated.
    assert "(1 ok item)" in output


def test_render_unreachable_shows_connection_msg():
    output = render_session(_load("unreachable"))
    assert "Connection refused" in output


def test_render_running_shows_running_status():
    output = render_session(_load("running"))
    assert "Status   running" in output


def test_render_includes_verbose_section_when_stderr_lines_exist():
    # Build a session with aom_stderr_line events to verify the verbose
    # section renders. The old test checked for "stderr.log" (the
    # file-based tail); the new code reads aom_stderr_line events
    # instead, so we inject synthetic ones here.
    session = _load("failed_loop")
    events = list(session.get("events", []))
    events.append(
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-05-20T11:25:00.000000Z",
            "line": "curl: (22) The requested URL returned error: 404",
            "source": "run_level",
            "level": 0,
            "host": None,
            "connection_id": None,
            "attribution_confidence": "unique",
        }
    )
    session["events"] = events
    output = render_session(session)
    assert "Verbose" in output
    assert "curl: (22)" in output


def test_render_verbose_play_scoping():
    # Session with two plays and task-level stderr lines with connection_id.
    # Scoping by play_name should include only lines for that play's tasks.
    base = _load("multi_host")
    events = list(base.get("events", []))
    # Add connection_acquired + stderr_line for task t1
    events.append(
        {
            "_event": "aom_connection_acquired",
            "_timestamp": "2026-05-19T15:00:01.500000Z",
            "connection_id": "conn1",
            "task_id": "t1",
            "host": "web1",
        }
    )
    events.append(
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-05-19T15:00:02.000000Z",
            "line": "task-level stderr for t1",
            "source": "task_level",
            "level": 1,
            "host": "web1",
            "connection_id": "conn1",
            "attribution_confidence": "unique",
        }
    )
    events.append(
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-05-19T15:00:02.100000Z",
            "line": "run-level warning",
            "source": "run_level",
            "level": 0,
            "host": None,
            "connection_id": None,
            "attribution_confidence": "unique",
        }
    )
    base["events"] = events
    output = render_session(base, play_name="web")
    assert "Verbose (play: web)" in output
    assert "task-level stderr for t1" in output
    assert "run-level warning" in output


def test_render_verbose_task_scoping():
    # Task scoping narrows to the connection for that specific task+host.
    base = _load("multi_host")
    events = list(base.get("events", []))
    events.append(
        {
            "_event": "aom_connection_acquired",
            "_timestamp": "2026-05-19T15:00:01.500000Z",
            "connection_id": "conn1",
            "task_id": "t1",
            "host": "web1",
        }
    )
    events.append(
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-05-19T15:00:02.000000Z",
            "line": "task-level stderr for t1",
            "source": "task_level",
            "level": 1,
            "host": "web1",
            "connection_id": "conn1",
            "attribution_confidence": "unique",
        }
    )
    events.append(
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-05-19T15:00:02.100000Z",
            "line": "unrelated run-level warning",
            "source": "run_level",
            "level": 0,
            "host": None,
            "connection_id": None,
            "attribution_confidence": "unique",
        }
    )
    base["events"] = events
    output = render_session(base, task_name="deploy : restart service")
    assert "Verbose (task: deploy : restart service)" in output
    # Task-level scoping includes run-level lines
    assert "unrelated run-level warning" in output


def test_render_no_verbose_section_when_no_stderr_events():
    # Clean run has no aom_stderr_line events; Verbose section should
    # not appear (no lines to show).
    output = render_session(_load("clean_run"))
    assert "Verbose" not in output


def test_render_verbose_not_gated_on_failed_status():
    # Completed sessions should still show verbose lines if they exist.
    session = _load("clean_run")
    events = list(session.get("events", []))
    events.append(
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-05-19T18:02:20.000000Z",
            "line": "a deprecation warning",
            "source": "run_level",
            "level": 0,
            "host": None,
            "connection_id": None,
            "attribution_confidence": "unique",
        }
    )
    session["events"] = events
    output = render_session(session)
    assert "Status   completed" in output
    assert "Verbose" in output
    assert "a deprecation warning" in output
