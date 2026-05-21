"""Phase 10: render-storm self-diagnostic.

When the renderer redraws far more often than the runner emits events,
something is forcing redundant compute on the render hot path. The
diagnostics layer flags this so the next post-mortem reads it from
``diagnostics.json`` without anyone having to profile.
"""

from __future__ import annotations

import pytest

from ansible_aom.core import diagnostics


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    yield
    diagnostics._reset_for_testing()


def test_no_warning_for_low_event_count() -> None:
    stats = diagnostics.RendererStats(events_received=10, render_calls=500)
    assert diagnostics.render_storm_warning(stats) is None


def test_no_warning_for_reasonable_ratio() -> None:
    stats = diagnostics.RendererStats(events_received=200, render_calls=400)
    assert diagnostics.render_storm_warning(stats) is None


def test_warning_for_high_ratio() -> None:
    stats = diagnostics.RendererStats(events_received=500, render_calls=10_000)
    msg = diagnostics.render_storm_warning(stats)
    assert msg is not None
    assert "render" in msg.lower()
    assert "10000" in msg or "10,000" in msg


def test_warning_when_zero_events_but_renders() -> None:
    stats = diagnostics.RendererStats(events_received=0, render_calls=5000)
    # zero events shouldn't divide by zero — must short-circuit cleanly.
    msg = diagnostics.render_storm_warning(stats)
    # Either None (events too low for confidence) or a non-empty string.
    # We pick None to avoid spamming on cancelled/early-failure runs.
    assert msg is None


def test_build_diagnostics_record_includes_warnings_field() -> None:
    stats = diagnostics.RendererStats(events_received=500, render_calls=10_000)
    record = diagnostics.build_diagnostics_record(
        session_id="abc",
        aom_version="1.3.0",
        lifecycle_marks_ns=[],
        stats=stats,
        event_histogram={"v2_runner_on_ok": 500},
        env_snapshot={},
    )
    assert "warnings" in record
    assert isinstance(record["warnings"], list)
    assert any("render" in w.lower() for w in record["warnings"])


def test_build_diagnostics_record_warnings_empty_when_healthy() -> None:
    stats = diagnostics.RendererStats(events_received=500, render_calls=300)
    record = diagnostics.build_diagnostics_record(
        session_id="abc",
        aom_version="1.3.0",
        lifecycle_marks_ns=[],
        stats=stats,
        event_histogram={},
        env_snapshot={},
    )
    assert record["warnings"] == []
