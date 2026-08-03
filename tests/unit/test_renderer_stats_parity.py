"""Phase 12: JsonRenderer publishes RendererStats at completion.

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
