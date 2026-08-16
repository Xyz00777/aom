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


def test_aom_synthetic_stderr_events_are_not_unknown(capsys):
    """AOM's own ``aom_stderr_line`` synthetic events are known — they must
    not be flagged by the R5 future-drift hint. A run that only records
    stderr lines (e.g. ansible.posix.profile_tasks banners) should not end
    with a bogus "(N unknown events: aom_stderr_line×N)" footer."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    state = _empty_state()
    for _ in range(3):
        state.handle_event(
            {
                "_event": "aom_stderr_line",
                "_timestamp": "2026-08-05T00:00:00Z",
                "line": "Dienstag 04 August 2026  19:02:51 +0200 (0:00:00.477)"
                "       0:00:00.477 *******",
                "source": "run_level",
            }
        )
    renderer._state = state

    renderer.handle_completion(0, "completed")

    captured = capsys.readouterr()
    assert "unknown events" not in captured.out
    assert "aom_stderr_line" not in captured.out


def test_aom_connection_events_are_not_unknown(capsys):
    """The bundled aom_connection notification callback's synthetic events
    are also AOM-internal and must not trip the future-drift hint."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])
    state = _empty_state()
    state.handle_event(
        {
            "_event": "aom_connection_acquired",
            "_timestamp": "2026-08-05T00:00:00Z",
            "host": "web1",
            "connection_id": "conn-1",
        }
    )
    state.handle_event(
        {
            "_event": "aom_connection_released",
            "_timestamp": "2026-08-05T00:00:00Z",
            "host": "web1",
            "connection_id": "conn-1",
        }
    )
    renderer._state = state

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
