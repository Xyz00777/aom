"""Phase 12: JsonRenderer and AOMApp publish RendererStats at completion.

Spec: docs/superpowers/specs/2026-05-21-diagnostics-layer-design.md §4.
"""

from __future__ import annotations

from io import StringIO
from typing import Any
from unittest.mock import patch

import pytest

from ansible_aom.core import diagnostics


@pytest.fixture(autouse=True)
def _reset() -> None:
    diagnostics._reset_for_testing()
    yield
    diagnostics._reset_for_testing()


# ---- JsonRenderer ---------------------------------------------------------


def _drive_json(events: list[dict[str, Any]]) -> None:
    from ansible_aom.formats.json import JsonRenderer

    r = JsonRenderer()
    r.start("site.yml", [])
    for ev in events:
        r.update_state(ev)
    with patch("sys.stdout", new=StringIO()):
        r.handle_completion(0, "completed")
    r.stop()


def test_json_renderer_publishes_stats_on_completion() -> None:
    _drive_json(
        [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-01-01T00:00:00Z"},
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-01-01T00:00:01Z"},
        ]
    )
    stats = diagnostics.get_last_renderer_stats()
    assert stats is not None
    # JSON mode doesn't render a live panel — render_calls stays 0, but
    # the snapshot itself must exist so post-mortem can tell "json mode
    # ran" from "no renderer at all".
    assert stats.log_writes == 0


# ---- AOMApp ---------------------------------------------------------------


def test_aomapp_print_log_increments_log_writes() -> None:
    from ansible_aom.tui.app import AOMApp

    app = AOMApp()
    app.start("site.yml", [])
    app.print_log("hello")
    app.print_log("world")
    assert app._log_writes == 2


def test_aomapp_update_state_increments_render_calls() -> None:
    from ansible_aom.tui.app import AOMApp

    app = AOMApp()
    app.start("site.yml", [])
    app.update_state(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-01-01T00:00:00Z",
            "play": {"id": "p1", "name": "p"},
        }
    )
    app.update_state(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-01-01T00:00:00Z",
            "task": {"id": "t1", "name": "t"},
        }
    )
    assert app._render_calls >= 2


def test_aomapp_handle_completion_publishes_stats() -> None:
    from ansible_aom.tui.app import AOMApp

    app = AOMApp()
    app.start("site.yml", [])
    app.print_log("a")
    app.update_state(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-01-01T00:00:00Z",
            "play": {"id": "p1", "name": "p"},
        }
    )
    app.handle_completion(0, "completed")

    stats = diagnostics.get_last_renderer_stats()
    assert stats is not None
    assert stats.log_writes >= 1
    assert stats.render_calls >= 1
