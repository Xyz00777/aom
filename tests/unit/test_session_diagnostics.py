"""Phase 5: SessionManager writes diagnostics.json next to meta.json.

Spec: docs/superpowers/specs/2026-05-21-diagnostics-layer-design.md §5.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ansible_aom.core import diagnostics
from ansible_aom.session.store import SessionManager, load_session


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    yield
    diagnostics._reset_for_testing()


def _start_and_end(
    tmp_path: Path,
    *,
    status: str = "completed",
    preflight_task_count: int = 4,
    resolved_host_count: int = 2,
) -> str:
    mgr = SessionManager(session_dir=tmp_path, playbook="site.yml")
    sid = mgr.start_session("site.yml", ansible_args=[])
    mgr.end_session(
        sid,
        status,
        preflight_task_count=preflight_task_count,
        resolved_host_count=resolved_host_count,
    )
    return sid


def test_diagnostics_json_written_alongside_meta(tmp_path: Path) -> None:
    """end_session writes diagnostics.json containing the schema version + histogram."""
    diag = diagnostics.RunDiagnostics()
    diag.note_event("v2_playbook_on_start")
    diag.note_event("v2_runner_on_ok")
    diag.note_event("v2_runner_on_ok")
    diag.note_event("v2_playbook_on_stats")
    diagnostics.set_last_run_diagnostics(diag)
    diagnostics.set_last_renderer_stats(diagnostics.RendererStats(render_calls=4, log_writes=8))

    sid = _start_and_end(tmp_path, preflight_task_count=42, resolved_host_count=14)

    diag_file = tmp_path / sid / "diagnostics.json"
    assert diag_file.exists()
    payload = json.loads(diag_file.read_text())
    assert payload["schema_version"] == 1
    assert payload["session_id"] == sid
    assert payload["host_count"] == 14
    assert payload["playbook_task_count"] == 42
    assert payload["event_histogram"]["v2_runner_on_ok"] == 2
    assert payload["counters"]["events_received"] == 4
    assert payload["counters"]["render_calls"] == 4
    assert payload["counters"]["log_writes"] == 8


def test_diagnostics_json_handles_no_run_diagnostics(tmp_path: Path) -> None:
    """If the run path never published a RunDiagnostics, schema still writes
    with zero counters (lean tier is always-on)."""
    sid = _start_and_end(tmp_path)
    diag_file = tmp_path / sid / "diagnostics.json"
    assert diag_file.exists()
    payload = json.loads(diag_file.read_text())
    assert payload["counters"]["events_received"] == 0
    assert payload["event_histogram"] == {}


def test_load_session_returns_diagnostics_when_present(tmp_path: Path) -> None:
    diag = diagnostics.RunDiagnostics()
    diag.note_event("v2_runner_on_ok")
    diagnostics.set_last_run_diagnostics(diag)
    sid = _start_and_end(tmp_path)

    session = load_session(sid, tmp_path)
    assert session is not None
    assert session["diagnostics"] is not None
    assert session["diagnostics"]["schema_version"] == 1
    assert session["diagnostics"]["event_histogram"]["v2_runner_on_ok"] == 1


def test_load_session_returns_none_diagnostics_for_legacy_session(tmp_path: Path) -> None:
    """A session directory without diagnostics.json (older session) is still loadable;
    the diagnostics field is None rather than an exception."""
    # Build a session dir by hand without going through end_session.
    sdir = tmp_path / "legacy-session-id"
    sdir.mkdir()
    (sdir / "meta.json").write_text(
        json.dumps(
            {"session_id": "legacy-session-id", "playbook": "old.yml", "status": "completed"}
        )
    )
    (sdir / "events.jsonl").write_text("")

    session = load_session("legacy-session-id", tmp_path)
    assert session is not None
    assert session["diagnostics"] is None


def test_diagnostics_json_includes_aom_version(tmp_path: Path) -> None:
    sid = _start_and_end(tmp_path)
    payload = json.loads((tmp_path / sid / "diagnostics.json").read_text())
    assert isinstance(payload["aom_version"], str)
    assert payload["aom_version"]  # non-empty


def test_disk_failure_during_diagnostics_write_does_not_break_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """diagnostics.json write is best-effort: an OSError must not propagate
    out of end_session (which would crash the runner's success path)."""

    # First start the session normally
    mgr = SessionManager(session_dir=tmp_path, playbook="site.yml")
    sid = mgr.start_session("site.yml", ansible_args=[])

    # Patch open() so writes to diagnostics.json specifically fail.
    real_open = open

    def failing_open(path, *args, **kwargs):  # type: ignore[no-untyped-def]
        if str(path).endswith("diagnostics.json") and ("w" in (args[0] if args else "r")):
            raise OSError("disk full")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", failing_open)
    # Should not raise.
    mgr.end_session(sid, "completed", preflight_task_count=1, resolved_host_count=1)
