"""Completion-time hint when terminal runner events couldn't be attributed.

Sibling of the R5 unknown-events hint: a ``v2_runner_on_*`` event whose
``(play_id, task_id)`` — and path/name fallback — matched nothing is
dropped, which leaves hosts stuck as RUNNING in the tree. The drop is
now counted in ``RunState.unmatched_events``; this hint makes it visible
at completion so a stale tree is diagnosable without reading logs.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.run_state import RunState


def _empty_state() -> RunState:
    state = RunState(playbook="site.yml")
    state.start_time = datetime.now(timezone.utc)
    return state


def test_completion_prints_unmatched_event_hint(capsys):
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    state = _empty_state()
    state.unmatched_events = {"v2_runner_on_ok": 8, "v2_runner_on_failed": 1}
    renderer._state = state

    renderer.handle_completion(0, "completed")

    captured = capsys.readouterr()
    assert "unmatched result events" in captured.out
    assert "v2_runner_on_ok×8" in captured.out
    assert "v2_runner_on_failed×1" in captured.out


def test_completion_no_hint_when_all_matched(capsys):
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    renderer._state = _empty_state()

    renderer.handle_completion(0, "completed")

    captured = capsys.readouterr()
    assert "unmatched result events" not in captured.out
