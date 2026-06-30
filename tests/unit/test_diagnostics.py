"""Unit tests for core.diagnostics — opt-in observability layer.

Spec: docs/superpowers/specs/2026-05-21-diagnostics-layer-design.md (Phase 1).
"""

from __future__ import annotations

import faulthandler
import json
import logging
from unittest.mock import patch

import pytest

from ansible_aom.core import diagnostics


@pytest.fixture(autouse=True)
def _reset_diagnostics() -> None:
    diagnostics._reset_for_testing()
    yield
    diagnostics._reset_for_testing()


# TC-D01 — empty env is a true no-op (besides unconditional faulthandler).
def test_install_from_env_with_empty_env_is_noop() -> None:
    aom_logger = logging.getLogger("ansible_aom")
    initial_level = aom_logger.level

    diagnostics.install_from_env(env={})

    assert diagnostics.is_debug() is False
    assert diagnostics.watchdog_seconds() is None
    assert aom_logger.level == initial_level


# TC-D02 — AOM_WATCHDOG=N arms faulthandler.dump_traceback_later(N, repeat=True).
def test_watchdog_calls_dump_traceback_later() -> None:
    with patch("faulthandler.dump_traceback_later") as mock_dump:
        diagnostics.install_from_env(env={"AOM_WATCHDOG": "5"})
        mock_dump.assert_called_once()
        args, kwargs = mock_dump.call_args
        timeout = args[0] if args else kwargs.get("timeout")
        assert timeout == 5
        assert kwargs.get("repeat") is True
    assert diagnostics.watchdog_seconds() == 5


# TC-D03 — AOM_DEBUG=1 sets the ansible_aom logger to DEBUG.
def test_debug_sets_logger_level() -> None:
    aom_logger = logging.getLogger("ansible_aom")
    original = aom_logger.level
    try:
        diagnostics.install_from_env(env={"AOM_DEBUG": "1"})
        assert aom_logger.level == logging.DEBUG
        assert diagnostics.is_debug() is True
    finally:
        aom_logger.setLevel(original)


# TC-D04 / TC-D05 — lifecycle_mark is always-on; AOM_DEBUG only controls
# whether the post-run summary is *printed*, not whether marks are
# *recorded*. Marks always flow into diagnostics.json so post-mortem
# has the timeline regardless of how the run was invoked.
def test_lifecycle_mark_always_records() -> None:
    diagnostics.install_from_env(env={})
    diagnostics.lifecycle_mark("first")
    diagnostics.lifecycle_mark("second")
    marks = diagnostics.get_lifecycle_marks()
    assert [m[0] for m in marks] == ["first", "second"]
    assert marks[1][1] >= marks[0][1]


# TC-D06 — build_diagnostics_record JSON-round-trips and has the required keys.
def test_build_diagnostics_record_json_roundtrip() -> None:
    record = diagnostics.build_diagnostics_record(
        session_id="abc-123",
        aom_version="1.3.0",
        lifecycle_marks_ns=[("preflight_start", 1_000_000), ("completion", 2_500_000)],
        stats=diagnostics.RendererStats(events_received=10, render_calls=4, log_writes=2),
        event_histogram={"v2_runner_on_ok": 7, "v2_playbook_on_stats": 1},
        env_snapshot={"TERM": "xterm-256color"},
        host_count=14,
        playbook_task_count=1200,
        session_recording_disabled=False,
        session_disable_reason=None,
    )
    payload = json.dumps(record)
    parsed = json.loads(payload)
    assert parsed["schema_version"] == 1
    assert parsed["session_id"] == "abc-123"
    assert parsed["aom_version"] == "1.3.0"
    assert parsed["host_count"] == 14
    assert parsed["playbook_task_count"] == 1200
    for key in ("lifecycle", "counters", "resources", "event_histogram", "env_snapshot"):
        assert key in parsed
    assert parsed["counters"]["events_received"] == 10
    assert parsed["event_histogram"]["v2_runner_on_ok"] == 7


# TC-D07 — phase 15 collapsed AOM_TRACE_PEXPECT / AOM_TRACE / AOM_TRACE_EVENTS
# into a single AOM_DEBUG knob. Those names are gone; AOM_DEBUG=1 enables
# the entire verbose surface.
def test_aom_debug_is_the_only_trace_knob() -> None:
    diagnostics.install_from_env(env={"AOM_DEBUG": "1"})
    assert diagnostics.is_debug() is True
    assert not hasattr(diagnostics, "is_trace_pexpect")
    assert not hasattr(diagnostics, "is_trace_events")


# TC-D08 — faulthandler is enabled after install_from_env regardless of env.
def test_install_enables_faulthandler() -> None:
    diagnostics.install_from_env(env={})
    assert faulthandler.is_enabled()


# Extras: idempotence + remaining env vars.
def test_install_is_idempotent() -> None:
    diagnostics.install_from_env(env={"AOM_DEBUG": "1"})
    diagnostics.install_from_env(env={"AOM_DEBUG": "0"})
    assert diagnostics.is_debug() is True


def test_watchdog_with_invalid_value_is_none() -> None:
    with patch("faulthandler.dump_traceback_later") as mock_dump:
        diagnostics.install_from_env(env={"AOM_WATCHDOG": "not-a-number"})
        mock_dump.assert_not_called()
    assert diagnostics.watchdog_seconds() is None


def test_watchdog_zero_is_treated_as_disabled() -> None:
    with patch("faulthandler.dump_traceback_later") as mock_dump:
        diagnostics.install_from_env(env={"AOM_WATCHDOG": "0"})
        mock_dump.assert_not_called()
    assert diagnostics.watchdog_seconds() is None


def test_debug_falsy_values_disable() -> None:
    diagnostics.install_from_env(env={"AOM_DEBUG": "0"})
    assert diagnostics.is_debug() is False
    diagnostics._reset_for_testing()
    diagnostics.install_from_env(env={"AOM_DEBUG": ""})
    assert diagnostics.is_debug() is False
