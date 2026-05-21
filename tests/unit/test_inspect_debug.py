"""Phase 6: ``aom inspect --debug`` prints diagnostics.json contents.

Spec: docs/superpowers/specs/2026-05-21-diagnostics-layer-design.md §5.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from ansible_aom.core import diagnostics
from ansible_aom.inspect.cli import main as inspect_main
from ansible_aom.inspect.formatters import format_diagnostics_section


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    yield
    diagnostics._reset_for_testing()


def _write_session(
    state_dir: Path,
    session_id: str,
    *,
    with_diagnostics: bool = True,
    histogram: dict[str, int] | None = None,
) -> None:
    sdir = state_dir / session_id
    sdir.mkdir(parents=True)
    (sdir / "meta.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "playbook": "site.yml",
                "status": "completed",
                "start_time": "2026-05-21T10:00:00Z",
                "end_time": "2026-05-21T10:00:42Z",
                "duration_seconds": 42.0,
            }
        )
    )
    (sdir / "events.jsonl").write_text("")
    if with_diagnostics:
        record = {
            "schema_version": 1,
            "session_id": session_id,
            "aom_version": "1.3.0",
            "lifecycle": {
                "preflight_start_ms": 0,
                "preflight_end_ms": 1200,
                "spawn_ms": 1350,
                "first_event_ms": 2100,
                "last_event_ms": 41000,
                "completion_ms": 41050,
            },
            "counters": {
                "events_received": sum((histogram or {}).values()) or 4821,
                "render_calls": 312,
                "log_writes": 14,
                "pty_bytes": 198432,
                "stall_count_max": 3,
                "pexpect_timeouts": 88,
                "session_recording_disabled": False,
                "session_disable_reason": None,
            },
            "resources": {
                "max_rss_kb": 84320,
                "state_size_bytes": None,
                "tracemalloc_peak_kb": None,
            },
            "event_histogram": histogram or {
                "v2_playbook_on_task_start": 4200,
                "v2_runner_on_ok": 400,
                "v2_runner_on_failed": 21,
                "v2_playbook_on_stats": 1,
            },
            "env_snapshot": {"TERM": "xterm-256color", "AOM_DEBUG": "1"},
            "host_count": 14,
            "playbook_task_count": 1200,
        }
        (sdir / "diagnostics.json").write_text(json.dumps(record))


# ---- pure formatter tests -------------------------------------------------


def test_format_diagnostics_section_with_full_record() -> None:
    record = {
        "schema_version": 1,
        "session_id": "abc",
        "aom_version": "1.3.0",
        "lifecycle": {
            "preflight_start_ms": 0,
            "completion_ms": 1500,
        },
        "counters": {
            "events_received": 100,
            "render_calls": 25,
            "log_writes": 5,
            "pty_bytes": 12_000,
            "stall_count_max": 1,
            "pexpect_timeouts": 4,
            "session_recording_disabled": False,
            "session_disable_reason": None,
        },
        "resources": {"max_rss_kb": 50_000, "state_size_bytes": None, "tracemalloc_peak_kb": None},
        "event_histogram": {"v2_runner_on_ok": 80, "v2_runner_on_failed": 20},
        "env_snapshot": {"TERM": "xterm"},
        "host_count": 3,
        "playbook_task_count": 50,
    }
    output = format_diagnostics_section(record)
    assert "Diagnostics (schema v1)" in output
    assert "events_received" in output
    assert "v2_runner_on_ok" in output
    assert "100" in output
    # Lifecycle delta from anchor.
    assert "1500" in output


def test_format_diagnostics_section_with_none_returns_fallback() -> None:
    output = format_diagnostics_section(None)
    assert "no diagnostics" in output.lower()


def test_format_diagnostics_recording_disabled_surfaces_reason() -> None:
    record = {
        "schema_version": 1,
        "session_id": "abc",
        "aom_version": "1.3.0",
        "lifecycle": {},
        "counters": {
            "events_received": 0,
            "render_calls": 0,
            "log_writes": 0,
            "pty_bytes": 0,
            "stall_count_max": 0,
            "pexpect_timeouts": 0,
            "session_recording_disabled": True,
            "session_disable_reason": "disk full",
        },
        "resources": {"max_rss_kb": None, "state_size_bytes": None, "tracemalloc_peak_kb": None},
        "event_histogram": {},
        "env_snapshot": {},
        "host_count": None,
        "playbook_task_count": None,
    }
    output = format_diagnostics_section(record)
    assert "disk full" in output
    assert "recording disabled" in output.lower()


# ---- CLI integration tests ------------------------------------------------


def test_inspect_debug_prints_histogram(tmp_path: Path) -> None:
    _write_session(tmp_path, "019e4ba7-ebf6-7000-9250-e869f2f45843")

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = inspect_main(["--debug", "--state-dir", str(tmp_path)])

    assert rc == 0
    out = buf.getvalue()
    assert "v2_playbook_on_task_start" in out
    assert "4200" in out


def test_inspect_debug_on_legacy_session_prints_fallback(tmp_path: Path) -> None:
    _write_session(tmp_path, "legacy-session", with_diagnostics=False)

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = inspect_main(["--debug", "--state-dir", str(tmp_path)])

    assert rc == 0
    out = buf.getvalue()
    assert "no diagnostics" in out.lower()


def test_inspect_debug_with_specific_session_id(tmp_path: Path) -> None:
    _write_session(tmp_path, "019e4ba7-aaaa-7000-9250-e869f2f45843")
    _write_session(
        tmp_path,
        "019e4ba7-bbbb-7000-9250-e869f2f45843",
        histogram={"v2_runner_on_unreachable": 7},
    )

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = inspect_main(
            [
                "--debug",
                "--session",
                "019e4ba7-bbbb-7000-9250-e869f2f45843",
                "--state-dir",
                str(tmp_path),
            ]
        )

    assert rc == 0
    assert "v2_runner_on_unreachable" in buf.getvalue()


def test_inspect_debug_no_sessions(tmp_path: Path) -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = inspect_main(["--debug", "--state-dir", str(tmp_path)])
    assert rc == 0
    assert "no session" in buf.getvalue().lower()
