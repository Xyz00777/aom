"""Verify the runner persists preflight task/host counts into meta.json.

Lighter end-to-end style: drive ``_SessionSink`` directly and assert it
forwards the counts to ``SessionManager.end_session``. The runner's
``run_playbook`` orchestration is exercised by the existing integration
tests; here we cover only the new wiring on the sink.
"""

from __future__ import annotations

import json
from pathlib import Path

from ansible_aom.ansible.runner import _SessionSink


def test_sink_end_persists_counts(tmp_path: Path) -> None:
    sink = _SessionSink(
        session_dir=tmp_path / "sessions",
        playbook="play.yml",
        ansible_args=["--tags", "web"],
    )
    assert sink.session_id is not None
    sink.end("completed", preflight_task_count=42, resolved_host_count=3)

    meta_path = tmp_path / "sessions" / sink.session_id / "meta.json"
    meta = json.loads(meta_path.read_text())
    assert meta["preflight_task_count"] == 42
    assert meta["resolved_host_count"] == 3
    assert meta["status"] == "completed"


def test_sink_end_without_counts_still_works(tmp_path: Path) -> None:
    """Crash / early-failure path may not have preflight data."""
    sink = _SessionSink(
        session_dir=tmp_path / "sessions",
        playbook="play.yml",
        ansible_args=[],
    )
    assert sink.session_id is not None
    sink.end("crashed")
    meta_path = tmp_path / "sessions" / sink.session_id / "meta.json"
    meta = json.loads(meta_path.read_text())
    assert meta["status"] == "crashed"
    assert "preflight_task_count" in meta and meta["preflight_task_count"] is None
    assert "resolved_host_count" in meta and meta["resolved_host_count"] is None
