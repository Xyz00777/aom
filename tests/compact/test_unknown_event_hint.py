"""R5: completion-time hint when JSONL emits events AOM didn't recognise.

When ansible-core or a third-party callback introduces a new ``_event``
value, RunState today drops it on the floor. That makes future-version
drift invisible — the run completes, but features are silently missing.
The hint surfaces a one-line summary at completion ("(N unknown events:
foo×3, bar×1)") so the user knows something was unhandled without
seeing per-event noise mid-run.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.run_state import RunState


def _empty_state() -> RunState:
    state = RunState(playbook="site.yml")
    state.start_time = datetime.now(timezone.utc)
    return state


def test_completion_prints_unknown_event_hint(capsys):
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    state = _empty_state()
    # Simulate three unknowns of one kind, one of another.
    for _ in range(3):
        state.handle_event({"_event": "v2_playbook_on_include"})
    state.handle_event({"_event": "v2_some_new_event"})
    renderer._state = state

    renderer.handle_completion(0, "completed")

    captured = capsys.readouterr()
    assert "unknown events" in captured.out
    assert "v2_playbook_on_include" in captured.out
    assert "v2_some_new_event" in captured.out
    # Format is "name×count" — pin the multiplication sign so a future
    # refactor doesn't accidentally use "x" or " * ".
    assert "v2_playbook_on_include×3" in captured.out
    assert "v2_some_new_event×1" in captured.out


def test_completion_no_hint_when_all_known(capsys):
    """No "unknown events" line when nothing weird happened."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    renderer._state = _empty_state()

    renderer.handle_completion(0, "completed")

    captured = capsys.readouterr()
    assert "unknown events" not in captured.out


def test_completion_no_hint_when_state_is_none(capsys):
    """stop()'d renderer with state=None must still complete cleanly."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    renderer._state = None

    renderer.handle_completion(0, "completed")

    captured = capsys.readouterr()
    assert "unknown events" not in captured.out
