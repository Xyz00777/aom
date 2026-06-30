"""Phase 11: surface session-sink disable + preflight timing.

Two small always-on signals that don't need AOM_DEBUG:
- ``counters.session_recording_disabled`` + ``session_disable_reason``
  carry the on-disk failure mode (disk full, NFS hiccup, quota) into
  ``diagnostics.json``.
- ``counters.preflight_ms`` is the elapsed time of the parallel
  ``--list-tasks`` + ``--list-hosts`` preflight, in ms.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ansible_aom.core import diagnostics
from ansible_aom.session.store import SessionManager


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    yield
    diagnostics._reset_for_testing()


def test_set_session_recording_disabled_default_false() -> None:
    diagnostics.install_from_env(env={})
    assert diagnostics.session_recording_disabled() is False
    assert diagnostics.session_disable_reason() is None


def test_set_session_recording_disabled_records_reason() -> None:
    diagnostics.set_session_recording_disabled("disk full")
    assert diagnostics.session_recording_disabled() is True
    assert diagnostics.session_disable_reason() == "disk full"


def test_session_disable_clears_on_reset() -> None:
    diagnostics.set_session_recording_disabled("disk full")
    diagnostics._reset_for_testing()
    assert diagnostics.session_recording_disabled() is False
    assert diagnostics.session_disable_reason() is None


def test_diagnostics_json_propagates_session_disable(tmp_path: Path) -> None:
    diagnostics.set_session_recording_disabled("disk full")
    mgr = SessionManager(session_dir=tmp_path, playbook="x.yml")
    sid = mgr.start_session("x.yml", ansible_args=[])
    mgr.end_session(sid, "completed", preflight_task_count=1, resolved_host_count=1)

    payload = json.loads((tmp_path / sid / "diagnostics.json").read_text())
    assert payload["counters"]["session_recording_disabled"] is True
    assert payload["counters"]["session_disable_reason"] == "disk full"


def test_run_diagnostics_preflight_ms_field() -> None:
    diag = diagnostics.RunDiagnostics()
    assert diag.preflight_ms == 0
    diag.note_preflight_elapsed_ms(1234)
    assert diag.preflight_ms == 1234


def test_diagnostics_json_includes_preflight_ms(tmp_path: Path) -> None:
    diag = diagnostics.RunDiagnostics()
    diag.note_preflight_elapsed_ms(842)
    diagnostics.set_last_run_diagnostics(diag)

    mgr = SessionManager(session_dir=tmp_path, playbook="x.yml")
    sid = mgr.start_session("x.yml", ansible_args=[])
    mgr.end_session(sid, "completed", preflight_task_count=1, resolved_host_count=1)

    payload = json.loads((tmp_path / sid / "diagnostics.json").read_text())
    assert payload["counters"]["preflight_ms"] == 842
