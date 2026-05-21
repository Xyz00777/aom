"""Phase 4: CompactRenderer publishes its own activity counters.

Spec: docs/superpowers/specs/2026-05-21-diagnostics-layer-design.md §4.

Counters live on the renderer (render_calls, log_writes) because
they describe rendering activity, not domain state — the runner's
``RunDiagnostics`` carries the orthogonal event-side counters.
"""

from __future__ import annotations

import pytest

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core import diagnostics


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    yield
    diagnostics._reset_for_testing()


def _ok_event(host: str, task_id: str = "t1") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-01-01T00:00:00Z",
        "task": {"id": task_id, "name": "install"},
        "hosts": {host: {"ok": True}},
    }


def test_update_state_increments_render_calls() -> None:
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    renderer.update_state(_ok_event("web1"))
    renderer.update_state(_ok_event("web1"))
    renderer.update_state(_ok_event("web2"))

    # update_state triggers _emit_event_log (writes log lines) AND
    # _render_status_panel — the latter is what render_calls counts.
    assert renderer._render_calls >= 3


def test_print_log_increments_log_writes() -> None:
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    renderer.print_log("hello")
    renderer.print_log("world")
    renderer.print_log("!")

    assert renderer._log_writes >= 3


def test_collect_stats_returns_snapshot() -> None:
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    renderer.update_state(_ok_event("web1"))
    renderer.print_log("a")

    stats = renderer.collect_stats()

    # Snapshot is the immutable RendererStats — mutating later doesn't
    # affect the previously-returned value.
    assert stats.render_calls >= 1
    assert stats.log_writes >= 1


def test_stop_publishes_last_renderer_stats() -> None:
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    renderer.update_state(_ok_event("web1"))
    renderer.print_log("a")
    renderer.stop()

    published = diagnostics.get_last_renderer_stats()
    assert published is not None
    assert published.render_calls >= 1
    assert published.log_writes >= 1


def test_last_renderer_stats_initially_none() -> None:
    assert diagnostics.get_last_renderer_stats() is None


def test_reset_clears_last_renderer_stats() -> None:
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    renderer.stop()
    assert diagnostics.get_last_renderer_stats() is not None

    diagnostics._reset_for_testing()
    assert diagnostics.get_last_renderer_stats() is None
