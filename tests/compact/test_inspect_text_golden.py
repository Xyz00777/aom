"""Golden-frame tests for the text-mode inspect renderer."""

import json
from pathlib import Path

from ansible_aom.inspect.text import render_session


def _load(name: str) -> dict:
    src = Path(__file__).parent.parent / "fixtures" / "sessions" / name
    meta = json.loads((src / "meta.json").read_text())
    events = [
        json.loads(line)
        for line in (src / "events.jsonl").read_text().splitlines()
        if line.strip()
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


def test_render_includes_stderr_tail_on_failure():
    output = render_session(_load("failed_loop"))
    assert "stderr.log" in output
    assert "curl: (22)" in output
